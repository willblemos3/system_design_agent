import os

from src.shared.provider_config import load_provider_config

# Local OpenAI-compatible servers (e.g. Ollama) ignore the key, but the client requires one.
_LOCAL_API_KEY = "local"


def build_runtime(instruction: str = "", memory_provider=None, user_id: str = "default_user", verbose: bool = True):
    cfg = load_provider_config()
    entry = cfg.runtime.primary_entry()
    if entry.class_name == "OpenAIRuntime":
        from src.runtime import OpenAIRuntime
        api_key = os.getenv(entry.requires) if entry.requires else _LOCAL_API_KEY
        if not api_key:
            raise EnvironmentError(f"{entry.requires} not set (runtime: {entry.name})")
        return OpenAIRuntime(
            model=entry.model,
            instruction=instruction,
            memory_provider=memory_provider,
            user_id=user_id,
            verbose=verbose,
            base_url=entry.base_url,
            api_key=api_key,
        )
    from src.runtime import ADKRuntime
    return ADKRuntime(
        model=entry.model,
        instruction=instruction,
        memory_provider=memory_provider,
        user_id=user_id,
        verbose=verbose,
    )


def build_pm_session(
    module: int | str,
    exercise: str | int | None = None,
    pm_name: str | None = None,
    language: str | None = None,
    verbose: bool = False,
):
    """
    PM agent for a system design exercise.

    exercise=None picks a random exercise from the module.
    Runtime comes from providers.yaml, like build_runtime().
    """
    from src.applications.system_design import ExerciseRepository, PMSession, build_pm_instruction
    from src.applications.system_design.prompt_builder import DEFAULT_LANGUAGE, DEFAULT_PM_NAME

    chosen = ExerciseRepository().get(module, exercise)
    pm_name = pm_name or DEFAULT_PM_NAME
    runtime = build_runtime(
        instruction=build_pm_instruction(chosen, pm_name=pm_name, language=language or DEFAULT_LANGUAGE),
        verbose=verbose,
    )
    return PMSession(runtime=runtime, exercise=chosen, pm_name=pm_name)


def build_llm_provider():
    cfg = load_provider_config()
    entry = cfg.llm.primary_entry()
    if entry.name == "openai":
        from src.foundation.llm import OpenAILLMProvider
        return OpenAILLMProvider(model=entry.model)
    from src.foundation.llm import GeminiLLMProvider
    return GeminiLLMProvider(model=entry.model)


def build_embedding_provider():
    cfg = load_provider_config()
    entry = cfg.embedding.primary_entry()
    if entry.name == "openai":
        from src.foundation.embeddings import OpenAIEmbeddingProvider
        return OpenAIEmbeddingProvider(model=entry.model)
    from src.foundation.embeddings import GeminiEmbeddingProvider
    return GeminiEmbeddingProvider(model=entry.model)
