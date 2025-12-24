import asyncio
import logging

from emoji import replace_emoji
from langchain.tools import tool

_logger = logging.getLogger("emoji_remover")


@tool(parse_docstring=True)
async def remove_emojis(text: str) -> str | None:
    """Removes emojis from text based content

    Args:
        text (str): The text that needs to be cleaned of any emojis.

    Returns:
        str | None: The cleaned text without emojis.

    """

    try:
        _logger.info("[Tool] emoji removal process called.")

        result = replace_emoji(text, replace="")
        await asyncio.sleep(0)  # Yield control to the event loop
        return result

    except Exception as e:
        raise RuntimeError(f"An error occurred while removing emojis: {e}") from e
