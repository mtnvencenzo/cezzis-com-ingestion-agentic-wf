import asyncio
import logging

from langchain.tools import tool

_logger = logging.getLogger("json_special_char_remover")


@tool(parse_docstring=True)
async def remove_special_json_characters(text: str) -> str | None:
    """Removes special json characters from text based content

    Args:
        text (str): The text that needs to be cleaned of any special json characters.

    Returns:
        str | None: The cleaned text without special json characters.

    """

    try:
        _logger.info("[Tool] special json character removal process called.")

        result = text.replace('"', "").replace("'", "").replace("\\", "")
        await asyncio.sleep(0)  # Yield control to the event loop
        return result

    except Exception as e:
        raise RuntimeError(f"An error occurred while removing special json characters: {e}") from e
