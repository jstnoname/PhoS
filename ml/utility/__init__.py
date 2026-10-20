from pathlib import Path

from dotenv import load_dotenv as ld


def find_dotenv() -> Path | str | None:
    path = Path().resolve()
    if path.is_file():
        path = path.parent

    while True:
        if (path / ".env").exists():
            return path / ".env"
        if (path / ".git").exists() or path == path.parent:
            return None
        path = path.parent


def load_dotenv() -> bool:
    env = find_dotenv()
    if env is None:
        raise FileNotFoundError("No .env file found")
    return ld(env)
