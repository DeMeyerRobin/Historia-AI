# agents/planner_agent.py
"""
PLANNER AGENT
=============
RESPONSIBILITY: Orchestrates the creation of comprehensive history lesson packages.

PURPOSE:
- Plans multi-lesson units on historical topics
- Coordinates research, content generation, and file creation
- Manages Worker, Fact-Checker, and PPT agents
- Produces Teacher Guides (DOCX) and PowerPoint presentations

FLOW:
1. Receives validated history request from request_reviewer
2. Creates lesson plan structure
3. Coordinates research via Worker agent (Wikipedia)
4. Generates detailed Teacher's Guide content
5. Creates PowerPoint slide structures
6. Dispatches to PPT agent for file generation
7. Returns file paths to user

GUARDRAILS:
- Assumes all requests are pre-validated as history-related
- Focuses strictly on historical education content
- Uses evidence-based content generation
"""

import asyncio
import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List

try:
    import docx
except ImportError:
    docx = None

from queues.message_bus import task_queue, result_queue, ppt_queue
from utils.llm import generate
from agents.worker_agent import run_worker_step as worker_agent
from agents.fact_checker_agent import fact_checker_agent


OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Config
SLIDE_TARGET = 30
MAX_WIKI_TOPICS = 5 


def _slugify_title(title: str) -> str:
    """Return a filesystem-safe slug derived from the desired PPT title."""
    safe_text = (title or "presentation").encode("ascii", errors="ignore").decode()
    safe_text = re.sub(r"[^A-Za-z0-9]+", "-", safe_text).strip("-") or "presentation"
    return safe_text[:60].lower()


def build_ppt_filename(title: str) -> str:
    """Create a unique PPT filename."""
    base_slug = _slugify_title(title)
    candidate = base_slug
    counter = 1
    while (OUTPUT_DIR / f"{candidate}.pptx").exists():
        candidate = f"{base_slug}-{counter}"
        counter += 1
    return f"{candidate}.pptx"


def _safe_json_loads(raw: str) -> Dict[str, Any]:
    if not raw:
        return {}
    raw = raw.strip()
    match = re.search(r"```json\s*(.*?)\s*```", raw, flags=re.DOTALL)
    if match:
        raw = match.group(1)
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {}

# -------------------------------------------------------------------------
#  DOCX HELPER
# -------------------------------------------------------------------------
def create_docx(filename: str, title: str, summary_text: str):
    """Creates a Word document with continuous flowing text."""
    if not docx:
        print("[Planner] python-docx not installed, skipping DOCX generation.")
        return False
        
    try:
        doc = docx.Document()
        doc.add_heading(title, 0)
        
        # Add the summary as continuous text, preserving paragraph breaks
        paragraphs = summary_text.split('\n\n')
        for para_text in paragraphs:
            para_text = para_text.strip()
            if para_text:
                # Remove any markdown formatting for cleaner continuous text
                para_text = para_text.replace('**', '').replace('##', '').replace('#', '')
                doc.add_paragraph(para_text)
        
        out_path = OUTPUT_DIR / filename
        doc.save(out_path)
        return True
    except Exception as e:
        print(f"[Planner] Error writing DOCX: {e}")
        return False

# -------------------------------------------------------------------------
#  PROMPTS
# -------------------------------------------------------------------------

def _plan_lessons_prompt(topic: str, num_lessons: int) -> str:
    return f"""
You are an expert history teacher creating educational content.

**CRITICAL REQUIREMENT: This is a HISTORY education system.**
You must create a comprehensive {num_lessons}-lesson unit plan on: "{topic}".

Return STRICT JSON matching this schema:
{{
  "unit_title": "Title of the whole unit",
  "lessons": [
    {{
      "lesson_number": 1,
      "title": "Concrete Topic Name",
      "topics_to_research_on_wikipedia": ["Topic 1", "Topic 2"] 
    }}
  ]
}}

MANDATORY Requirements:
- EXACTLY {num_lessons} lessons
- HISTORY-FOCUSED: All lessons must cover historical events, periods, figures, or movements
- Lesson titles must be CONCRETE and FACTUAL (e.g. "The Storming of the Bastille", not "A Dream of Liberty")
- Number the lessons sequentially
- Topics must be suitable for Wikipedia research on historical subjects
- Maintain academic rigor appropriate for history education
""".strip()


