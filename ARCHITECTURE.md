# System Architecture Diagram

## Overview: Multi-Agent History Education System

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                          DISCORD USER INTERFACE                           ║
║                      /task Create 3 lessons on...                         ║
╚═══════════════════════════════════════════════════════════════════════════╝
                                      │
                                      ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                              main.py (bot)                                │
│  • Receives Discord commands                                              │
│  • Routes to request reviewer                                             │
│  • Returns results to user                                                │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
╔═══════════════════════════════════════════════════════════════════════════╗
║                    🛡️ GUARDRAIL CHECKPOINT #1                             ║
║                                                                           ║
║                  REQUEST REVIEWER AGENT                                   ║
║                 (request_reviewer_agent.py)                               ║
║                                                                           ║
║  Validates: Is this about HISTORY?                                        ║
║                                                                           ║
║  ✅ YES → Continue to Planner                                             ║
║  ❌ NO  → Reject with helpful message                                     ║
╚══════════════════════════════════════════════════════════════════════════=═╝
                    │                              │
                    │ APPROVED                     │ REJECTED
                    ▼                              ▼
┌────────────────────────────────┐   ┌───────────────────────────────┐
│      Continue Processing       │   │   Return Rejection Message    │
└────────────────────────────────┘   │  "Only history topics..."     │
                    │                └───────────────────────────────┘
                    ▼
╔═══════════════════════════════════════════════════════════════════════════╗
║                         PLANNER AGENT (Orchestrator)                      ║
║                          (planner_agent.py)                               ║
║                                                                           ║
║  Phase 1: PLANNING                                                        ║
║  ├─ Parse request                                                         ║
║  ├─ Extract topic and number of lessons                                   ║
║  └─ Create unit plan structure                                            ║
║                                                                           ║
║  Phase 2: FOR EACH LESSON                                                 ║
║  ├─ Research (via Worker Agent: Britannica → Wikipedia)                   ║
║  ├─ Generate Teacher's Guide (30 sections)                                ║
║  ├─ Fact-check content (up to 4 revision attempts)                        ║
║  ├─ Filter irrelevant sources from bibliography                           ║
║  ├─ Create slide structure (28 content + 2 question slides)               ║
║  └─ Dispatch to PPT Agent                                                 ║
║                                                                           ║
║  Phase 3: QUIZ GENERATION                                                 ║
║  ├─ Send all lessons to Quizzer Agent                                     ║
║  └─ Generate 10 age-appropriate questions                                 ║
║                                                                           ║
║  Phase 4: DELIVERY                                                        ║
║  ├─ Report fact-check results to user                                     ║
║  └─ Return file paths (guides, slides, quiz, sources)                     ║
╚═══════════════════════════════════════════════════════════════════════════╝
         │                    │                    │                    │
         │ Research           │ Validate           │ Generate           │ Quiz
         ▼                    ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  WORKER AGENT   │  │ FACT-CHECKER    │  │   PPT AGENT     │  │  QUIZZER AGENT  │
│  worker_agent   │  │ AGENT           │  │   ppt_agent     │  │  quizzer_agent  │
│      .py        │  │ fact_checker_   │  │      .py        │  │      .py        │
│                 │  │   agent.py      │  │                 │  │                 │
│  Executes:      │  │                 │  │  Creates:       │  │  Generates:     │
│  • Britannica   │  │  Validates:     │  │  • .pptx files  │  │  • 10 questions │
│    research     │  │  • Content vs   │  │  • Title slide  │  │  • Age-scaled   │
│  • Wikipedia    │  │    evidence     │  │  • 28 content   │  │    difficulty   │
│    fallback     │  │  • Accuracy     │  │    slides       │  │  • DOCX format  │
│  • Smart retry  │  │                 │  │  • 2 question   │  │                 │
│                 │  │  Revision loop: │  │    slides       │  │  Saves to:      │
│  Returns:       │  │  • Max 4 tries  │  │                 │  │  outputs/       │
│  • Research     │  │  • GO/NO-GO     │  │  Saves to:      │  │  quiz.docx      │
│    data         │  │  • Warnings     │  │  outputs/       │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │                    │
         └────────────────────┴────────────────────┴────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      OUTPUTS DIRECTORY        │
              │                               │
              │  • lesson-1-topic.docx        │
              │  • lesson-1-topic.pptx        │
              │  • lesson-2-topic.docx        │
              │  • lesson-2-topic.pptx        │
              │  • quiz.docx                  │
              │  • sources.docx               │
              │  • ...                        │
              └───────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │       DISCORD USER            │
              │  Receives files + summary     │
              └───────────────────────────────┘
