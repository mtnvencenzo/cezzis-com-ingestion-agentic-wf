import logging

from cezzis_kafka import KafkaConsumerSettings
from injector import inject
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings
from langchain_qdrant import QdrantVectorStore
from mediatr import GenericQuery, Mediator
from opentelemetry import trace
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from cocktails_embedding_agent.domain.config import AppOptions, HuggingFaceOptions, QdrantOptions
from cocktails_embedding_agent.domain.models.cocktail_chunking_model import (
    CocktailChunkingModel,
)


class ProcessEmbeddingEventCommand(GenericQuery[bool]):
    def __init__(self, model: CocktailChunkingModel) -> None:
        self.model = model


@Mediator.behavior
class ProcessEmbeddingEventCommandValidator:
    def handle(self, command: ProcessEmbeddingEventCommand, next) -> None:
        if not command.model or not command.model.cocktail_model or not command.model.cocktail_model.id:
            raise ValueError("Invalid cocktail model provided for embedding processing")

        chunks_to_embed = [chunk for chunk in command.model.chunks if chunk.content.strip() != ""]

        if not chunks_to_embed or len(chunks_to_embed) == 0:
            raise ValueError("No valid chunks to embed for cocktail, skipping embedding process")

        return next()


@Mediator.handler
class ProcessEmbeddingEventCommandHandler:
    collection_exists: bool = False

    @inject
    def __init__(
        self,
        kafka_consumer_settings: KafkaConsumerSettings,
        app_options: AppOptions,
        kafka_consumer_options: KafkaConsumerSettings,
        hugging_face_options: HuggingFaceOptions,
        qdrant_client: QdrantClient,
        qdrant_options: QdrantOptions,
    ) -> None:
        self.kafka_consiumer_settings = kafka_consumer_options
        self.app_options = app_options
        self.logger = logging.getLogger("process_embedding_event_command_handler")
        self.tracer = trace.get_tracer("embedding_agent")
        self.qdrant_client = qdrant_client
        self.hugging_face_options = hugging_face_options
        self.qdrant_options = qdrant_options
        self.kafka_consumer_settings = kafka_consumer_settings

    async def handle(self, command: ProcessEmbeddingEventCommand) -> bool:
        assert command.model.cocktail_model is not None
        assert command.model.chunks is not None

        self.logger.info(
            msg="Processing cocktail embedding message item",
            extra={
                "cocktail_id": command.model.cocktail_model.id,
            },
        )

        chunks_to_embed = [chunk for chunk in command.model.chunks if chunk.content.strip() != ""]
        if not chunks_to_embed or len(chunks_to_embed) == 0:
            self.logger.warning(
                msg="No valid chunks to embed for cocktail, skipping embedding process",
                extra={
                    "cocktail_id": command.model.cocktail_model.id,
                },
            )
            return False

        ## -------------------------------
        ## Ensure Qdrant collection exists
        ## -------------------------------
        if not ProcessEmbeddingEventCommandHandler.collection_exists:
            existing_collections = [c.name for c in self.qdrant_client.get_collections().collections]

            if self.qdrant_options.collection_name not in existing_collections:
                self.qdrant_client.create_collection(
                    collection_name=self.qdrant_options.collection_name,
                    vectors_config=VectorParams(size=self.qdrant_options.vector_size, distance=Distance.COSINE),
                )
            ProcessEmbeddingEventCommandHandler.collection_exists = True

        vector_store = QdrantVectorStore(
            client=self.qdrant_client,
            collection_name=self.qdrant_options.collection_name,
            embedding=HuggingFaceEndpointEmbeddings(
                model=self.hugging_face_options.inference_model,  # http://localhost:8989 | sentence-transformers/all-mpnet-base-v2
                huggingfacehub_api_token=self.hugging_face_options.api_token,
                task="feature-extraction",
            ),
        )

        self.logger.info(
            msg="Deleting existing cocktail embedding vectors from database",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_consumer_settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.consumer_topic_name,
                "cocktail_id": command.model.cocktail_model.id,
            },
        )

        self.qdrant_client.delete(
            collection_name=self.qdrant_options.collection_name,
            points_selector=Filter(
                must=[FieldCondition(key="cocktail_id", match=MatchValue(value=command.model.cocktail_model.id))]
            ),
        )

        self.logger.info(
            msg="Sending cocktail embedding result to vector database",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_consumer_settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.consumer_topic_name,
                "cocktail_id": command.model.cocktail_model.id,
            },
        )

        result = vector_store.add_texts(
            texts=[chunk.content for chunk in chunks_to_embed],
            metadatas=[
                {
                    "cocktail_id": command.model.cocktail_model.id,
                    "category": chunk.category,
                    "description": chunk.content,
                }
                for chunk in chunks_to_embed
            ],
            ids=[chunks_to_embed[i].to_uuid() for i in range(len(chunks_to_embed))],
        )

        if len(result) == 0:
            raise ValueError("No embedding results returned from vector store")

        self.logger.info(
            msg="Cocktail embedding succeeded",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_consumer_settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.consumer_topic_name,
                "cocktail_id": command.model.cocktail_model.id,
                "cocktail_ingestion_state": "embedding-succeeded",
            },
        )

        return True
