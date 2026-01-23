# Agent System Quick Reference

## 🎯 What Each Agent Does

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENTIC SYSTEM OVERVIEW                     │
└─────────────────────────────────────────────────────────────────┘

1️⃣  REQUEST REVIEWER AGENT (request_reviewer_agent.py)
    ├─ Validates: Is this a history question?
    ├─ Approves: ✅ "Teach me about Ancient Rome"
    └─ Rejects: ❌ "What's the weather today?"

            ↓ (if approved)

2️⃣  PLANNER AGENT (planner_agent.py)
    ├─ Creates: Multi-lesson unit plan
    ├─ Orchestrates: All other agents
    ├─ Generates: Teacher guides (DOCX)
    ├─ Designs: Slide structures
    └─ Output: Complete lesson packages

            ↓ (delegates to)

3️⃣  WORKER AGENT (worker_agent.py)
    ├─ Executes: Britannica + Wikipedia research
    ├─ Smart retry: Detects irrelevant results
    └─ Returns: Authoritative historical data

4️⃣  FACT-CHECKER AGENT (fact_checker_agent.py)
    ├─ Validates: Content accuracy vs evidence
    ├─ Revises: Up to 4 attempts to fix issues
    ├─ Filters: Removes irrelevant sources
    └─ Reports: Verification status to user

5️⃣  PPT AGENT (ppt_agent.py)
    ├─ Creates: PowerPoint files (.pptx)
    ├─ Formats: 28 content + 2 question slides
    ├─ Adds: Speaker notes from guide
    └─ Saves: To outputs/ directory

6️⃣  QUIZZER AGENT (quizzer_agent.py)
    ├─ Generates: 10 age-appropriate questions
    ├─ Adjusts: Difficulty by student age
    └─ Creates: Quiz document (.docx)
```

---

## 🔄 Request Flow

```
User Types: "/task Create 3 lessons on the French Revolution"
     │
     ├─→ REQUEST REVIEWER checks: "Is this history?" 
     │         │
     │         ├─→ YES ✅ → Continue
     │         └─→ NO ❌  → Reject with helpful message
     │
     ├─→ PLANNER creates unit plan:
     │         │
     │         ├─→ Lesson 1: Causes of the Revolution
     │         ├─→ Lesson 2: The Reign of Terror  
     │         └─→ Lesson 3: Napoleon's Rise
     │
     │   For each lesson:
     │         │
     │         ├─→ WORKER researches on Wikipedia
     │         │      └─→ Returns: Historical evidence
     │         │
     │         ├─→ PLANNER writes Teacher's Guide (30 sections)
     │         │      └─→ Saves: lesson-1-causes.docx
     │         │
     │         ├─→ PLANNER designs slides (30 slides)
     │         │      └─→ Sends to PPT AGENT
     │         │
     │         └─→ PPT AGENT creates PowerPoint
     │                └─→ Saves: lesson-1-causes.pptx
     │
     └─→ User receives:
              ├─ lesson-1-causes.docx + .pptx
              ├─ lesson-2-terror.docx + .pptx
              └─ lesson-3-napoleon.docx + .pptx
```

---

## 🛡️ Guardrails Summary

| Checkpoint | Agent | Action |
|------------|-------|--------|
| **Input Validation** | Request Reviewer | Only history requests pass |
| **Content Generation** | Planner | History-focused prompts |
| **Accuracy Check** | Fact-Checker | Validates & revises (4x max) |
| **Evidence Base** | Worker | Britannica + Wikipedia sources |
| **Source Filtering** | Fact-Checker | Removes irrelevant references |

---

## 📂 File Locations

| Component | File Path |
|-----------|-----------|
| Request validation | `agents/request_reviewer_agent.py` |
| Main orchestration | `agents/planner_agent.py` |
| Research & tools | `agents/worker_agent.py` |
| Accuracy validation | `agents/fact_checker_agent.py` |
| File generation | `agents/ppt_agent.py` |
| Quiz generation | `agents/quizzer_agent.py` |
| Discord interface | `bot/main.py` |
| Generated files | `outputs/` |
| Documentation | `AGENTS_README.md` |

---

## 🎓 Example Use Cases

### ✅ APPROVED Requests

```
"Create 3 lessons on the French Revolution"
"Teach me about Ancient Egypt"
"Make a presentation on World War II"
"Explain the Renaissance period"
"5 lessons on the American Civil War"
"Tell me about Julius Caesar"
```

### ❌ REJECTED Requests

```
"What's the weather today?"
"Write a Python function to sort a list"
"Solve this math problem"
"Tell me a joke"
"What's the latest news?"
"Teach me how to cook pasta"
```

### 💡 BORDERLINE (Will be evaluated by LLM)

```
"History of computers" ← APPROVED (history aspect)
"How computers work" ← REJECTED (technical, not historical)

