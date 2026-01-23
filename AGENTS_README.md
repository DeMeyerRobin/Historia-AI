# Agentic History Education System

## Overview
An intelligent Discord bot system that generates comprehensive history lesson packages, including teacher guides and PowerPoint presentations. The system uses multiple specialized agents working together, with built-in guardrails to ensure only history-related content is processed.

---

## 🛡️ Guardrails

**CRITICAL: This system ONLY processes history-related educational content.**

All user requests are validated by the Request Reviewer Agent before processing. Non-history requests are rejected with a helpful explanation.

### Allowed Topics:
- Historical events, periods, civilizations, wars, revolutions
- Historical figures, leaders, monarchs, explorers
- Cultural history, social movements, political developments
- Ancient, medieval, modern, or contemporary history
- Educational content about past events and their significance

### Rejected Topics:
- Current events or news (after 2024)
- Science, math, programming, technology (unless their history)
- Entertainment, games, sports (unless their history)
- Personal questions or advice
- General knowledge unrelated to history

---

## 🏗️ System Architecture

```
User Request
    ↓
[1] REQUEST REVIEWER AGENT ← Validates history-related
    ↓ (if approved)
[2] PLANNER AGENT ← Orchestrates entire workflow
    ↓
    ├→ [3] WORKER AGENT ← Research (Wikipedia)
    ├→ [4] FACT-CHECKER AGENT ← Validates accuracy
    └→ [5] PPT AGENT ← Generates PowerPoint
    ↓
User receives files (DOCX + PPTX)
```

---

## 📋 Agent Responsibilities

### 1. **Request Reviewer Agent** (`request_reviewer_agent.py`)
**Role:** Gate-keeper / Input Validation

**Responsibilities:**
- Validates that incoming requests are history-related
- Rejects non-history requests with helpful feedback
- Approves valid requests for processing

**Example Rejections:**
- "What's the weather today?" ❌
- "Write a Python function" ❌
- "Teach me calculus" ❌

**Example Approvals:**
- "Create 3 lessons on the French Revolution" ✅
- "Make a presentation on Ancient Egypt" ✅
- "Explain World War II" ✅

---

### 2. **Planner Agent** (`planner_agent.py`)
**Role:** Orchestrator / Project Manager

**Responsibilities:**
- Creates multi-lesson unit plans
- Coordinates research via Worker Agent
- Generates detailed Teacher's Guides (DOCX format)
- Creates PowerPoint slide structures
- Manages the entire workflow from request to delivery

**Key Features:**
- Plans 1-N lessons based on user request
- Each lesson gets:
  - Teacher's Guide (Word document with detailed content)
  - PowerPoint Presentation (30 slides with keywords)
- Avoids content repetition across lessons
- Uses evidence caching to minimize duplicate research

**Configuration:**
- `SLIDE_TARGET = 30` (slides per presentation)
- `MAX_WIKI_TOPICS = 5` (max Wikipedia topics per lesson)

---

### 3. **Worker Agent** (`worker_agent.py`)
**Role:** Task Executor / Tool Runner

**Responsibilities:**
- Executes research tasks (Britannica + Wikipedia)
- Runs fact-checking operations
- Handles any LLM-based task steps
- Serves as the "hands" of the Planner

**Supported Tools:**
```python
# Britannica research (primary source)
"TOOL:britannica:Korean War 1950-1953"

# Wikipedia research (fallback)
"TOOL:wikipedia:French Revolution"

# Fact-checking
"TOOL:factcheck:Louis XVI was executed in 1793|||<evidence text>"
```

**Smart Research Features:**
- **Primary Source:** Encyclopaedia Britannica for authoritative content
- **Relevance Checking:** Automatically detects when wrong article is found (e.g., ancient vs modern)
- **Automatic Retry:** Tries alternative search queries (up to 2 retries) if irrelevant result
- **Fallback:** Wikipedia available as backup source

**Usage:**
- Called by Planner for each step in the workflow
- Returns results as strings
- Handles both tool execution and LLM queries

---

### 4. **Fact-Checker Agent** (`fact_checker_agent.py`)
**Role:** Quality Assurance / Accuracy Validator

**Responsibilities:**
- Validates generated content against Britannica/Wikipedia evidence
- Ensures historical accuracy
- Prevents hallucinations and unsupported claims
- Triggers automatic content revision when issues found
- Filters out irrelevant sources from bibliography

**Output Format:**
```
GO/NO-GO: <verdict>
Confidence: <High|Medium|Low>
Reason: <explanation>
Warnings: <specific issues or "None">
```

