from cezzis_kafka import KafkaConsumerSettings

from cocktails_extraction_agent.domain.config.ext_agent_options import get_ext_agent_options
from cocktails_extraction_agent.domain.config.kafka_options import get_kafka_options


def get_kafka_consumer_settings() -> KafkaConsumerSettings:
    """Get Kafka consumer settings based on KafkaOptions.

    Returns:
        KafkaConsumerSettings: The Kafka consumer settings.
    """
    kafka_options = get_kafka_options()
    ext_agent_options = get_ext_agent_options()
    return KafkaConsumerSettings(
        bootstrap_servers=kafka_options.bootstrap_servers,
        consumer_group=kafka_options.consumer_group,
        num_consumers=ext_agent_options.num_consumers,
        topic_name=ext_agent_options.consumer_topic_name,
        max_poll_interval_ms=ext_agent_options.max_poll_interval_ms,
        auto_offset_reset=ext_agent_options.auto_offset_reset,
    )