"History of science in Ancient Greece" ← APPROVED
"Explain quantum physics" ← REJECTED

"History of the Olympics" ← APPROVED
"Who won the Olympics last year?" ← REJECTED
```

---

## 🔧 Quick Configuration

```python
# In planner_agent.py

SLIDE_TARGET = 30                    # Slides per presentation (28 content + 2 questions)
MAX_WIKI_TOPICS = 5                  # Max Wikipedia lookups per lesson
FACT_CHECK_ENABLED = True            # Enable fact-checking with revision loop
DEFAULT_RESEARCH_TOOL = "britannica" # Primary source (with Wikipedia fallback)

# In .env file

DISCORD_TOKEN=your_token
OPENAI_API_KEY=your_key   # Or other LLM provider (Hugging Face Router API recommended)
```

---

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install discord.py python-dotenv python-pptx python-docx openai
   ```

2. **Configure .env:**
   ```
   DISCORD_TOKEN=your_discord_token
   OPENAI_API_KEY=your_api_key
   ```

3. **Run bot:**
   ```bash
   python bot/main.py
   ```

4. **Test in Discord:**
   ```
   /task Create 3 lessons on Ancient Rome
   ```

---

## 📊 Agent Responsibilities Matrix

| Agent | Input | Output | Purpose |
|-------|-------|--------|---------|
| **Request Reviewer** | User query | Approved/Rejected | Guardrail |
| **Planner** | Approved query | DOCX + PPTX + Quiz + Sources | Orchestrator |
| **Worker** | Research task | Britannica/Wikipedia data | Tool executor |
| **Fact-Checker** | Text + Evidence | GO/NO-GO + Warnings | Quality assurance |
| **PPT** | Slide structure | .pptx file (with questions) | File generator |
| **Quizzer** | All lessons | .docx quiz (10 questions) | Assessment creator |

---

## 🎯 Key Principles

1. **Separation of Concerns**
   - Each agent has ONE clear responsibility
   - No overlap in functionality

2. **History-Only Focus**
   - Validated at entry point (Request Reviewer)
   - Reinforced in all prompts (Planner)

3. **Evidence-Based**
   - Primary research from Encyclopaedia Britannica
   - Wikipedia fallback for additional context
   - Fact-checking validates accuracy with up to 4 revision attempts

4. **Quality Assurance**
   - Smart search with relevance detection and retry
   - Automatic revision loop fixes fact-checker warnings
   - Source filtering removes irrelevant references

5. **Async Communication**
   - Agents communicate via queues
   - Decoupled, scalable architecture

6. **Clear Documentation**
   - Each file has header explaining purpose
   - README provides system overview
   - This file gives quick reference

---

## 🐛 Common Issues

| Problem | Solution |
|---------|----------|
| Request rejected | Make sure it's history-related |
| No files generated | Check `outputs/` directory and logs |
| Wikipedia errors | Topic may be too obscure/specific |
| Britannica search fails | System will automatically retry with alternative queries, then fall back to Wikipedia |
| Fact-checker rejects content | Content will be automatically revised up to 4 times with specific warnings |
| Bot not responding | Check if agents started in `on_ready()` |
| DOCX not created | Install: `pip install python-docx` |
| PPTX not created | Install: `pip install python-pptx` |

---

## 📚 Further Reading

- Full documentation: `AGENTS_README.md`
- Code comments: Check each agent file header
- Message bus: `queues/message_bus.py`
- Tools: `utils/tools.py`
- LLM interface: `utils/llm.py`

---

**Last Updated:** 2026-01-19
