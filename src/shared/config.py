import os


def load_env() -> None:
    from dotenv import load_dotenv
    load_dotenv()


def get_api_key(provider: str) -> str:
    key = os.getenv(f"{provider.upper()}_API_KEY")
    if not key:
        raise EnvironmentError(f"{provider.upper()}_API_KEY not set")
    return key