**Revision Loop:**
- **Maximum 4 attempts** to fix content issues
- Automatically regenerates content based on fact-checker feedback
- Keeps trying until GO verdict or attempts exhausted
- Tracks revision history and includes in final report

**Current Integration:**
- ✅ **ENABLED** by default for all lessons
- Runs after Teacher's Guide generation
- Excludes irrelevant sources from sources document
- Provides detailed feedback to user on verification status

---

### 5. **PPT Agent** (`ppt_agent.py`)
**Role:** File Generator / PowerPoint Creator

**Responsibilities:**
- Converts slide structures into .pptx files
- Saves presentations to `outputs/` directory
- Operates asynchronously via message queue
- Handles content slides AND thought-provoking questions

**Slide Structure (30 slides per lesson):**
- **Slide 0:** Title slide (main title + subtitle)
- **Slides 1-28:** Content slides (title + bullet points + speaker notes)
- **Slides 10 & 20:** 🤔 **Critical Thinking Questions** (1 question each)
  - Makes students think logically
  - Not necessarily answerable from content
  - Example: "Why would coal and steel be the two important resources to focus on in the ECSC after WW2?"

**Features:**
- Automatic unique filename generation
- Based on lesson title with filesystem-safe slugs
- Speaker notes extracted from Teacher's Guide
- Special guidance notes for question slides

---

### 6. **Quizzer Agent** (`quizzer_agent.py`)
**Role:** Assessment Generator

**Responsibilities:**
- Generates age-appropriate quiz questions based on lesson content
- Creates questions answerable from the material taught
- Adjusts difficulty level based on student age (14-18 years)
- Produces 10 questions per unit

**Age-Based Difficulty:**
- **14 years:** Basic factual recall (names, dates, events)
- **16 years:** Moderate comprehension and basic analysis
- **18 years:** Analytical and critical thinking questions

**Output:**
- Saved as `quiz_<unit-title>.docx`
- Formatted for educational assessment
- Questions directly based on Teacher's Guide content

---

## 🔄 Workflow Example

### User Request:
```
/task Create 3 lessons on the French Revolution
```

### System Processing:

1. **Request Reviewer** validates it's history-related ✅

2. **Planner** creates unit plan:
   ```json
   {
     "unit_title": "The French Revolution",
     "lessons": [
       {"lesson_number": 1, "title": "Causes of the Revolution", ...},
       {"lesson_number": 2, "title": "The Reign of Terror", ...},
       {"lesson_number": 3, "title": "Napoleon's Rise to Power", ...}
     ]
   }
   ```

3. **For each lesson:**
   - **Worker** researches topics on Britannica (with smart retry for relevance)
   - **Planner** generates Teacher's Guide (30 sections, continuous text)
   - **Fact-Checker** validates content (up to 4 revision attempts if needed)
   - **Planner** creates slide structure (28 content + 2 question slides)
   - **PPT Agent** generates PowerPoint file with notes

4. **After all lessons:**
   - **Quizzer** generates age-appropriate quiz (10 questions)
   - **Planner** creates sources document with all references

