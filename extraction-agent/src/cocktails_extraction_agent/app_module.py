from cezzis_kafka import KafkaConsumerSettings, KafkaProducer
from injector import Binder, Injector, Module, noscope, singleton
from mediatr import Mediator

from cocktails_extraction_agent.application.concerns import RunExtractionAgentCommandHandler
from cocktails_extraction_agent.domain.config import (
    AppOptions,
    KafkaOptions,
    get_app_options,
    get_kafka_options,
)
from cocktails_extraction_agent.domain.config.kafka_consumer_settings import get_kafka_consumer_settings
from cocktails_extraction_agent.domain.config.kafka_producer_settings import get_kafka_producer_settings
from cocktails_extraction_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_extraction_agent.domain.config.llm_options import LLMOptions, get_llm_options
from cocktails_extraction_agent.infrastructure.eventing import ExtractionEventReceiver
from cocktails_extraction_agent.infrastructure.llm.llm_content_cleaner import LLMContentCleaner
from cocktails_extraction_agent.infrastructure.llm.ollama_llm_factory import OllamaLLMFactory


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
        binder.bind(RunExtractionAgentCommandHandler, RunExtractionAgentCommandHandler, scope=singleton)
        binder.bind(ExtractionEventReceiver, ExtractionEventReceiver, scope=noscope)
        binder.bind(KafkaProducer, KafkaProducer(get_kafka_producer_settings()), scope=singleton)
        binder.bind(OllamaLLMFactory, OllamaLLMFactory, scope=singleton)
        binder.bind(LLMContentCleaner, LLMContentCleaner, scope=singleton)


injector = create_injector()
