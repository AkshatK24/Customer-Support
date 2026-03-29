"""Tasks package exports."""
from .task_easy import TASK_EASY_CONFIG
from .task_medium import TASK_MEDIUM_CONFIG
from .task_hard import TASK_HARD_CONFIG

TASK_REGISTRY: dict = {
    "easy": TASK_EASY_CONFIG,
    "medium": TASK_MEDIUM_CONFIG,
    "hard": TASK_HARD_CONFIG,
}

__all__ = ["TASK_EASY_CONFIG", "TASK_MEDIUM_CONFIG", "TASK_HARD_CONFIG", "TASK_REGISTRY"]