def _teacher_summary_prompt(lesson_title: str, evidence: str, previous_content: str = "") -> str:
    previous_context = ""
    if previous_content:
        previous_context = f"""
CONTEXT FROM PREVIOUS LESSONS:
{previous_content}

CRITICAL: The above content was already covered in previous lessons. 
DO NOT repeat these topics, facts, or concepts. Build upon them and introduce NEW information.
Reference previous lessons briefly if needed for continuity, but focus on ORIGINAL content.

"""
    
    return f"""
**SYSTEM GUARDRAIL: HISTORY EDUCATION ONLY**
You are an expert HISTORY teacher writing a comprehensive "Teacher's Guide" for: "{lesson_title}".

This guide will be saved as a Word document and accompanies a 30-slide PowerPoint presentation.
The guide must contain ALL the detailed knowledge the teacher needs, written as CONTINUOUS FLOWING TEXT.

{previous_context}IMPORTANT STRUCTURAL REQUIREMENTS:
1. Write in continuous paragraphs (NOT bullet points or lists)
2. Organize content into EXACTLY 30 logical sections (one per slide)
3. Each section should be 3-5 sentences that expand on one key concept
4. Start each section with a clear topic sentence that could serve as a slide title
5. Use academic, clear language - NO poetic or "dreamy" phrasing
6. Ensure all content is NEW and does not repeat what was covered before

**HISTORY GUARDRAILS:**
- Focus EXCLUSIVELY on historical facts, events, and analysis
- Base all content on the provided evidence from historical sources
- Maintain chronological accuracy and historical context
- Use proper historical terminology and period-appropriate references
- Cite specific dates, figures, and locations where relevant

Format:
[Section 1 topic]
[3-5 sentences of detailed explanation]

[Section 2 topic]
[3-5 sentences of detailed explanation]

... continue for 30 sections total

EVIDENCE:
{evidence}
""".strip()


def _slide_generation_prompt(lesson_title: str, teacher_summary: str, target_slide_count: int, previous_slide_titles: List[str] = None) -> str:
    previous_context = ""
    if previous_slide_titles:
        previous_context = f"""
SLIDE TITLES FROM PREVIOUS LESSONS:
{chr(10).join(f'- {title}' for title in previous_slide_titles)}

CRITICAL: Avoid creating slides with similar titles or covering the same topics.
Your slides must introduce NEW concepts and information.

"""
    
    return f"""
You are an instructional designer. Create a PowerPoint structure for: "{lesson_title}".
Target length: EXACTLY {target_slide_count} slides.

The Teacher's Guide is organized into {target_slide_count} sections. Create ONE SLIDE PER SECTION.

{previous_context}Return STRICT JSON:
{{
  "slides": [
    {{
      "title": "Slide Title",
      "bullets": ["Keyword 1", "Keyword 2", "Short phrase"]
    }}
  ]
}}

MANDATORY RULES:
1. Extract the topic sentence from each section as the slide title
2. Convert key facts from each section into 2-4 bullets
3. Bullets MUST be keywords, dates, names, or short phrases (<= 6 words)
4. NO complete sentences in bullets
5. Maintain the EXACT order of sections from the guide
6. Slide titles must be concrete and factual (e.g., "Economic Crisis 1789")
7. You MUST generate EXACTLY {target_slide_count} slides - no more, no less
8. Ensure content is unique and does not duplicate previous lessons

**HISTORY EDUCATION REQUIREMENTS:**
- All slide content must be historically accurate and factual
- Include specific dates, names, and locations in bullets
- Focus on cause-effect relationships and historical significance
- Maintain educational value appropriate for history teaching

TEACHER'S GUIDE:
{teacher_summary}
""".strip()