```

---

## Communication Queues

```
┌─────────────┐
│  task_queue │ ← User requests go here (from main.py → planner)
└─────────────┘

┌──────────────┐
│ result_queue │ ← Final results go here (from planner → main.py)
└──────────────┘

┌───────────┐
│ ppt_queue │ ← Slide structures go here (from planner → ppt_agent)
└───────────┘
```

---

## Guardrail Layers

```
Layer 1: REQUEST REVIEWER
├─ Checks: Is this a history question?
├─ Method: LLM-based validation
└─ Action: Reject or approve

Layer 2: PLANNER PROMPTS
├─ Checks: History-focused instructions
├─ Method: Prompt engineering
└─ Action: Guide content generation

Layer 3: EVIDENCE-BASED RESEARCH
├─ Checks: Britannica article relevance with smart retry
├─ Method: Worker research with alternative queries
└─ Action: Fall back to Wikipedia if needed

Layer 4: FACT-CHECKING WITH REVISION
├─ Checks: Content accuracy vs evidence
├─ Method: Fact-checker validation with up to 4 revision attempts
└─ Action: Regenerate content based on specific warnings

Layer 5: SOURCE FILTERING
├─ Checks: Relevance of cited sources
├─ Method: Evidence tracking and filtering
└─ Action: Remove irrelevant sources from bibliography
```

---

## Request Flow Timeline

```
T=0s    User sends: "/task Create 3 lessons on French Revolution"
        ↓
T=1s    Main.py receives command
        ↓
T=2s    Request Reviewer validates
        ├─ LLM call: "Is this history-related?"
        └─ Result: ✅ APPROVED
        ↓
T=3s    Planner receives approved request
        ├─ LLM call: "Create unit plan"
        └─ Result: 3 lessons structured
        ↓
T=4s    FOR LESSON 1:
        ├─ Worker researches on Britannica (smart retry if needed)
        ├─ Planner writes Teacher's Guide (30 sections)
        ├─ Fact-checker validates content (up to 4 revisions if needed)
        ├─ Planner filters irrelevant sources from bibliography
        ├─ Planner designs slides (28 content + 2 question slides)
        └─ PPT Agent creates .pptx file
        ↓
T=60s   FOR LESSON 2: (repeat)
        ↓
T=120s  FOR LESSON 3: (repeat)
        ↓
T=180s  Quiz generation
        ├─ Quizzer receives all lessons
        ├─ Generates 10 age-appropriate questions
        └─ Saves quiz.docx
        ↓
T=185s  All files ready
        ├─ User receives fact-check report (revision counts)
        └─ User downloads: 3 guides, 3 slides, 1 quiz, 1 sources (8 files)
```

---

## Agent Interaction Patterns

### Pattern 1: Request Validation (Request Reviewer)
```
┌──────┐     query      ┌─────────────────┐     
│ User │ ──────────────>│ Request Reviewer│
└──────┘                └─────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │     LLM Call      │
                    │ "Is this history?"│
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                  ✅ YES              ❌ NO
                    │                   │
              Continue            Reject & explain
```

### Pattern 2: Research (Worker Agent)
```
┌─────────┐   TOOL:britannica:Lisbon Treaty    ┌────────┐
│ Planner │ ─────────────────────────────────> │ Worker │
└─────────┘                                    └────────┘
                                                    │
                                            ┌───────┴────────┐
                                            │ Britannica API │
                                            │ Check relevance│
                                            └───────┬────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                          │                   │
                                    ✅ Relevant         ❌ Irrelevant
                                          │                   │
                                   Return data        Retry with alt query
                                                             │
                                                      Max 2 attempts
                                                             │
                                                    Fall back to Wikipedia
                                                             │
┌─────────┐   Return: Historical evidence                    │
│ Planner │ <────────────────────────────────────────────────┘
└─────────┘
```

### Pattern 3: File Generation (PPT Agent)
```
┌─────────┐   {slides: [...], title: ...}    ┌───────────┐
│ Planner │ ────────────────────────────────>│ ppt_queue │
└─────────┘                                  └───────────┘
                                                    │
                                             ┌──────┴──────┐
                                             │  PPT Agent  │
                                             │  (listening)│
                                             └──────┬──────┘
                                                    │
                                            ┌───────┴────────┐
                                            │ python-pptx    │
                                            │ Create .pptx   │
                                            └───────┬────────┘
                                                    │
                                                    ▼
                                            ┌───────────────┐
                                            │ outputs/      │
                                            │ lesson-1.pptx │
                                            └───────────────┘
