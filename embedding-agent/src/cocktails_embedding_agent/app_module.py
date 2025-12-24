from cezzis_kafka import KafkaConsumerSettings
from injector import Binder, Injector, Module, noscope, singleton
from mediatr import Mediator
from qdrant_client import QdrantClient

from cocktails_embedding_agent.application.concerns.embedding.commands.run_embedding_agent_command import (
    RunEmbeddingAgentCommandHandler,
)
from cocktails_embedding_agent.domain.config import (
    AppOptions,
    HuggingFaceOptions,
    QdrantOptions,
    get_app_options,
    get_huggingface_options,
    get_kafka_consumer_settings,
    get_kafka_options,
    get_qdrant_options,
    kafka_options,
)
from cocktails_embedding_agent.infrastructure.eventing.embedding_event_receiver import EmbeddingEventReceiver


def create_injector() -> Injector:
    return Injector([AppModule()])


def mediator_manager(handler_class, is_behavior=False):
    return injector.get(handler_class)


class AppModule(Module):
    def configure(self, binder: Binder):
        qdrant_options = get_qdrant_options()
        qdrant_client = QdrantClient(
            url=qdrant_options.host,  # http://localhost:6333 | https://aca-vec-eus-glo-qdrant-001.proudfield-08e1f932.eastus.azurecontainerapps.io
            api_key=qdrant_options.api_key if qdrant_options.api_key else None,
            port=qdrant_options.port,
            https=qdrant_options.use_https,
            prefer_grpc=False,
            timeout=60,
        )

        binder.bind(Mediator, Mediator(handler_class_manager=mediator_manager), scope=singleton)
        binder.bind(Mediator, Mediator(handler_class_manager=mediator_manager), scope=singleton)
        binder.bind(kafka_options.KafkaOptions, get_kafka_options(), scope=singleton)
        binder.bind(KafkaConsumerSettings, get_kafka_consumer_settings(), scope=singleton)
        binder.bind(QdrantOptions, get_qdrant_options(), scope=singleton)
        binder.bind(AppOptions, get_app_options(), scope=singleton)
        binder.bind(HuggingFaceOptions, get_huggingface_options(), scope=singleton)
        binder.bind(RunEmbeddingAgentCommandHandler, RunEmbeddingAgentCommandHandler, scope=singleton)
        binder.bind(EmbeddingEventReceiver, EmbeddingEventReceiver, scope=noscope)
        binder.bind(QdrantClient, qdrant_client, scope=singleton)


injector = create_injector()
