import asyncio

# Primary queue for planner-bound user tasks
task_queue = asyncio.Queue()

# Dedicated queue for PPT generation jobs so they are never swallowed by the planner
ppt_queue = asyncio.Queue()

result_queue = asyncio.Queue()