import logging

from cezzis_kafka import KafkaProducerSettings

from cocktails_extraction_agent.domain.config.kafka_options import get_kafka_options

logger = logging.getLogger("kafka_producer")


def get_kafka_producer_settings() -> KafkaProducerSettings:
    """Get Kafka producer settings based on KafkaOptions.

    Returns:
        KafkaProducerSettings: The Kafka producer settings.
    """
    kafka_options = get_kafka_options()
    return KafkaProducerSettings(
        bootstrap_servers=kafka_options.bootstrap_servers,
        on_delivery=lambda err, msg: (
            logger.error(f"Message delivery failed: {err}")
            if err
            else logger.info(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
        ),
    )
