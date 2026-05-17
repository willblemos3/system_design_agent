from src.shared.provider_config import load_provider_config


def build_runtime(instruction: str = "", memory_provider=None, user_id: str = "default_user", verbose: bool = True):
    cfg = load_provider_config()
    entry = cfg.runtime.primary_entry()
    if entry.name == "openai":
        from src.runtime import OpenAIRuntime
        return OpenAIRuntime(
            model=entry.model,
            instruction=instruction,
            memory_provider=memory_provider,
            user_id=user_id,
            verbose=verbose,
        )
    from src.runtime import ADKRuntime
    return ADKRuntime(
        model=entry.model,
        instruction=instruction,
        memory_provider=memory_provider,
        user_id=user_id,
        verbose=verbose,
    )


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


def build_resume_parser():
    from src.applications.parsing.resume_parser import ResumeParser
    return ResumeParser(llm_provider=build_llm_provider())
