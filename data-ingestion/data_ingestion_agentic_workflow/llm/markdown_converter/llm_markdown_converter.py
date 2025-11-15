import asyncio
import os

import httpx
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

# from langfuse.langchain import CallbackHandler
from data_ingestion_agentic_workflow.llm.markdown_converter.llm_markdown_converter_prompts import (
    md_converter_human_prompt,
    md_converter_sys_prompt,
)


class LLMMarkdownConverter:
    def __init__(self, ollama_host: str, langfuse_host: str, langfuse_public_key: str, langfuse_secret_key: str):
        self.llm = OllamaLLM(model="llama3.2:3b", base_url=ollama_host, temperature=0.1, num_predict=2024, verbose=True)
        self._llm_timeout = 180.0

        os.environ["LANGFUSE_BASE_URL"] = langfuse_host
        os.environ["LANGFUSE_HOST"] = langfuse_host
        os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = langfuse_secret_key

        # self._langfuse_handler = LangfuseCallbackHandler()

    async def convert_markdown(self, markdown_text: str) -> str:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", md_converter_sys_prompt),
                ("human", md_converter_human_prompt),
            ]
        )
        chain = prompt | self.llm | StrOutputParser()

        try:
            result = await chain.ainvoke({"markdown": markdown_text}, timeout=self._llm_timeout)

            return result

        except asyncio.TimeoutError:
            raise TimeoutError(f"LLM call timed out after {self._llm_timeout} seconds")
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP error during LLM call: {e}")
        except Exception as e:
            raise RuntimeError(f"An error occurred during LLM call: {e}")
