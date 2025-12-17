import json
import logging

from cezzis_kafka import IAsyncKafkaMessageProcessor, KafkaConsumerSettings
from confluent_kafka import Message
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from langchain_qdrant import QdrantVectorStore
from opentelemetry import trace
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from data_ingestion_agentic_workflow.agents.base_agent_evt_receiver import BaseAgentEventReceiver
from data_ingestion_agentic_workflow.agents.embedding_agent.emb_agent_options import get_emb_agent_options
from data_ingestion_agentic_workflow.config.hugging_face_options import get_huggingface_options
from data_ingestion_agentic_workflow.config.qdrant_options import get_qdrant_options
from data_ingestion_agentic_workflow.models.cocktail_chunking_model import (
    CocktailChunkingModel,
    CocktailDescriptionChunk,
)
from data_ingestion_agentic_workflow.models.cocktail_models import CocktailModel


class EmbeddingAgentEventReceiver(BaseAgentEventReceiver):
    """Concrete implementation of IAsyncKafkaMessageProcessor for processing cocktail embedding messages from Kafka.

    Attributes:
        _logger (logging.Logger): Logger instance for logging messages.
        _kafka_settings (KafkaConsumerSettings): Kafka consumer settings.
        _tracer (trace.Tracer): OpenTelemetry tracer for creating spans.

    Methods:
        message_received(msg: Message) -> None:
            Process a received Kafka message.
    """

    def __init__(self, kafka_consumer_settings: KafkaConsumerSettings) -> None:
        """Initialize the CocktailsEmbeddingProcessor
        Args:
            kafka_consumer_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            None
        """
        super().__init__(kafka_consumer_settings=kafka_consumer_settings)

        self._logger: logging.Logger = logging.getLogger("embedding_agent")
        self._tracer = trace.get_tracer("embedding_agent")
        self._options = get_emb_agent_options()
        self._huggingface_options = get_huggingface_options()
        self._qdrant_options = get_qdrant_options()
        self._collection_exists: bool = False
        self.qdrant_client = QdrantClient(
            url=self._qdrant_options.host,  # http://localhost:6333 | https://aca-vec-eus-glo-qdrant-001.proudfield-08e1f932.eastus.azurecontainerapps.io
            api_key=self._qdrant_options.api_key if self._qdrant_options.api_key else None,
            port=self._qdrant_options.port,
            https=self._qdrant_options.use_https,
            prefer_grpc=False,
            timeout=60,
        )

    @staticmethod
    def CreateNew(kafka_settings: KafkaConsumerSettings) -> IAsyncKafkaMessageProcessor:
        """Factory method to create a new instance of EmbeddingAgentEventReceiver.

        Args:
            kafka_settings (KafkaConsumerSettings): The Kafka consumer settings.

        Returns:
            IAsyncKafkaMessageProcessor: A new instance of EmbeddingAgentEventReceiver.
        """
        return EmbeddingAgentEventReceiver(kafka_consumer_settings=kafka_settings)

    async def message_received(self, msg: Message) -> None:
        with super().create_kafka_consumer_read_span(self._tracer, "cocktail-embedding-message-processing", msg):
            try:
                value = msg.value()
                if value is not None:
                    self._logger.info(
                        msg="Received cocktail embedding message",
                        extra={**super().get_kafka_attributes(msg)},
                    )

                    data = json.loads(value.decode("utf-8"))
                    chunking_model = CocktailChunkingModel(
                        cocktail_model=CocktailModel.model_validate(data["cocktail_model"]),
                        chunks=[CocktailDescriptionChunk.from_dict(chunk) for chunk in data["chunks"]],
                    )

                    if not chunking_model.chunks or not chunking_model.cocktail_model:
                        self._logger.warning(
                            msg="Received empty cocktail chunking model",
                            extra={**super().get_kafka_attributes(msg)},
                        )
                        return

                    # ----------------------------------------
                    # Process the individual cocktail message
                    # ----------------------------------------
                    self._process_message(chunking_model=chunking_model)
                else:
                    self._logger.warning(
                        msg="Received cocktail embedding message with no value",
                        extra={**super().get_kafka_attributes(msg)},
                    )
            except Exception as e:
                self._logger.error(
                    msg="Error processing cocktail embedding message",
                    exc_info=True,
                    extra={
                        **super().get_kafka_attributes(msg),
                        "error": str(e),
                    },
                )

    def _process_message(self, chunking_model: CocktailChunkingModel) -> None:
        with super().create_processing_read_span(
            self._tracer,
            "cocktail-embedding-processing",
            span_attributes={"cocktail_id": chunking_model.cocktail_model.id},
        ):
            self._logger.info(
                msg="Processing cocktail embedding message item",
                extra={
                    "cocktail.id": chunking_model.cocktail_model.id,
                },
            )

            chunks_to_embed = [chunk for chunk in chunking_model.chunks if chunk.content.strip() != ""]

            if not chunks_to_embed or len(chunks_to_embed) == 0:
                self._logger.warning(
                    msg="No valid chunks to embed for cocktail, skipping embedding process",
                    extra={
                        "cocktail.id": chunking_model.cocktail_model.id,
                    },
                )
                return

            ## -------------------------------
            ## Ensure Qdrant collection exists
            ## -------------------------------
            if not self._collection_exists:
                existing_collections = [c.name for c in self.qdrant_client.get_collections().collections]

                if self._qdrant_options.collection_name not in existing_collections:
                    self.qdrant_client.create_collection(
                        collection_name=self._qdrant_options.collection_name,
                        vectors_config=VectorParams(size=self._qdrant_options.vector_size, distance=Distance.COSINE),
                    )
                self._collection_exists = True

            vector_store = QdrantVectorStore(
                client=self.qdrant_client,
                collection_name=self._qdrant_options.collection_name,
                embedding=HuggingFaceEndpointEmbeddings(
                    model=self._huggingface_options.inference_model,  # http://localhost:8989 | sentence-transformers/all-mpnet-base-v2
                    huggingfacehub_api_token=self._huggingface_options.api_token,
                    task="feature-extraction",
                ),
            )

            self._logger.info(
                msg="Deleting existing cocktail embedding vectors from database",
                extra={
                    "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                    "messaging.kafka.topic_name": self._options.consumer_topic_name,
                    "cocktail.id": chunking_model.cocktail_model.id,
                },
            )

            self.qdrant_client.delete(
                collection_name=self._qdrant_options.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="cocktail_id", match=MatchValue(value=chunking_model.cocktail_model.id))]
                ),
            )


            self._logger.info(
                msg="Sending cocktail embedding result to vector database",
                extra={
                    "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                    "messaging.kafka.topic_name": self._options.consumer_topic_name,
                    "cocktail.id": chunking_model.cocktail_model.id,
                },
            )

            result = vector_store.add_texts(
                texts=[chunk.content for chunk in chunks_to_embed],
                metadatas=[
                    {
                        "cocktail_id": chunking_model.cocktail_model.id,
                        "category": chunk.category,
                        "description": chunk.content,
                    }
                    for chunk in chunks_to_embed
                ],
                ids=[chunks_to_embed[i].to_uuid() for i in range(len(chunks_to_embed))],
            )

            if len(result) == 0:
                self._logger.warning(
                    msg="No embedding results returned",
                    extra={
                        "cocktail.id": chunking_model.cocktail_model.id,
                    },
                )
                return
            

            self._logger.info(
                msg="Ccocktail embedding result successfully stored in vector database",
                extra={
                    "messaging.kafka.bootstrap_servers": self._kafka_consumer_settings.bootstrap_servers,
                    "messaging.kafka.topic_name": self._options.consumer_topic_name,
                    "cocktail.id": chunking_model.cocktail_model.id,
                },
            )
