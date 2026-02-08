import logging

from cezzis_kafka import KafkaConsumerSettings
from injector import inject
from mediatr import GenericQuery, Mediator
from opentelemetry import trace

from cocktails_embedding_agent.domain.config import AppOptions
from cocktails_embedding_agent.domain.models.cocktail_chunking_model import CocktailChunkingModel
from cocktails_embedding_agent.infrastructure.clients.aisearch_api import aisearch_models
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.aisearch_models import (
    CocktailDescriptionChunk,
    CocktailEmbeddingModel,
    CocktailEmbeddingRq,
    CocktailSearchIngredientModel,
    CocktailSearchKeywords,
)
from cocktails_embedding_agent.infrastructure.clients.aisearch_api.iaisearch_client import IAISearchClient


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
        aisearch_client: IAISearchClient,
    ) -> None:
        self.kafka_consiumer_settings = kafka_consumer_options
        self.app_options = app_options
        self.logger = logging.getLogger("process_embedding_event_command_handler")
        self.tracer = trace.get_tracer("embedding_agent")
        self.kafka_consumer_settings = kafka_consumer_settings
        self.aisearch_client = aisearch_client

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

        self.logger.info(
            msg="Sending cocktail chunking result to ai search api for vector embedding storage",
            extra={
                "messaging.kafka.bootstrap_servers": self.kafka_consumer_settings.bootstrap_servers,
                "messaging.kafka.topic_name": self.app_options.consumer_topic_name,
                "cocktail_id": command.model.cocktail_model.id,
            },
        )

        await self.aisearch_client.create_embeddings(
            embedding_rq=CocktailEmbeddingRq(
                contentChunks=[
                    CocktailDescriptionChunk(content=chunk.content, category=chunk.category)
                    for chunk in chunks_to_embed
                ],
                cocktailEmbeddingModel=CocktailEmbeddingModel(
                    id=command.model.cocktail_model.id,
                    title=command.model.cocktail_model.title,
                    descriptiveTitle=command.model.cocktail_model.descriptiveTitle,
                    serves=command.model.cocktail_model.serves,
                    prepTimeMinutes=command.model.cocktail_model.prepTimeMinutes,
                    isIba=command.model.cocktail_model.isIba,
                    ingredients=[
                        CocktailSearchIngredientModel(
                            name=ingredient.name,
                            units=ingredient.units,
                            display=ingredient.display,
                            suggestions=ingredient.suggestions,
                            preparation=aisearch_models.CocktailSearchPreparationTypeModel[
                                ingredient.preparation.value
                            ],
                            uoM=aisearch_models.CocktailSearchUofMTypeModel[ingredient.uoM.value],
                            types=[
                                aisearch_models.CocktailSearchIngredientTypeModel[type_.value]
                                for type_ in ingredient.types
                            ],
                            applications=[
                                aisearch_models.CocktailSearchIngredientApplicationTypeModel[application.value]
                                for application in ingredient.applications
                            ],
                            requirement=aisearch_models.CocktailSearchIngredientRequirementTypeModel[
                                ingredient.requirement.value
                            ],
                        )
                        for ingredient in command.model.cocktail_model.ingredients
                    ],
                    glassware=[
                        aisearch_models.CocktailSearchGlasswareTypeModel[glass.value]
                        for glass in command.model.cocktail_model.glassware
                    ],
                    rating=command.model.cocktail_model.rating.rating,
                    searchTiles=[s.uri for s in command.model.cocktail_model.searchTiles],
                ),
                cocktailKeywords=CocktailSearchKeywords(
                    keywordsBaseSpirit=[kw for kw in (command.model.cocktail_model.keywords.keywordsBaseSpirit or [])]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsBaseSpirit
                    else [],
                    keywordsFlavorProfile=[
                        kw for kw in (command.model.cocktail_model.keywords.keywordsFlavorProfile or [])
                    ]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsFlavorProfile
                    else [],
                    keywordsTechnique=[kw for kw in (command.model.cocktail_model.keywords.keywordsTechnique or [])]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsTechnique
                    else [],
                    keywordsOccasion=[kw for kw in (command.model.cocktail_model.keywords.keywordsOccasion or [])]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsOccasion
                    else [],
                    keywordsCocktailFamily=[
                        kw for kw in (command.model.cocktail_model.keywords.keywordsCocktailFamily or [])
                    ]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsCocktailFamily
                    else [],
                    keywordsMood=[kw for kw in (command.model.cocktail_model.keywords.keywordsMood or [])]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsMood
                    else [],
                    keywordsSearchTerms=[kw for kw in (command.model.cocktail_model.keywords.keywordsSearchTerms or [])]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsSearchTerms
                    else [],
                    keywordsSpiritSubtype=[
                        kw for kw in (command.model.cocktail_model.keywords.keywordsSpiritSubtype or [])
                    ]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsSpiritSubtype
                    else [],
                    keywordsSeason=[kw for kw in (command.model.cocktail_model.keywords.keywordsSeason or [])]
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsSeason
                    else [],
                    keywordsStrength=command.model.cocktail_model.keywords.keywordsStrength
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsStrength
                    else None,
                    keywordsTemperature=command.model.cocktail_model.keywords.keywordsTemperature
                    if command.model.cocktail_model
                    and command.model.cocktail_model.keywords
                    and command.model.cocktail_model.keywords.keywordsTemperature
                    else None,
                ),
            )
        )

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
