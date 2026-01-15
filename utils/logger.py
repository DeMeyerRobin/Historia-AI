# utils/logger.py
import os


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


VERBOSE_LOGS = _is_truthy(os.getenv("AGENT_DEBUG_LOGS", "0"))


def log_debug(message: str) -> None:
    if VERBOSE_LOGS:
        print(message)