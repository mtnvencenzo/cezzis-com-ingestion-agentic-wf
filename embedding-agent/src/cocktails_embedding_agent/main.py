import asyncio
import logging
import sys

from mediatr import Mediator

from cocktails_embedding_agent.app_module import injector
from cocktails_embedding_agent.application import initialize_opentelemetry
from cocktails_embedding_agent.application.behaviors.exception_handling.global_exception_handler import (
    global_exception_handler,
)
from cocktails_embedding_agent.application.concerns.embedding import RunEmbeddingAgentCommand

sys.excepthook = global_exception_handler

logger = logging.getLogger("main")


async def main():
    """Main function to run the cocktails data ingestion embedding agent."""
    global logger

    initialize_opentelemetry()
    logger = logging.getLogger("main")
    logger.info("Starting cocktails ingestion embedding agent...")

    mediator = injector.get(Mediator)

    try:
        await mediator.send_async(RunEmbeddingAgentCommand())
    except asyncio.CancelledError:
        logger.info("Application cancelled")
    except Exception as e:
        logger.exception("Application error", extra={"error": str(e)})
        raise

    logger.info("Cocktails ingestion embedding agent stopped.")


def main_entry():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    finally:
        logger.info("Application shutdown complete.")


if __name__ == "__main__":
    main_entry()
