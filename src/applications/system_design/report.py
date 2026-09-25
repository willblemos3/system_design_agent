import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.applications.system_design.documents import IMAGE_EXTENSIONS
from src.applications.system_design.exercise import Exercise


_DEFAULT_DIR = Path(__file__).resolve().parents[3] / "reports"
_NOT_SUBMITTED = "_Not submitted._"
_NOT_ANSWERED = "_Not answered._"


@dataclass
class SessionReport:
    exercise: Exercise
    solution: str | None
    tradeoff_answers: dict[int, str]   # question index → answer
    started_at: datetime
    finished_at: datetime
    solution_source: Path | None = None           # file in results/ the solution came from
    diagrams: list[Path] = field(default_factory=list)  # files in results/diagrams/

    def to_markdown(self, report_dir: Path | None = None) -> str:
        """report_dir: where the report will live, so diagram links resolve relative to it."""
        ex = self.exercise
        lines = [
            f"# System Design Report — {ex.company}",
            "",
            f"- **Exercise:** {ex.title} (`{ex.path.stem}`)",
            f"- **Module:** {ex.module_title}",
            f"- **Date:** {self.finished_at:%Y-%m-%d %H:%M}",
            f"- **Diagrams:** {len(self.diagrams)} file(s) in `results/diagrams/`" if self.diagrams
            else "- **Diagrams:** none",
            "",
            "---",
            "",
            "## 1. Problem",
            "",
            "### Context",
            "",
            ex.context,
            "",
            "### Data available",
            "",
            ex.data,
            "",
            "### Deliverable",
            "",
            ex.deliverable,
            "",
            "---",
            "",
            "## 2. Proposed solution",
            "",
        ]
        if self.solution_source:
            lines += [f"_Loaded from `results/{self.solution_source.name}`._", ""]
        lines += [
            self.solution or _NOT_SUBMITTED,
            "",
            "---",
            "",
            "## 3. Trade-offs",
            "",
        ]
        for i, question in enumerate(ex.tradeoffs):
            lines += [
                f"### Q{i + 1}. {question}",
                "",
                self.tradeoff_answers.get(i) or _NOT_ANSWERED,
                "",
            ]
        if self.diagrams:
            lines += ["---", "", "## 4. Diagrams", ""]
            lines += [f"The student provided {len(self.diagrams)} file(s) in `results/diagrams/`:", ""]
            for diagram in self.diagrams:
                link = _link(diagram, report_dir)
                if diagram.suffix.lower() in IMAGE_EXTENSIONS:
                    lines += [f"### {diagram.name}", "", f"![{diagram.name}]({link})", ""]
                else:
                    lines += [f"- [{diagram.name}]({link})"]
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def save(self, directory: str | Path | None = None) -> Path:
        directory = Path(directory) if directory else _DEFAULT_DIR
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.finished_at:%Y-%m-%d_%H%M}_module{self.exercise.module}_{self.exercise.path.stem}.md"
        path.write_text(self.to_markdown(report_dir=directory), encoding="utf-8")
        return path


def _link(target: Path, report_dir: Path | None) -> str:
    try:
        relative = os.path.relpath(target, report_dir) if report_dir else str(target)
    except ValueError:  # different drives on Windows
        relative = str(target)
    return Path(relative).as_posix().replace(" ", "%20")
