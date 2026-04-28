import asyncio
import logging

from langchain.tools import tool
from strip_markdown import strip_markdown

_logger = logging.getLogger("markdown_remover")


@tool(parse_docstring=True)
async def remove_markdown(markdown_text: str) -> str | None:
    """Removes markdown formatting from any text based content.

    Args:
        markdown_text (str): The text that needs to be cleaned of any markdown syntax.

    Returns:
        str | None: The cleaned text without markdown formatting.

    """

    try:
        _logger.info("[Tool] markdown removal process called.")

        result = strip_markdown(md=markdown_text)
        result = _strip_code_fences(result)
        result = result.replace("`", "")  # Remove any remaining backticks
        await asyncio.sleep(0)  # Yield control to the event loop
        return result

    except Exception as e:
        raise RuntimeError(f"An error occurred during markdown removal process: {e}") from e


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return text
