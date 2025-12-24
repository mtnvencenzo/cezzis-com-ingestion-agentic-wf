import logging

from cezzis_kafka import spawn_consumers_async
from injector import inject
from mediatr import GenericQuery, Mediator

from cocktails_chunking_agent.domain.config.app_options import AppOptions
from cocktails_chunking_agent.domain.config.kafka_options import KafkaOptions
from cocktails_chunking_agent.infrastructure.eventing.chunking_event_receiver import ChunkingEventReceiver


class RunChunkingAgentCommand(GenericQuery[bool]):
    """Command to run the chunking agent"""

    pass


@Mediator.handler
class RunChunkingAgentCommandHandler:
    """Handler for RunChunkingAgentCommand"""

    @inject
    def __init__(self, app_options: AppOptions, kafka_options: KafkaOptions) -> None:
        self.logger = logging.getLogger("run_chunking_agent_command_handler")
        self.app_options = app_options
        self.kafka_options = kafka_options

    async def handle(self, command: RunChunkingAgentCommand) -> bool:
        """Handles the RunChunkingAgentCommand

        Args:
            command (RunChunkingAgentCommand): The command to handle
        Returns:
            bool: True if the agent ran successfully, False otherwise
        """

        self.logger.info("Starting Cocktail Chunking Agent")

        if not self.app_options.enabled:
            self.logger.info("Chunking agent is disabled. Exiting.")
            return False

        await spawn_consumers_async(
            factory_type=ChunkingEventReceiver,
            bootstrap_servers=self.kafka_options.bootstrap_servers,
            consumer_group=self.kafka_options.consumer_group,
            num_consumers=self.app_options.num_consumers,
            topic_name=self.app_options.consumer_topic_name,
            max_poll_interval_ms=self.app_options.max_poll_interval_ms,
            auto_offset_reset=self.app_options.auto_offset_reset,
        )

        return True
