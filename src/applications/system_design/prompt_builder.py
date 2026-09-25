from pathlib import Path
from string import Template

from src.applications.system_design.exercise import Exercise


_TEMPLATE_PATH = Path(__file__).parent / "prompts" / "pm_system_prompt.md"
_NO_NOTES = "None for this exercise."

DEFAULT_PM_NAME = "Alex"
DEFAULT_LANGUAGE = "English"


def build_pm_instruction(
    exercise: Exercise,
    pm_name: str = DEFAULT_PM_NAME,
    language: str = DEFAULT_LANGUAGE,
) -> str:
    """Renders the PM system prompt (CO-STAR) for one exercise."""
    template = Template(_TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.substitute(
        exercise_brief=_pm_brief(exercise),
        instructor_notes=exercise.instructor_notes or _NO_NOTES,
        module_title=exercise.module_title,
        company=exercise.company,
        pm_name=pm_name,
        language=language,
    )


def _pm_brief(exercise: Exercise) -> str:
    # The trade-off questions are left out on purpose: the PM cannot leak what it does not know.
    return "\n\n".join([
        f"# {exercise.title}",
        f"## Context\n\n{exercise.context}",
        f"## Data available\n\n{exercise.data}",
        f"## Deliverable\n\n{exercise.deliverable}",
    ])
