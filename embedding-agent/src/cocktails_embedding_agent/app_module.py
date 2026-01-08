from cezzis_kafka import KafkaConsumerSettings
from injector import Binder, Injector, Module, noscope, singleton
from mediatr import Mediator

from cocktails_embedding_agent.application.concerns.embedding.commands.run_embedding_agent_command import (
    RunEmbeddingAgentCommandHandler,
)
from cocktails_embedding_agent.domain.config import (
    AISearchApiOptions,
    AppOptions,
    get_aisearch_api_options,
    get_app_options,
    get_kafka_consumer_settings,
    get_kafka_options,
    get_oauth_options,
    kafka_options,
)
from cocktails_embedding_agent.domain.config.oauth_options import OAuthOptions
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.aisearch_client import AISearchClient
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.iaisearch_client import IAISearchClient
from cocktails_embedding_agent.infrastructure.clients.oauth.oauth_token_provider import (
    IOAuthTokenProvider,
    OAuthTokenProvider,
)
from cocktails_embedding_agent.infrastructure.eventing.embedding_event_receiver import EmbeddingEventReceiver


def create_injector() -> Injector:
    return Injector([AppModule()])


def mediator_manager(handler_class, is_behavior=False):
    return injector.get(handler_class)


class AppModule(Module):
    def configure(self, binder: Binder):
        binder.bind(Mediator, Mediator(handler_class_manager=mediator_manager), scope=singleton)
        binder.bind(kafka_options.KafkaOptions, get_kafka_options(), scope=singleton)
        binder.bind(KafkaConsumerSettings, get_kafka_consumer_settings(), scope=singleton)
        binder.bind(AppOptions, get_app_options(), scope=singleton)
        binder.bind(AISearchApiOptions, get_aisearch_api_options(), scope=singleton)
        binder.bind(OAuthOptions, get_oauth_options(), scope=singleton)
        binder.bind(IOAuthTokenProvider, OAuthTokenProvider, scope=singleton)
        binder.bind(RunEmbeddingAgentCommandHandler, RunEmbeddingAgentCommandHandler, scope=singleton)
        binder.bind(IAISearchClient, AISearchClient, scope=singleton)
        binder.bind(EmbeddingEventReceiver, EmbeddingEventReceiver, scope=noscope)


injector = create_injector()