```

---

## File Structure with Agent Mapping

```
agentic_system/
│
├── agents/                          ← All agent logic
│   ├── request_reviewer_agent.py   ← 🛡️ Validates history requests
│   ├── planner_agent.py            ← 🎯 Orchestrates workflow
│   ├── worker_agent.py             ← 🔧 Executes tasks (Britannica + Wikipedia)
│   ├── fact_checker_agent.py       ← ✅ Validates accuracy with revision loop
│   ├── ppt_agent.py                ← 📄 Generates PowerPoints (28 + 2 question slides)
│   └── quizzer_agent.py            ← 📝 Creates age-appropriate quizzes
│
├── bot/                             ← Discord interface
│   └── main.py                     ← Entry point, slash commands
│
├── queues/                          ← Agent communication
│   └── message_bus.py              ← Async queues (task, result, ppt)
│
├── utils/                           ← Shared utilities
│   ├── llm.py                      ← LLM interface
│   ├── tools.py                    ← Britannica, Wikipedia, fact-check tools
│   └── logger.py                   ← Logging
│
├── outputs/                         ← Generated files
│   ├── lesson-1-topic.docx
│   ├── lesson-1-topic.pptx
│   ├── quiz.docx
│   ├── sources.docx
│   └── ...
│
└── Documentation/
    ├── AGENTS_README.md            ← Full documentation
    ├── QUICK_REFERENCE.md          ← Quick lookup
    ├── CHANGES_SUMMARY.md          ← What changed
    └── ARCHITECTURE.md             ← This file
```

---

## Technology Stack

```
┌─────────────────────────────────────────┐
│         APPLICATION LAYER               │
│  • Discord Bot (discord.py)             │
│  • Async Event Loop (asyncio)           │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         AGENT LAYER                     │
│  • Custom Agents (Python classes)       │
│  • Message Queues (asyncio.Queue)       │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         SERVICES LAYER                  │
│  • Hugging Face Router API (LLM)        │
│  • Encyclopaedia Britannica (Primary)   │
│  • Wikipedia API (Fallback)             │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         FILE GENERATION                 │
│  • python-pptx (PowerPoint)             │
│  • python-docx (Word)                   │
└─────────────────────────────────────────┘
                  │
┌─────────────────────────────────────────┐
│         STORAGE                         │
│  • Local filesystem (outputs/)          │
└─────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Asynchronous Architecture
- **Why:** Allows multiple operations to run concurrently
- **How:** asyncio queues for inter-agent communication
- **Benefit:** Better performance, scalable

### 2. Specialized Agents
- **Why:** Separation of concerns, easier maintenance
- **How:** Each agent has ONE clear responsibility
- **Benefit:** Modular, testable, clear

### 3. Queue-Based Communication
- **Why:** Decouples agents, allows async processing
- **How:** task_queue, result_queue, ppt_queue
- **Benefit:** Scalable, fault-tolerant

### 4. LLM-Based Validation
- **Why:** Flexible, understands natural language
- **How:** Request Reviewer uses LLM to assess intent
- **Benefit:** Catches edge cases, user-friendly

### 5. Evidence-Based Content with Smart Retry
- **Why:** Ensures factual accuracy and relevance
- **How:** Britannica primary research with relevance checking, automatic retry with alternative queries (max 2 attempts), Wikipedia fallback
- **Benefit:** Authoritative sources, handles search failures gracefully

### 6. Fact-Checking with Revision Loop
- **Why:** Maintains content quality and accuracy
- **How:** LLM-based fact-checking with up to 4 automatic revision attempts based on specific warnings
- **Benefit:** High-quality content, transparent verification process

### 7. Source Filtering
- **Why:** Bibliography should only include relevant references
- **How:** Track evidence usage during fact-checking, filter out irrelevant sources
- **Benefit:** Clean bibliographies, professional documentation

---

## Scalability Considerations

### Current System (Single Instance)
```
Discord Bot → Request Reviewer → Planner → [Worker, Fact-Checker, PPT]
   (1)              (1)             (1)              (1 each)
```

### Potential Scaling (Multiple Workers)
```
Discord Bot → Request Reviewer → Planner → [Worker Pool] → PPT Pool
   (1)              (1)             (1)         (N)          (M)
```

### Potential Distributed (Multiple Planners)
```
Load Balancer → [Planner Pool] → [Worker Pool] → [PPT Pool]
     (1)            (N)              (M)            (K)
```

---

**This architecture provides:**
- ✅ Clear separation of concerns
- ✅ History-only guardrails
- ✅ Scalable async design
- ✅ Evidence-based content
- ✅ User-friendly interface
