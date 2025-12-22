import logging

from cezzis_kafka import spawn_consumers_async
from injector import inject
from mediatr import GenericQuery, Mediator

from cocktails_extraction_agent.application.concerns.extraction.extraction_event_receiver import ExtractionEventReceiver
from cocktails_extraction_agent.domain.config.ext_agent_options import ExtractionAgentOptions
from cocktails_extraction_agent.domain.config.kafka_options import KafkaOptions


class RunAgentCommand(GenericQuery[bool]):
    """Command to run the extraction agent"""

    pass


@Mediator.handler
class RunAgentCommandHandler:
    """Handler for RunAgentCommand"""

    @inject
    def __init__(self, ext_agent_options: ExtractionAgentOptions, kafka_options: KafkaOptions) -> None:
        self.logger = logging.getLogger("create_kafka_command_handler")
        self.ext_agent_options = ext_agent_options
        self.kafka_options = kafka_options

    async def handle(self, command: RunAgentCommand) -> bool:
        """Handles the RunAgentCommand

        Args:
            command (RunAgentCommand): The command to handle

        Returns:
            bool: True if the agent ran successfully, False otherwise
        """

        self.logger.info("Starting Cocktail Extraction Agent")

        if not self.ext_agent_options.enabled:
            self.logger.info("Extraction agent is disabled. Exiting.")
            return False

        await spawn_consumers_async(
            factory_type=ExtractionEventReceiver,
            bootstrap_servers=self.kafka_options.bootstrap_servers,
            consumer_group=self.kafka_options.consumer_group,
            num_consumers=self.ext_agent_options.num_consumers,
            topic_name=self.ext_agent_options.consumer_topic_name,
            max_poll_interval_ms=self.ext_agent_options.max_poll_interval_ms,
            auto_offset_reset=self.ext_agent_options.auto_offset_reset,
        )

        return True
