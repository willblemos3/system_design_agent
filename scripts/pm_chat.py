"""
Terminal session with the PM agent for a system design exercise.

    python scripts/pm_chat.py --module 1                   # random exercise from module 1
    python scripts/pm_chat.py --module 2 --exercise zumi   # specific exercise
    python scripts/pm_chat.py --list                       # list modules and exercises

Runtime comes from providers.yaml. Reports are saved to reports/.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
os.chdir(_REPO_ROOT)  # providers.yaml and .env are resolved from the cwd

from src.applications.system_design import ExerciseRepository, run_console  # noqa: E402
from src.shared.config import load_env  # noqa: E402
from src.shared.exceptions import ExerciseNotFoundError, ProviderError  # noqa: E402
from src.shared.factory import build_pm_session  # noqa: E402
from src.shared.provider_config import load_provider_config  # noqa: E402


def _list_exercises() -> None:
    repo = ExerciseRepository()
    for module in repo.modules():
        for ex in repo.list(module):
            print(f"module {module}  {ex.path.stem:15s} {ex.title}")


async def _run(args: argparse.Namespace) -> None:
    session = build_pm_session(
        module=args.module,
        exercise=args.exercise,
        pm_name=args.pm_name,
        language=args.language,
    )
    runtime = load_provider_config().runtime.primary_entry()
    print(f"{session.exercise.title}  ·  runtime: {runtime.name} ({runtime.model})")
    await run_console(session)


def main() -> None:
    parser = argparse.ArgumentParser(description="Session with the PM agent for a system design exercise.")
    parser.add_argument("--module", "-m", help="Module number, e.g. 1 or module_1.")
    parser.add_argument("--exercise", "-e", default=None,
                        help="Exercise name (norva, 01_norva) or number. Omit for a random one.")
    parser.add_argument("--language", default=None, help="Language of the opening message. Default: English.")
    parser.add_argument("--pm-name", default=None, help="PM persona name. Default: Alex.")
    parser.add_argument("--list", action="store_true", help="List modules and exercises, then exit.")
    args = parser.parse_args()

    if args.list:
        _list_exercises()
        return
    if not args.module:
        parser.error("--module is required (or use --list)")

    load_env()
    try:
        asyncio.run(_run(args))
    except (ExerciseNotFoundError, EnvironmentError) as e:
        sys.exit(f"error: {e}")
    except ProviderError as e:
        sys.exit(f"error: {e}\n(is the runtime in providers.yaml reachable? for ollama: 'ollama list')")


if __name__ == "__main__":
    main()
