import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

from cezzis_kafka import spawn_consumers_async

from cocktails_embedding_agent.application.concerns.embedding.emb_agent_evt_receiver import (
    EmbeddingAgentEventReceiver,
)
from cocktails_embedding_agent.domain.config.emb_agent_options import get_emb_agent_options
from cocktails_embedding_agent.domain.config.kafka_options import KafkaOptions, get_kafka_options

logger: logging.Logger = logging.getLogger("emb_agent_runner")


def run_embedding_agent() -> Coroutine[Any, Any, None]:
    """Main function to run the embedding agent

    Returns:
        CoroutineType[Any, Any, None]: Coroutine object to run the embedding agent consumers
    """

    logger.info("Starting Cocktail Embedding Agent")
    options = get_emb_agent_options()
    kafka_options: KafkaOptions = get_kafka_options()

    if not options.enabled:
        logger.info("Embedding agent is disabled. Exiting.")
        return asyncio.sleep(0)  # Return a no-op coroutine

    return spawn_consumers_async(
        factory_type=EmbeddingAgentEventReceiver,
        bootstrap_servers=kafka_options.bootstrap_servers,
        consumer_group=kafka_options.consumer_group,
        num_consumers=options.num_consumers,
        topic_name=options.consumer_topic_name,
    )
