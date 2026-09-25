"""
Text interface for a PMSession — used by scripts/pm_chat.py.

Free text goes to the PM. Menu options (details, solution, trade-offs, report) are handled
here deterministically, without the LLM.
"""
import os
import re
import sys
import time
from pathlib import Path

from src.applications.system_design.documents import (
    RESULTS_DIR,
    SUPPORTED_EXTENSIONS,
    DocumentLoadError,
    list_diagrams,
    load_solution_file,
)
from src.applications.system_design.pm_session import PMSession


_RULE = "─" * 60
_PASTE_WAIT = 0.05  # seconds to let the rest of a paste reach the input buffer
_PREVIEW_LINES = 15
# A lone "name.ext" line is treated as a file in results/ — these extensions get a clear "unsupported" error.
_FILENAME = re.compile(r"[^\\/:*?\"<>|\n]+\.[A-Za-z0-9]{2,5}")
_OTHER_FILE_EXTENSIONS = (".pdf", ".rtf", ".odt", ".pages", ".ppt", ".pptx", ".xls", ".xlsx", ".csv", ".png", ".jpg", ".jpeg")


def _menu(pm_name: str) -> str:
    return f"""
{_RULE}
What would you like to do?
  1. Ask a question        talk to {pm_name} about the business
  2. See the details       data available and deliverables
  3. Submit your solution  record your proposed architecture
  4. Trade-off questions   answer questions about your design
  5. Finish                save the report and end
Type a number, or just type your question.
{_RULE}"""


