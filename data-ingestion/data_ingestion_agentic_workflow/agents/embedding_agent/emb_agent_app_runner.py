import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

from cezzis_kafka import spawn_consumers_async

from data_ingestion_agentic_workflow.agents.embedding_agent.emb_agent_app_options import get_emb_agent_options
from data_ingestion_agentic_workflow.agents.embedding_agent.emb_agent_evt_processor import CocktailsEmbeddingProcessor

logger: logging.Logger = logging.getLogger("emb_agent_runner")


def run_embedding_agent() -> Coroutine[Any, Any, None]:
    """Main function to run the embedding agent

    Returns:
        CoroutineType[Any, Any, None]: Coroutine object to run the embedding agent consumers
    """

    logger.info("Starting Cocktail Embedding Agent")
    options = get_emb_agent_options()

    if not options.enabled:
        logger.info("Embedding agent is disabled. Exiting.")
        return asyncio.sleep(0)  # Return a no-op coroutine

    return spawn_consumers_async(
        factory_type=CocktailsEmbeddingProcessor,
        num_consumers=options.num_consumers,
        bootstrap_servers=options.bootstrap_servers,
        consumer_group=options.consumer_group,
        topic_name=options.embedding_topic_name,
    )
