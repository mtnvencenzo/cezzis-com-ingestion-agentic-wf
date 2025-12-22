from langchain_ollama import ChatOllama, OllamaLLM

from cocktails_extraction_agent.domain.config.llm_model_options import LLMModelOptions
from cocktails_extraction_agent.domain.config.llm_options import LLMOptions


def get_ollama_model_client(name: str, llm_options: LLMOptions, llm_model_options: LLMModelOptions) -> OllamaLLM:
    """Create and return an OllamaLLM client configured with the given LLM options and model settings.

    Args:
        llm_options (LLMOptions): The LLM options for configuration.
        llm_model_options (LLMModelOptions): The model settings for configuration.

    Returns:
        OllamaLLM: The configured OllamaLLM client.
    """
    return OllamaLLM(
        name=name,
        model=llm_model_options.model,
        base_url=llm_options.llm_host,
        verbose=llm_model_options.verbose or False,
        reasoning=llm_model_options.reasoning,
        mirostat=llm_model_options.mirostat,
        mirostat_eta=llm_model_options.mirostat_eta,
        mirostat_tau=llm_model_options.mirostat_tau,
        num_ctx=llm_model_options.num_ctx,
        num_gpu=llm_model_options.num_gpu,
        num_thread=llm_model_options.num_thread,
        num_predict=llm_model_options.num_predict,
        repeat_last_n=llm_model_options.repeat_last_n,
        repeat_penalty=llm_model_options.repeat_penalty,
        temperature=llm_model_options.temperature,
        seed=llm_model_options.seed,
        stop=llm_model_options.stop,
        tfs_z=llm_model_options.tfs_z,
        top_k=llm_model_options.top_k,
        top_p=llm_model_options.top_p,
        format=llm_model_options.format,
        keep_alive=llm_model_options.keep_alive,
        client_kwargs=llm_model_options.client_kwargs,
        async_client_kwargs=llm_model_options.async_client_kwargs,
        sync_client_kwargs=llm_model_options.sync_client_kwargs,
    )


def get_ollama_chat_model(name: str, llm_options: LLMOptions, llm_model_options: LLMModelOptions) -> ChatOllama:
    """Create and return an OllamaLLM client configured with the given LLM options and model settings.

    Args:
        llm_options (LLMOptions): The LLM options for configuration.
        llm_model_options (LLMModelOptions): The model settings for configuration.

    Returns:
        OllamaLLM: The configured OllamaLLM client.
    """
    return ChatOllama(
        name=name,
        verbose=llm_model_options.verbose or False,
        model=llm_model_options.model,
        base_url=llm_options.llm_host,
        reasoning=llm_model_options.reasoning,
        mirostat=llm_model_options.mirostat,
        mirostat_eta=llm_model_options.mirostat_eta,
        mirostat_tau=llm_model_options.mirostat_tau,
        num_ctx=llm_model_options.num_ctx,
        num_gpu=llm_model_options.num_gpu,
        num_thread=llm_model_options.num_thread,
        num_predict=llm_model_options.num_predict,
        repeat_last_n=llm_model_options.repeat_last_n,
        repeat_penalty=llm_model_options.repeat_penalty,
        temperature=llm_model_options.temperature,
        seed=llm_model_options.seed,
        stop=llm_model_options.stop,
        tfs_z=llm_model_options.tfs_z,
        top_k=llm_model_options.top_k,
        top_p=llm_model_options.top_p,
        format=llm_model_options.format,
        keep_alive=llm_model_options.keep_alive,
        client_kwargs=llm_model_options.client_kwargs,
        async_client_kwargs=llm_model_options.async_client_kwargs,
        sync_client_kwargs=llm_model_options.sync_client_kwargs,
    )
