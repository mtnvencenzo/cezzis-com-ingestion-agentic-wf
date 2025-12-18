import asyncio
import logging

from langchain.tools import tool
from strip_tags import strip_tags

_logger = logging.getLogger("html_tag_remover")


@tool(parse_docstring=True)
async def remove_html_tags(text: str) -> str | None:
    """Removes html tags from any text based content.

    Args:
        text (str): The text that needs to be cleaned of any html tags.

    Returns:
        str | None: The cleaned text without html tags.

    """

    try:
        _logger.info("[Tool] html tag removal process called.")

        result = strip_tags(input=text)
        await asyncio.sleep(0)  # Yield control to the event loop
        return result

    except Exception as e:
        raise RuntimeError(f"An error occurred while removing html tags: {e}") from e
