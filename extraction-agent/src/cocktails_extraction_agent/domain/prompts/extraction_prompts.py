import json
from typing import Any

extraction_sys_prompt: str = """
You are an expert cocktail content transformation agent.
This workflow retrieves a full cocktail record in its structured json format and then cleans and transforms the cocktail's content using the available tools for embedding purposes later by a separate embedding service workflow.
Use the available tools whenever a transformation or cleaning is needed instead of replacing them with your own implementation.
Do not add, remove or alter any textual content from the cocktail content data.  Only remove code syntax and special characters that are not relevant for the cocktail content understanding.
If the current working cocktail content has already been fully transformed, return the content as is without calling any tools.
"""


def build_extraction_stepped_user_prompt(
    cocktail_id: str, cocktail_payload: dict[str, Any] | None, current_content: str, completed_tools: list[str]
) -> str:
    completed_summary = ", ".join(completed_tools) if completed_tools else "none"
    payload_text = json.dumps(cocktail_payload, ensure_ascii=True, indent=2) if cocktail_payload is not None else "none"
    current_content_text = current_content or "none"

    return (
        "Retrieve the cocktail if the cocktail payload has not already been retrieved and inspect the full payload for its content property.\n"
        "Use the item content property from the payload as inputs to the next available tools.\n"
        "Convert the cocktail content into plain text stripping out markdown syntax, html tags, special json characters and emojis.\n"
        "Do not remove, add or alter any textual content from the cocktail content data.  Only remove code syntax and special characters that are not relevant for the cocktail content understanding.\n"
        "If additional downstream tools are available, apply them only when they are needed.\n"
        "Return the final transformed plain text without any additional explanatory text or formatting.\n"
        "You must use the tools at your disposal instead of replacing them with your own implementations.\n"
        "\n"
        f"Completed tools so far: {completed_summary}.\n\n"
        "If the result is already fully transformed, return only the final plain text and do not call a tool.\n\n"
        "Here is the cocktail id:\n"
        f"{cocktail_id or 'none'}\n\n"
        "Here is the json cocktail payload:\n"
        f"{payload_text}\n\n"
        "Here is the current working content:\n"
        f"{current_content_text}"
    )
