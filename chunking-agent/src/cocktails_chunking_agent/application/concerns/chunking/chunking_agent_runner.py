import asyncio
import logging
from typing import Any, Coroutine

from cezzis_kafka import spawn_consumers_async

from cocktails_chunking_agent.application.concerns.chunking.chunking_agent_evt_receiver import (
    ChunkingAgentEventReceiver,
)
from cocktails_chunking_agent.domain.config.chunking_agent_options import get_chunking_agent_options
from cocktails_chunking_agent.domain.config.kafka_options import KafkaOptions, get_kafka_options

logger: logging.Logger = logging.getLogger("chunking_agent_app_runner")


def run_chunking_agent() -> Coroutine[Any, Any, None]:
    """Main function to run the chunking Kafka agent

    Returns:
        CoroutineType[Any, Any, None]: Coroutine object to run the chunking agent consumers
    """

    logger.info("Starting Cocktail Chunking Agent")
    options = get_chunking_agent_options()
    kafka_options: KafkaOptions = get_kafka_options()

    if not options.enabled:
        logger.info("Chunking agent is disabled. Exiting.")
        return asyncio.sleep(0)  # Return a no-op coroutine

    return spawn_consumers_async(
        factory_type=ChunkingAgentEventReceiver,
        bootstrap_servers=kafka_options.bootstrap_servers,
        consumer_group=kafka_options.consumer_group,
        num_consumers=options.num_consumers,
        topic_name=options.consumer_topic_name,
        max_poll_interval_ms=options.max_poll_interval_ms,
        auto_offset_reset=options.auto_offset_reset,
    )
