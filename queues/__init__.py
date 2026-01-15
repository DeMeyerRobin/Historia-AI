# queues/__init__.py
from .message_bus import task_queue, result_queue, ppt_queue

__all__ = ["task_queue", "result_queue", "ppt_queue"]