def _plain(markdown: str) -> str:
    """Strips markdown emphasis and escapes for terminal display."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", markdown)
    return text.replace("\\_", "_").replace("`", "")


def _pasting() -> bool:
    """True when more pasted text is already waiting in the terminal (so a blank line is part of the paste)."""
    time.sleep(_PASTE_WAIT)
    try:
        if os.name == "nt":
            import msvcrt
            return msvcrt.kbhit()
        import select
        return bool(select.select([sys.stdin], [], [], 0)[0])
    except Exception:  # no real terminal (e.g. notebooks)
        return False


def _read_text(instruction: str | None, lines: list[str] | None = None) -> str:
    """Multi-line input: Enter on an empty line submits. Returns '' if nothing was typed."""
    if instruction:
        print(f"\n{instruction}")
    lines = list(lines or [])
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        if not line.strip():
            if not lines or not _pasting():
                break
        lines.append(line)
    return "\n".join(lines).strip()


def _confirm(question: str, default: bool = False) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"{question} {hint} ").strip().lower()
    except EOFError:
        return default
    return default if not answer else answer in ("y", "yes", "s", "sim")


async def _say(session: PMSession, message: str | None) -> None:
    print(f"\n{session.pm_name}: ", end="", flush=True)
    async for chunk in session.stream(message):
        print(chunk, end="", flush=True)
    print()


def _show_details(session: PMSession) -> None:
    ex = session.exercise
    print(f"\n{session.pm_name}: Sure, here's what we have and what we need from you.\n")
    print("DATA AVAILABLE\n")
    print(_plain(ex.data))
    print("\nWHAT WE NEED FROM YOU\n")
    print(_plain(ex.deliverable))
    print("\nIf anything's unclear, just ask.")


def _looks_like_filename(line: str) -> bool:
    name = line.strip().strip('"').strip("'")
    if len(name) > 120 or not _FILENAME.fullmatch(name):
        return False
    return Path(name).suffix.lower() in SUPPORTED_EXTENSIONS + _OTHER_FILE_EXTENSIONS or (RESULTS_DIR / name).exists()


def _preview(text: str) -> str:
    lines = text.splitlines()
    if len(lines) <= _PREVIEW_LINES:
        return text
    return "\n".join(lines[:_PREVIEW_LINES]) + f"\n… (+{len(lines) - _PREVIEW_LINES} more lines)"


def _submit_solution(session: PMSession) -> bool:
    if session.solution and not _confirm("\nYou already submitted a solution. Replace it?"):
        return False

    print(
        f"\n{session.pm_name}: Great, go ahead and describe your solution. You can write it here "
        "(several lines, or paste it),\nor, if it's saved in the results/ folder, just type the file name "
        f"with its extension, e.g. solution.docx ({', '.join(SUPPORTED_EXTENSIONS)}).\n"
        "When you're done writing, press Enter on an empty line to send it."
    )
    source = None
    while True:
        try:
            first = input("> ")
        except EOFError:
            first = ""
        if not first.strip():
            print("Nothing recorded.")
            return False
        if not _looks_like_filename(first):
            text = _read_text(None, lines=[first])
            break
        try:
            source, text = load_solution_file(first)
        except DocumentLoadError as e:
            print(f"\n{session.pm_name}: I couldn't load that file. {e}")
            print("Type the file name again, or write your solution here (empty line to cancel).")
            continue
        print(f"\n{session.pm_name}: Loaded {source.name} from results/ ({len(text.split())} words).")
        break

    print(f"\n{_RULE}\n{_preview(text) if source else text}\n{_RULE}")
    if not _confirm(f"Record this as your final solution? ({len(text.split())} words)", default=True):
        print("Not recorded.")
        return False
    session.submit_solution(text, source=source)
    print(f"\n{session.pm_name}: Got it, your solution is recorded.")
    return True


def _answer_tradeoffs(session: PMSession) -> None:
    questions = session.exercise.tradeoffs
    if not questions:
        print("\nThis exercise has no trade-off questions.")
        return
    print(
        f"\n{session.pm_name}: I have {len(questions)} questions about your architecture. "
        "I'll just record your answers, no debate here.\n"
        "Press Enter on an empty line to send each answer (or right away to skip the question)."
    )
    answered = session.tradeoff_answers
    for i, question in enumerate(questions):
        if i in answered and not _confirm(
            f"\nQ{i + 1}/{len(questions)}. {_plain(question)}\nYou already answered this one. Replace your answer?"
        ):
            continue
        text = _read_text(f"Q{i + 1}/{len(questions)}. {_plain(question)}")
        if text:
            session.answer_tradeoff(i, text)
            print("Recorded.")
        else:
            print("Skipped.")


def _save(session: PMSession, reports_dir: str | Path | None) -> Path:
    report = session.report()
    path = report.save(reports_dir)
    if report.diagrams:
        names = ", ".join(d.name for d in report.diagrams)
        print(f"\nDiagrams found in results/diagrams/ and included in the report: {names}")
    print(f"\nReport saved to: {path}")
    return path


def _check_diagrams(session: PMSession) -> None:
    """When the deliverable asks for a diagram, give the student a chance to drop it in results/diagrams/."""
    while "diagram" in session.exercise.deliverable.lower() and not list_diagrams():
        if _confirm(
            f"\n{session.pm_name}: We asked for a diagram, but results/diagrams/ is empty. "
            "Continue without it? (Answer 'n' after adding the file to check again.)", default=True
        ):
            return


def _finish(session: PMSession, reports_dir: str | Path | None) -> None:
    if session.solution is None and _confirm(
        f"\n{session.pm_name}: You haven't submitted a solution yet. Would you like to do it now?", default=True
    ):
        _submit_solution(session)

    pending = session.unanswered_tradeoffs()
    if pending and _confirm(
        f"\n{session.pm_name}: Before we wrap up, would you like to answer "
        f"{len(pending)} question{'s' if len(pending) > 1 else ''} about your architecture?", default=True
    ):
        _answer_tradeoffs(session)

    _check_diagrams(session)
    _save(session, reports_dir)
    print(f"\n{session.pm_name}: Thanks for your time. Good luck!")


async def run_console(session: PMSession, reports_dir: str | Path | None = None) -> None:
    """Runs the full session: opening, menu loop, report."""
    await _say(session, None)
    print(_menu(session.pm_name))

    while True:
        try:
            user_input = input("\nYou (m = menu): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            if session.has_progress():
                _save(session, reports_dir)
            return

        if not user_input:
            continue
        command = user_input.lower()

        if command in ("m", "menu"):
            print(_menu(session.pm_name))
        elif command == "1":
            print(f"\n{session.pm_name}: Go ahead, what would you like to know?")
        elif command == "2":
            _show_details(session)
        elif command == "3":
            if _submit_solution(session) and session.unanswered_tradeoffs() and _confirm(
                f"\n{session.pm_name}: Are you done? Would you like to answer "
                "a few questions about your architecture now?", default=True
            ):
                _answer_tradeoffs(session)
                print(_menu(session.pm_name))
        elif command == "4":
            _answer_tradeoffs(session)
            print(_menu(session.pm_name))
        elif command in ("5", "finish"):
            _finish(session, reports_dir)
            return
        elif command in ("exit", "quit", "sair"):
            if session.has_progress():
                _save(session, reports_dir)
            return
        else:
            await _say(session, user_input)
