from injector import Binder, Injector, Module, singleton
from mediatr import Mediator


def create_injector() -> Injector:
    return Injector([AppModule()])


def my_class_handler_manager(handler_class, is_behavior=False):
    if is_behavior:
        # custom logic
        pass

    return injector.get(handler_class)


class AppModule(Module):
    def configure(self, binder: Binder):
        binder.bind(Mediator, Mediator(handler_class_manager=my_class_handler_manager), scope=singleton)
        # For azure blob storage setup
        # binder.bind(AzureStorageOptions, get_azure_storage_options(), scope=singleton)
        # binder.bind(IAzureBlobService, AzureBlobService, scope=singleton)
        # binder.bind(CreateBlobStorageCommandHandler, CreateBlobStorageCommandHandler, scope=noscope)
        # for kafka setup
        # binder.bind(KafkaOptions, get_kafka_options(), scope=singleton)
        # binder.bind(IKafkaService, KafkaService, scope=singleton)
        # binder.bind(CreateKafkaCommandHandler, CreateKafkaCommandHandler, scope=noscope)
        # For CosmosDb Setup
        # binder.bind(CosmosDbOptions, get_cosmosdb_options(), scope=singleton)
        # binder.bind(ICosmosDbService, CosmosDbService, scope=singleton)
        # binder.bind(CreateCosmosDbCommandHandler, CreateCosmosDbCommandHandler, scope=noscope)


injector = create_injector()
