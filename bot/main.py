# bot/main.py
"""
MAIN BOT ENTRY POINT
====================
Discord bot that interfaces with the agentic history education system.

SYSTEM ARCHITECTURE:
1. REQUEST REVIEWER AGENT: Validates requests are history-related
2. PLANNER AGENT: Orchestrates lesson creation and coordinates other agents
3. WORKER AGENT: Executes research tasks (Wikipedia, fact-checking)
4. FACT-CHECKER AGENT: Validates content accuracy
5. PPT AGENT: Generates PowerPoint files

FLOW:
 User Request → Request Reviewer → Planner → Worker/Fact-Checker → PPT → User

GUARDRAILS:
- Only history-related requests are processed
- Non-history requests are rejected with helpful message
"""

import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import sys
from pathlib import Path

# Ensure the project root is on sys.path so our local queues package is imported
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import queues and agents
from queues.message_bus import task_queue, result_queue
from agents.planner_agent import planner_agent
from agents.ppt_agent import ppt_agent
from agents.request_reviewer_agent import review_request

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# -------------------------
# BOT READY
# -------------------------
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

    # Start agents in background
    if not getattr(bot, "agents_started", False):
        bot.agents_started = True
        bot.loop.create_task(planner_agent())
        bot.loop.create_task(ppt_agent())
        print("[Main] Planner + PPT agent started.")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print("Sync error:", e)


# -------------------------
# ROUTING FUNCTION
# -------------------------
async def route_task(task: str) -> str:
    """
    Sends a task into the task_queue and waits for the planner's final string result.
    Ignores non-string results (e.g., PPT agent dict messages) that may arrive on result_queue.
    """
    print(f"[Router] Routing task: {task}")
    await task_queue.put(task)

    while True:
        msg = await result_queue.get()
        result_queue.task_done()

        # Planner final output is a string
        if isinstance(msg, str):
            print("[Router] Got final result from planner.")
            return msg

        # Ignore PPT dict messages (planner will consume them internally)
        print(f"[Router] Skipping non-text result from queue: {type(msg).__name__}")



# -------------------------
# SLASH COMMAND
# -------------------------
def chunk_message(text: str, limit=1900):
    """
    Splits long output into chunks safe for Discord (under 2000 chars).
    """
    chunks = []
    while len(text) > limit:
        split_index = text.rfind("\n", 0, limit)
        if split_index == -1:
            split_index = limit
        chunks.append(text[:split_index])
        text = text[split_index:]
    chunks.append(text)
    return chunks

import re

def extract_files_from_response(text: str):
    """
    Extracts all __FILE__:path markers from the response text.
    Returns a list of file paths and the cleaned text.
    """
    file_paths = re.findall(r"__FILE__:([^\s]+)", text)
    cleaned_text = re.sub(r"__FILE__:[^\s]+", "", text).strip()
    return file_paths, cleaned_text


@bot.tree.command(name="task", description="Send a task to the agent system")
async def task_cmd(interaction: discord.Interaction, query: str):
    """
    Main command handler with request validation guardrail.
    Only history-related requests are processed.
    """
    await interaction.response.send_message("🔍 Reviewing your request...")

    # STEP 1: Request Review (Guardrail)
    review_result = await review_request(query)
    
    if not review_result["approved"]:
        # Request rejected - not history-related
        rejection_msg = review_result["message"]
        await interaction.followup.send(rejection_msg)
        return
    
    # STEP 2: Request approved - proceed with processing
    await interaction.followup.send("✅ Request validated - Processing your history task...")

    final_result = await route_task(query)

    file_paths, display_text = extract_files_from_response(final_result)

    chunks = chunk_message(display_text)

    # Send text output
    await interaction.followup.send(f"✅ **Result:**\n{chunks[0]}")
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk)

    # Send all generated files
    if file_paths:
        for file_path_str in file_paths:
            file_path = Path(file_path_str)
            if file_path.exists():
                await interaction.followup.send(
                    f"📄 **{file_path.name}**",
                    file=discord.File(str(file_path))
                )
            else:
                await interaction.followup.send(f"⚠️ File not found: `{file_path_str}`")




# -------------------------
# RUN BOT
# -------------------------
bot.run(TOKEN)