5. **User receives:**
   - `lesson-1-causes-of-the-revolution.docx` (Teacher's Guide)
   - `lesson-1-causes-of-the-revolution.pptx` (30 slides + notes)
   - `lesson-2-the-reign-of-terror.docx`
   - `lesson-2-the-reign-of-terror.pptx`
   - `lesson-3-napoleons-rise-to-power.docx`
   - `lesson-3-napoleons-rise-to-power.pptx`
   - `quiz_the-french-revolution.docx` (10 questions)
   - `sources_the-french-revolution.docx` (Bibliography)
   - **Fact-Check Report:** Shows which lessons were verified/revised

---

## 📁 Directory Structure

```
agentic_system/
├── agents/
│   ├── request_reviewer_agent.py  ← NEW: Validates history requests
│   ├── planner_agent.py           ← Orchestrates workflow
│   ├── worker_agent.py            ← Executes tasks/research
│   ├── fact_checker_agent.py      ← Validates accuracy
│   └── ppt_agent.py               ← Generates PowerPoints
├── bot/
│   └── main.py                    ← Discord bot interface
├── queues/
│   ├── __init__.py
│   └── message_bus.py             ← Agent communication queues
├── utils/
│   ├── llm.py                     ← LLM interface
│   ├── tools.py                   ← Wikipedia, fact-checking tools
│   └── logger.py                  ← Logging utilities
├── outputs/                       ← Generated files (DOCX + PPTX)
└── .env                           ← Configuration (Discord token, API keys)
```

---

## 🚀 Usage

### Discord Commands

```bash
/task Create 3 lessons on the French Revolution
/task Teach me about Ancient Egypt
/task Make a presentation on World War II
```

### Testing Request Reviewer (Local)

```bash
cd agents
python request_reviewer_agent.py
```

This runs test cases to validate the request filtering logic.

---

## 🔧 Configuration

### Environment Variables (.env)
```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key  # or other LLM provider
```

### Agent Settings (in `planner_agent.py`)
```python
SLIDE_TARGET = 30                # Slides per presentation (28 content + 2 questions)
MAX_WIKI_TOPICS = 5              # Max research topics per lesson
DEFAULT_RESEARCH_TOOL = "britannica"  # Primary research source
FACT_CHECK_ENABLED = True        # Enable automatic fact checking
```

---

## 🎯 Key Features

### ✅ History-Only Guardrails
- All requests validated before processing
- Clear rejection messages for non-history topics
- Prevents misuse and maintains focus

### 📚 Comprehensive Output
- **Teacher's Guide:** Detailed, continuous text (30 sections) with speaker notes
- **PowerPoint:** 28 content slides + 2 critical thinking questions
- **Quiz:** 10 age-appropriate assessment questions
- **Sources Document:** Complete bibliography with all references
- All files saved to `outputs/` directory

### 🛡️ Automatic Fact Checking
- **LLM-based verification** against Britannica/Wikipedia sources
- **Revision loop:** Up to 4 attempts to fix inaccuracies
- **Source filtering:** Removes irrelevant sources from bibliography
- **User reporting:** Clear feedback on verification status

### 🔄 Context Awareness
- Evidence caching prevents duplicate research
- Tracks previous lesson content to avoid repetition
- Maintains continuity across multi-lesson units
- Smart research with relevance detection and retry

### 🎓 Educational Quality
- **Authoritative sources:** Encyclopaedia Britannica primary
- **Fact-checked content:** Verified against evidence
- **Critical thinking:** Thought-provoking questions in slides
- **Age-appropriate:** Quiz difficulty scales with student age
- Academic tone with specific dates, names, and locations

---

## 🧪 Testing

### Test Request Reviewer
```bash
python agents/request_reviewer_agent.py
```

### Test Individual Agents
Each agent file includes basic test functionality or can be imported and tested:

```python
from agents.worker_agent import run_worker_step
import asyncio

result = asyncio.run(run_worker_step("TOOL:wikipedia:French Revolution"))
print(result)
```

---

## 📈 Future Enhancements

1. **More Robust Fact-Checking:** Integrate fact-checker into every content generation step
2. **Multi-Source Research:** Add sources beyond Wikipedia (academic databases, archives)
3. **Customizable Templates:** Allow users to specify presentation styles
4. **Assessment Generation:** Create quizzes and tests based on lesson content
5. **Interactive Timeline:** Generate visual timelines for historical events
6. **Citation Management:** Automatically track and format sources

---

## 🐛 Troubleshooting

### Request Rejected (Not History)
- **Problem:** Request is about non-history topics
- **Solution:** Reformulate to focus on historical aspects

### No Wikipedia Results
- **Problem:** Worker can't find information
- **Solution:** Use more specific historical terms in request

### Missing Files
- **Problem:** DOCX or PPTX files not generated
- **Solution:** Check `outputs/` directory and console logs

### Agent Not Responding
- **Problem:** Background agents not started
- **Solution:** Restart bot, check `on_ready()` logs

---

## 📝 Agent Communication

Agents communicate via asyncio queues:

- `task_queue`: User requests → Planner
- `result_queue`: Final results → User
- `ppt_queue`: Slide structures → PPT Agent

This decoupled architecture allows agents to work independently and asynchronously.

---

## 🤝 Contributing

When adding new features:
1. **Maintain history focus** in all prompts and validations
2. **Document agent responsibilities** clearly in file headers
3. **Use consistent coding style** (docstrings, type hints)
4. **Test with multiple historical topics** before deploying

---

## 📄 License

[Specify your license here]

---

## 👨‍💻 Authors

[Your name/organization]

---

## 🎉 Acknowledgments

- OpenAI/Anthropic for LLM APIs
- Wikipedia for historical research data
- python-pptx and python-docx libraries
- Discord.py for bot framework