# -------------------------------------------------------------------------
#  WORKFLOW STEPS
# -------------------------------------------------------------------------

async def _gather_evidence(topics: List[str], evidence_cache: Dict[str, str]) -> str:
    """
    Gathers evidence for topics, using cache to avoid duplicate research.
    Updates the evidence_cache with newly researched topics.
    """
    evidence_parts = []
    unique_topics = []
    seen = set()
    for t in topics:
        clean = t.strip()
        if clean.lower() not in seen:
            seen.add(clean.lower())
            unique_topics.append(clean)
    
    unique_topics = unique_topics[:MAX_WIKI_TOPICS]

    for topic in unique_topics:
        # Check cache first
        cache_key = topic.lower()
        if cache_key in evidence_cache:
            print(f"[Planner] Using cached evidence for: {topic}")
            evidence_parts.append(f"--- article: {topic} (cached) ---\n{evidence_cache[cache_key]}\n")
            continue
            
        # Research if not cached
        print(f"[Planner] Researching: {topic}")
        step_cmd = f"TOOL:wikipedia:{topic}"
        result = await worker_agent(step_cmd)
        
        # Store in cache
        evidence_cache[cache_key] = result
        evidence_parts.append(f"--- article: {topic} ---\n{result}\n")
    
    return "\n".join(evidence_parts)


