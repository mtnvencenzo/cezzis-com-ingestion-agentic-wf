from dataclasses import dataclass, field

from typing_extensions import Literal


@dataclass
class LLMModelOptions:
    """
    Options for configuring LLM model run-time behavior and settings.
    """

    model: str
    """Model name to use."""

    timeout_seconds: int | None = 30
    """Timeout for requests to the model."""

    verbose: bool | None = None
    """Whether to enable verbose logging."""

    reasoning: bool | None = None
    """Controls the reasoning/thinking mode for
    [supported models](https://ollama.com/search?c=thinking).

    - `True`: Enables reasoning mode. The model's reasoning process will be
        captured and returned separately in the `additional_kwargs` of the
        response message, under `reasoning_content`. The main response
        content will not include the reasoning tags.
    - `False`: Disables reasoning mode. The model will not perform any reasoning,
        and the response will not include any reasoning content.
    - `None` (Default): The model will use its default reasoning behavior. If
        the model performs reasoning, the `<think>` and `</think>` tags will
        be present directly within the main response content."""

    mirostat: int | None = None
    """Enable Mirostat sampling for controlling perplexity.
    (default: `0`, `0` = disabled, `1` = Mirostat, `2` = Mirostat 2.0)"""

    mirostat_eta: float | None = None
    """Influences how quickly the algorithm responds to feedback
    from the generated text. A lower learning rate will result in
    slower adjustments, while a higher learning rate will make
    the algorithm more responsive. (Default: `0.1`)"""

    mirostat_tau: float | None = None
    """Controls the balance between coherence and diversity
    of the output. A lower value will result in more focused and
    coherent text. (Default: `5.0`)"""

    num_ctx: int | None = None
    """Sets the size of the context window used to generate the
    next token. (Default: `2048`)"""

    num_gpu: int | None = None
    """The number of GPUs to use. On macOS it defaults to `1` to
    enable metal support, `0` to disable."""

    num_thread: int | None = None
    """Sets the number of threads to use during computation.
    By default, the llm models default detection will be used. It is recommended to set this 
    value to the number of physical CPU cores your system has 
    (as opposed to the logical number of cores)."""

    num_predict: int | None = None
    """Maximum number of tokens to predict when generating text.
    (Default: `128`, `-1` = infinite generation, `-2` = fill context)"""

    repeat_last_n: int | None = None
    """Sets how far back for the model to look back to prevent
    repetition. (Default: `64`, `0` = disabled, `-1` = `num_ctx`)"""

    repeat_penalty: float | None = None
    """Sets how strongly to penalize repetitions. A higher value (e.g., `1.5`)
    will penalize repetitions more strongly, while a lower value (e.g., `0.9`)
    will be more lenient. (Default: `1.1`)"""

    temperature: float | None = None
    """The temperature of the model. Increasing the temperature will
    make the model answer more creatively. (Default: `0.8`)"""

    seed: int | None = None
    """Sets the random number seed to use for generation. Setting this
    to a specific number will make the model generate the same text for
    the same prompt."""

    stop: list[str] | None = None
    """Sets the stop tokens to use."""

    tfs_z: float | None = None
    """Tail free sampling is used to reduce the impact of less probable
    tokens from the output. A higher value (e.g., `2.0`) will reduce the
    impact more, while a value of 1.0 disables this setting. (default: `1`)"""

    top_k: int | None = None
    """Reduces the probability of generating nonsense. A higher value (e.g. `100`)
    will give more diverse answers, while a lower value (e.g. `10`)
    will be more conservative. (Default: `40`)"""

    top_p: float | None = None
    """Works together with top-k. A higher value (e.g., `0.95`) will lead
    to more diverse text, while a lower value (e.g., `0.5`) will
    generate more focused and conservative text. (Default: `0.9`)"""

    format: Literal["", "json"] = ""
    """Specify the format of the output (options: `'json'`)"""

    keep_alive: int | str | None = None
    """How long the model will stay loaded into memory."""

    client_kwargs: dict = field(default_factory=dict)
    """Additional kwargs to pass to the httpx clients. Pass headers in here.

    These arguments are passed to both synchronous and async clients.

    Use `sync_client_kwargs` and `async_client_kwargs` to pass different arguments
    to synchronous and asynchronous clients.
    """

    async_client_kwargs: dict = field(default_factory=dict)
    """Additional kwargs to merge with `client_kwargs` before passing to httpx client.

    These are clients unique to the async client; for shared args use `client_kwargs`.

    For a full list of the params, see the [httpx documentation](https://www.python-httpx.org/api/#asyncclient).
    """

    sync_client_kwargs: dict = field(default_factory=dict)
    """Additional kwargs to merge with `client_kwargs` before passing to httpx client.

    These are clients unique to the sync client; for shared args use `client_kwargs`.

    For a full list of the params, see the [httpx documentation](https://www.python-httpx.org/api/#client).
    """
