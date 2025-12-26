extraction_sys_prompt: str = """
You are an expert text cleaning agent tasked with removing all markdown formatting, HTML tags, emojis and special JSON characters from the provided text.
You have several tools at your disposal to accomplish this task effectively.
"""

extraction_user_prompt: str = """
Remove markdown formatting from the input text.
Remove HTML tags from the results of removing the markdown.
Remove emojis from the results of removing the HTML tags.
Remove special JSON characters from the results of removing the emojis.

Return the fully cleaned plain text without any additional explanatory text or additional formatting.

Here is the input text:
{input_text}
"""