async def _process_lesson(lesson_info: Dict[str, Any], unit_title: str, shared_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles end-to-end generation for a single lesson.
    Uses shared_context to avoid repetition across lessons.
    Returns a dict with lesson details and file paths.
    """
    l_num = lesson_info.get("lesson_number", "?")
    l_title = lesson_info.get("title", "Untitled")
    topics = lesson_info.get("topics_to_research_on_wikipedia", [])
    
    # Concrete naming: "Lesson 1 - Topic Name"
    full_lesson_name = f"Lesson {l_num} - {l_title}"
    print(f"\n[Planner] Processing {full_lesson_name}...")

    # 1. Research (using shared evidence cache)
    evidence = await _gather_evidence(topics, shared_context["evidence_cache"])
    if not evidence.strip():
        evidence = "No specific evidence found."

    # 2. Write Teacher Summary (The Real Knowledge) - with context from previous lessons
    print(f"[Planner] Writing Teacher Guide for {full_lesson_name}...")
    previous_summaries = "\n\n---PREVIOUS LESSON---\n\n".join(shared_context["lesson_summaries"])
    summary = generate(
        _teacher_summary_prompt(full_lesson_name, evidence, previous_summaries), 
        max_tokens=2000
    )
    
    # Add to shared context (keep last 2 lessons to avoid token overflow)
    shared_context["lesson_summaries"].append(f"{full_lesson_name}:\n{summary[:1000]}...")
    if len(shared_context["lesson_summaries"]) > 2:
        shared_context["lesson_summaries"].pop(0)
    
    # 3. Create DOCX for Summary
    docx_filename = f"{_slugify_title(full_lesson_name)}.docx"
    docx_created = create_docx(docx_filename, full_lesson_name, summary)
    docx_path = OUTPUT_DIR / docx_filename if docx_created else None

    # 4. Generate Slide Structure (Keywords only) - with context from previous slides
    print(f"[Planner] Designing slides for {full_lesson_name}...")
    slides_json_str = generate(
        _slide_generation_prompt(
            full_lesson_name, 
            summary, 
            SLIDE_TARGET,
            shared_context["slide_titles"]
        ),
        max_tokens=2500,  
        temperature=0.3
    )
    slides_data = _safe_json_loads(slides_json_str)
    slides_list = slides_data.get("slides", [])

    if not slides_list:
        slides_list = [{"title": "Error generating slides", "bullets": ["Check logs."]}]
    
    # Track slide titles
    for slide in slides_list:
        shared_context["slide_titles"].append(slide.get("title", ""))

    # 5. Dispatch to PPT Agent
    ppt_filename = build_ppt_filename(full_lesson_name)
    ppt_task_id = str(uuid.uuid4())
    
    await ppt_queue.put({
        "id": ppt_task_id,
        "to": "ppt",
        "payload": {
            "title": full_lesson_name,
            "slides": slides_list, 
            "filename": ppt_filename
        }
    })

    ppt_path = OUTPUT_DIR / ppt_filename
    ppt_ready = False
    for _ in range(60): 
        if ppt_path.exists():
            ppt_ready = True
            break
        await asyncio.sleep(0.5)
    
    return {
        "lesson_name": full_lesson_name,
        "topics": topics,
        "ppt_path": str(ppt_path) if ppt_ready else None,
        "docx_path": str(docx_path) if docx_path else None
    }


# -------------------------------------------------------------------------
#  MAIN PLANNER LOGIC
# -------------------------------------------------------------------------

async def _orchestrate_history_package(request: str):
    
    # 1. Parsing
    intent_prompt = f"""
Extract topic and number of lessons from: "{request}".
Return JSON: {{"topic": "...", "num_lessons": 3}}
Default num_lessons to 1 if not specified.
""".strip()
    
    intent_raw = generate(intent_prompt)
    intent = _safe_json_loads(intent_raw)
    topic = intent.get("topic", request)
    try:
        num_lessons = int(intent.get("num_lessons", 1))
    except:
        num_lessons = 1
        
    print(f"[Planner] Plan: {num_lessons} lessons on '{topic}'")

    # 2. Planning
    plan_raw = generate(_plan_lessons_prompt(topic, num_lessons))
    unit_plan = _safe_json_loads(plan_raw)
    
    unit_title = unit_plan.get("unit_title", topic)
    lessons = unit_plan.get("lessons", [])

    if not lessons:
        return "❌ Failed to generate a valid lesson plan."

    # 3. Build a readable plan summary
    plan_summary = f"**Unit:** {unit_title}\n**Lessons:**\n"
    for lesson in lessons:
        l_num = lesson.get("lesson_number", "?")
        l_title = lesson.get("title", "Untitled")
        plan_summary += f"  {l_num}. {l_title}\n"

    # 4. Initialize shared context to track what's been covered
    shared_context = {
        "evidence_cache": {},  # Cache Wikipedia results
        "lesson_summaries": [],  # Track previous lesson content
        "slide_titles": []  # Track all slide titles to avoid duplicates
    }

    # 5. Execute Lessons with shared context
    lesson_results = []
    for lesson in lessons:
        lesson_data = await _process_lesson(lesson, unit_title, shared_context)
        lesson_results.append(lesson_data)

    # 6. Format Discord Output
    output_lines = [
        f"**📝 Request:** {request}",
        "",
        f"**📋 Plan made by planner agent:**",
        plan_summary,
        "",
        "**📦 Here are your files:**"
    ]

    for result in lesson_results:
        lesson_name = result["lesson_name"]
        output_lines.append(f"- {lesson_name}")
        
        if result["ppt_path"]:
            output_lines.append(f"  __FILE__:{result['ppt_path']}")
        if result["docx_path"]:
            output_lines.append(f"  __FILE__:{result['docx_path']}")

    return "\n".join(output_lines)


async def planner_agent():
    print("[Planner] Enhanced History Planner Started.")
    
    while True:
        task_str = await task_queue.get()
        print(f"\n[Planner] Task received: {task_str}")

        try:
            output = await _orchestrate_history_package(task_str)
        except Exception as e:
            output = f"❌ Error during planning execution: {e}"
            print(output) # log to console

        await result_queue.put(output)
        task_queue.task_done()
