from cezzis_kafka import KafkaConsumerSettings, KafkaProducer
from injector import Binder, Injector, Module, noscope, singleton
from mediatr import Mediator

from cocktails_chunking_agent.application.concerns.chunking.commands.run_chunking_agent_command import (
    RunChunkingAgentCommandHandler,
)
from cocktails_chunking_agent.domain.config import (
    AppOptions,
    KafkaOptions,
    LLMModelOptions,
    LLMOptions,
    get_app_options,
    get_kafka_consumer_settings,
    get_kafka_options,
    get_kafka_producer_settings,
    get_llm_options,
)
from cocktails_chunking_agent.infrastructure.eventing.chunking_event_receiver import ChunkingEventReceiver
from cocktails_chunking_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory

# from cocktails_chunking_agent.application.concerns import (
#     CreateBlobStorageCommandHandler,
#     CreateCosmosDbCommandHandler,
#     CreateKafkaCommandHandler,
# )
# from cocktails_chunking_agent.domain.config import (
#     KafkaOptions,
#     get_kafka_options,
# )
# from cocktails_chunking_agent.infrastructure.services import (
#     AzureBlobService,
#     CosmosDbService,
#     IAzureBlobService,
#     ICosmosDbService,
#     IKafkaService,
#     KafkaService,
# )


def create_injector() -> Injector:
    return Injector([AppModule()])


def mediator_manager(handler_class, is_behavior=False):
    return injector.get(handler_class)


class AppModule(Module):
    def configure(self, binder: Binder):
        app_options = get_app_options()

        llm_model_options = LLMModelOptions(
            model=app_options.llm_model,
            temperature=0.0,
            num_predict=-1,
            verbose=True,
            timeout_seconds=30,
            reasoning=False,
        )

        binder.bind(Mediator, Mediator(handler_class_manager=mediator_manager), scope=singleton)
        binder.bind(KafkaOptions, get_kafka_options(), scope=singleton)
        binder.bind(KafkaConsumerSettings, get_kafka_consumer_settings(), scope=singleton)
        binder.bind(LLMOptions, get_llm_options(), scope=singleton)
        binder.bind(LLMModelOptions, llm_model_options, scope=singleton)
        binder.bind(AppOptions, app_options, scope=singleton)
        binder.bind(RunChunkingAgentCommandHandler, RunChunkingAgentCommandHandler, scope=singleton)
        binder.bind(ChunkingEventReceiver, ChunkingEventReceiver, scope=noscope)
        binder.bind(KafkaProducer, KafkaProducer(get_kafka_producer_settings()), scope=singleton)
        binder.bind(OllamaLLMFactory, OllamaLLMFactory, scope=singleton)


injector = create_injector()
