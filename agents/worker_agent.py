# agents/worker_agent.py
from utils.llm import generate
from utils.tools import wikipedia_summary, lightweight_factcheck
import asyncio


def _run_tool(step: str) -> str:
    """
    Tool call format:
      TOOL:wikipedia:<query>
      TOOL:factcheck:<claim>|||<evidence>

    """
    try:
        _, tool_name, payload = step.split(":", 2)
        tool_name = tool_name.strip().lower()
        payload = payload.strip()

        if tool_name == "wikipedia":
            return wikipedia_summary(payload)

        if tool_name == "factcheck":
            if "|||" not in payload:
                return "factcheck tool format error. Use TOOL:factcheck:<claim>|||<evidence>"
            claim, evidence = payload.split("|||", 1)
            return lightweight_factcheck(claim.strip(), evidence.strip())

        return f"Unknown tool: {tool_name}"

    except ValueError:
        return "Tool parse error. Use TOOL:<name>:<payload>"


async def run_worker_step(step: str) -> str:
    """
    Worker Agent:
    - If step is a TOOL call -> run local python tool
    - Otherwise -> use LLM
    """

    print(f"[Worker] Starting step:\n{step}")

    # ✅ TOOL PATH
    normalized = step.replace("<", "").replace(">", "").strip()
    tool_index = normalized.upper().find("TOOL:")
    if tool_index != -1:
        normalized = normalized[tool_index:]  # cut off any prefix like "1) "
        result = _run_tool(normalized)
        print(f"[Worker] Tool result:\n{result}")
        await asyncio.sleep(0)
        return result

    # ✅ LLM PATH
    worker_prompt = f"""
Execute the following task step clearly and concisely:

Step: {step}

Return only the answer, no extra text.
"""
    result = generate(worker_prompt)

    print(f"[Worker] Result:\n{result}")
    await asyncio.sleep(0)
    return result
