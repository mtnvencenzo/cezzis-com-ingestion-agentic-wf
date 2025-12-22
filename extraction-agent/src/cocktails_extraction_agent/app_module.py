from cezzis_kafka import KafkaConsumerSettings, KafkaProducer
from injector import Binder, Injector, Module, noscope, singleton
from mediatr import Mediator

from cocktails_extraction_agent.application.concerns import ExtractionEventReceiver, RunAgentCommandHandler
from cocktails_extraction_agent.domain.config import (
    ExtractionAgentOptions,
    KafkaOptions,
    get_ext_agent_options,
    get_kafka_options,
)
from cocktails_extraction_agent.domain.config.kafka_consumer_settings import get_kafka_consumer_settings
from cocktails_extraction_agent.domain.config.kafka_producer_settings import get_kafka_producer_settings


def create_injector() -> Injector:
    return Injector([AppModule()])


def my_class_handler_manager(handler_class, is_behavior=False):
    if is_behavior:
        pass

    return injector.get(handler_class)


class AppModule(Module):
    def configure(self, binder: Binder):
        binder.bind(Mediator, Mediator(handler_class_manager=my_class_handler_manager), scope=singleton)
        binder.bind(KafkaOptions, get_kafka_options(), scope=singleton)
        binder.bind(KafkaConsumerSettings, get_kafka_consumer_settings(), scope=singleton)
        binder.bind(ExtractionAgentOptions, get_ext_agent_options(), scope=singleton)
        binder.bind(RunAgentCommandHandler, RunAgentCommandHandler, scope=singleton)
        binder.bind(ExtractionEventReceiver, ExtractionEventReceiver, scope=noscope)
        binder.bind(KafkaProducer, KafkaProducer(get_kafka_producer_settings()), scope=singleton)


injector = create_injector()
