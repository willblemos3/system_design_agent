import random
import re
from dataclasses import dataclass
from pathlib import Path

from src.shared.exceptions import ExerciseNotFoundError


# docs/system_design/module_<n>/<nn>_<slug>.md — resolved from the repo root, not the cwd
_DEFAULT_ROOT = Path(__file__).resolve().parents[3] / "docs" / "system_design"
_MODULE_DIR = re.compile(r"^module_(\d+)$")
_EXERCISE_FILE = re.compile(r"^(\d+)_(.+)\.md$")
# Everything from this heading on is private context for the agent, never shown to the student.
_INSTRUCTOR_NOTES = re.compile(r"^#+\s*\**\s*instructor notes.*$", re.IGNORECASE | re.MULTILINE)
# "## **Context**" — level-2+ headings split the brief into sections (some are indented in the source files).
_SECTION = re.compile(r"^[ \t]*#{2,}[ \t]*(.+?)[ \t]*$", re.MULTILINE)
_NUMBERED_ITEM = re.compile(r"^\s*\d+\.\s+(.+)$", re.MULTILINE)


@dataclass
class Exercise:
    module: int
    number: int
    slug: str
    title: str             # "System Design Exercise 1 — NORVA"
    company: str           # "NORVA"
    module_title: str      # "Module 1 — Recommender System Introduction and Evaluation Metrics"
    brief: str             # full student-facing markdown
    context: str           # "Context" section — company situation and the business request
    data: str              # "Data available" section
    deliverable: str       # "Deliverable" section
    tradeoffs: list[str]   # "Trade-offs to defend" questions, one per item
    instructor_notes: str | None
    path: Path


class ExerciseRepository:

    def __init__(self, root: str | Path | None = None) -> None:
        self._root = Path(root) if root else _DEFAULT_ROOT
        if not self._root.is_dir():
            raise ExerciseNotFoundError(f"Exercise root not found: {self._root}")

    def modules(self) -> list[int]:
        return sorted(
            int(m.group(1))
            for d in self._root.iterdir()
            if d.is_dir() and (m := _MODULE_DIR.match(d.name))
        )

    def list(self, module: int | str) -> list[Exercise]:
        module_dir = self._root / f"module_{_parse_module(module)}"
        if not module_dir.is_dir():
            raise ExerciseNotFoundError(
                f"Module {module} not found. Available modules: {self.modules()}"
            )
        return [
            _load(path, _parse_module(module))
            for path in sorted(module_dir.glob("*.md"))
            if _EXERCISE_FILE.match(path.name)
        ]

    def get(
        self,
        module: int | str,
        exercise: str | int | None = None,
        rng: random.Random | None = None,
    ) -> Exercise:
        """
        Returns one exercise from the module.

        exercise=None picks one at random. Otherwise it matches by slug ("norva"),
        file stem ("01_norva") or number (1).
        """
        exercises = self.list(module)
        if not exercises:
            raise ExerciseNotFoundError(f"Module {module} has no exercises.")

        if exercise is None:
            return (rng or random).choice(exercises)

        key = str(exercise).strip().lower().removesuffix(".md")
        for ex in exercises:
            if key in (ex.slug, ex.path.stem, str(ex.number), f"{ex.number:02d}"):
                return ex

        available = [ex.path.stem for ex in exercises]
        raise ExerciseNotFoundError(
            f"Exercise '{exercise}' not found in module {module}. Available: {available}"
        )


def _parse_module(module: int | str) -> int:
    text = str(module).strip().lower().removeprefix("module_").removeprefix("module")
    try:
        return int(text)
    except ValueError:
        raise ExerciseNotFoundError(f"Invalid module: {module!r}") from None


def _load(path: Path, module: int) -> Exercise:
    match = _EXERCISE_FILE.match(path.name)
    text = path.read_text(encoding="utf-8")

    notes_match = _INSTRUCTOR_NOTES.search(text)
    if notes_match:
        brief = text[:notes_match.start()]
        instructor_notes = text[notes_match.end():].strip() or None
    else:
        brief, instructor_notes = text, None

    title = _first_line(brief, lambda line: line.startswith("#"))
    module_title = _first_line(brief, lambda line: line.strip("*").lower().startswith("module"))
    sections = _sections(brief)

    return Exercise(
        module=module,
        number=int(match.group(1)),
        slug=match.group(2).lower(),
        title=title,
        company=title.split("—")[-1].strip() if "—" in title else match.group(2).upper(),
        module_title=module_title,
        brief=_strip_trailing_rule(brief),
        context=sections.get("context", ""),
        data=sections.get("data available", ""),
        deliverable=sections.get("deliverable", ""),
        tradeoffs=[q.strip() for q in _NUMBERED_ITEM.findall(sections.get("trade-offs to defend", ""))],
        instructor_notes=instructor_notes,
        path=path,
    )


def _sections(text: str) -> dict[str, str]:
    """Maps each level-2+ heading (lowercased, without markdown emphasis) to its body."""
    headings = list(_SECTION.finditer(text))
    sections = {}
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        name = heading.group(1).strip("*").strip().lower()
        sections[name] = _strip_trailing_rule(text[heading.end():end]).strip()
    return sections


def _first_line(text: str, predicate) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line and predicate(line):
            return line.lstrip("#").strip().strip("*").strip()
    return ""


def _strip_trailing_rule(text: str) -> str:
    text = text.rstrip()
    while text.endswith("---"):
        text = text[:-3].rstrip()
    return text
