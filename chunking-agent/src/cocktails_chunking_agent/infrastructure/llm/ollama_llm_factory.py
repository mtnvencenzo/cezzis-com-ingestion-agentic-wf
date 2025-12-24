from injector import inject
from langchain_ollama import ChatOllama

from cocktails_chunking_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_chunking_agent.domain.config.llm_options import LLMOptions


class OllamaLLMFactory:
    """Factory class for creating Ollama LLM instances."""

    @inject
    def __init__(self, llm_options: LLMOptions, llm_model_options: LLMModelOptions) -> None:
        self.llm_options = llm_options
        self.llm_model_options = llm_model_options

    def get_ollama_chat(
        self,
        name: str,
    ) -> ChatOllama:
        """Create and return an OllamaLLM chat model.

        Args:
            name (str): The name of the model.

        """

        return ChatOllama(
            name=name,
            verbose=self.llm_model_options.verbose or False,
            model=self.llm_model_options.model,
            base_url=self.llm_options.llm_host,
            reasoning=self.llm_model_options.reasoning,
            mirostat=self.llm_model_options.mirostat,
            mirostat_eta=self.llm_model_options.mirostat_eta,
            mirostat_tau=self.llm_model_options.mirostat_tau,
            num_ctx=self.llm_model_options.num_ctx,
            num_gpu=self.llm_model_options.num_gpu,
            num_thread=self.llm_model_options.num_thread,
            num_predict=self.llm_model_options.num_predict,
            repeat_last_n=self.llm_model_options.repeat_last_n,
            repeat_penalty=self.llm_model_options.repeat_penalty,
            temperature=self.llm_model_options.temperature,
            seed=self.llm_model_options.seed,
            stop=self.llm_model_options.stop,
            tfs_z=self.llm_model_options.tfs_z,
            top_k=self.llm_model_options.top_k,
            top_p=self.llm_model_options.top_p,
            format=self.llm_model_options.format,
            keep_alive=self.llm_model_options.keep_alive,
            client_kwargs=self.llm_model_options.client_kwargs,
            async_client_kwargs=self.llm_model_options.async_client_kwargs,
            sync_client_kwargs=self.llm_model_options.sync_client_kwargs,
        )
