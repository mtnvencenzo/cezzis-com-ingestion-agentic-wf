import asyncio
import logging
from typing import Any, Coroutine

from cezzis_kafka import spawn_consumers_async

from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_evt_receiver import (
    CocktailsExtractionEventReceiver,
)
from data_ingestion_agentic_workflow.agents.extraction_agent.ext_agent_options import get_ext_agent_options
from data_ingestion_agentic_workflow.infra.kafka_options import KafkaOptions, get_kafka_options

logger: logging.Logger = logging.getLogger("ext_agent_app_runner")


def run_extraction_agent() -> Coroutine[Any, Any, None]:
    """Main function to run the extraction Kafka agent

    Returns:
        CoroutineType[Any, Any, None]: Coroutine object to run the extraction agent consumers
    """

    logger.info("Starting Cocktail Extraction Agent")
    options = get_ext_agent_options()
    kafka_options: KafkaOptions = get_kafka_options()

    if not options.enabled:
        logger.info("Extraction agent is disabled. Exiting.")
        return asyncio.sleep(0)  # Return a no-op coroutine

    return spawn_consumers_async(
        factory_type=CocktailsExtractionEventReceiver,
        bootstrap_servers=kafka_options.bootstrap_servers,
        consumer_group=kafka_options.consumer_group,
        num_consumers=options.num_consumers,
        topic_name=options.consumer_topic_name,
        max_poll_interval_ms=options.max_poll_interval_ms,
        auto_offset_reset=options.auto_offset_reset,
    )
