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
│  • Receives Discord commands                                             │
│  • Routes to request reviewer                                            │
│  • Returns results to user                                               │
└───────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
╔═══════════════════════════════════════════════════════════════════════════╗
║                    🛡️ GUARDRAIL CHECKPOINT #1                            ║
║                                                                           ║
║                  REQUEST REVIEWER AGENT                                   ║
║                 (request_reviewer_agent.py)                               ║
║                                                                           ║
║  Validates: Is this about HISTORY?                                       ║
║                                                                           ║
║  ✅ YES → Continue to Planner                                            ║
║  ❌ NO  → Reject with helpful message                                    ║
╚═══════════════════════════════════════════════════════════════════════════╝
                    │                              │
                    │ APPROVED                     │ REJECTED
                    ▼                              ▼
┌────────────────────────────────┐   ┌───────────────────────────────┐
│      Continue Processing       │   │   Return Rejection Message    │
└────────────────────────────────┘   │  "Only history topics..."     │
                    │                 └───────────────────────────────┘
                    ▼
╔═══════════════════════════════════════════════════════════════════════════╗
║                         PLANNER AGENT (Orchestrator)                      ║
║                          (planner_agent.py)                               ║
║                                                                           ║
║  Phase 1: PLANNING                                                        ║
║  ├─ Parse request                                                         ║
║  ├─ Extract topic and number of lessons                                  ║
║  └─ Create unit plan structure                                           ║
║                                                                           ║
║  Phase 2: FOR EACH LESSON                                                ║
║  ├─ Research (via Worker Agent)                                          ║
║  ├─ Generate Teacher's Guide (30 sections)                               ║
║  ├─ Create slide structure (30 slides)                                   ║
║  └─ Dispatch to PPT Agent                                                ║
║                                                                           ║
║  Phase 3: DELIVERY                                                        ║
║  └─ Return file paths to user                                            ║
╚═══════════════════════════════════════════════════════════════════════════╝
         │                    │                    │
         │ Research           │ Validate           │ Generate
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  WORKER AGENT   │  │ FACT-CHECKER    │  │   PPT AGENT     │
│  worker_agent   │  │ AGENT           │  │   ppt_agent     │
│      .py        │  │ fact_checker_   │  │      .py        │
│                 │  │   agent.py      │  │                 │
│  Executes:      │  │                 │  │  Creates:       │
│  • Wikipedia    │  │  Validates:     │  │  • .pptx files  │
│    research     │  │  • Content vs   │  │  • Title slide  │
│  • Fact-check   │  │    evidence     │  │  • 30 content   │
│    tools        │  │  • Accuracy     │  │    slides       │
│  • LLM tasks    │  │                 │  │                 │
│                 │  │  Returns:       │  │  Saves to:      │
│  Returns:       │  │  • GO/NO-GO     │  │  outputs/       │
│  • Research     │  │  • Confidence   │  │                 │
│    data         │  │  • Corrections  │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┴────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      OUTPUTS DIRECTORY        │
              │                               │
              │  • lesson-1-topic.docx        │
              │  • lesson-1-topic.pptx        │
              │  • lesson-2-topic.docx        │
              │  • lesson-2-topic.pptx        │
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

Layer 3: EVIDENCE-BASED
├─ Checks: Content vs Wikipedia evidence
├─ Method: Worker research + Fact-checker validation
└─ Action: Ensure factual accuracy
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
        ├─ Worker researches on Wikipedia
        ├─ Planner writes Teacher's Guide (30 sections)
        ├─ Planner designs slides (30 slides)
        └─ PPT Agent creates .pptx file
        ↓
T=60s   FOR LESSON 2: (repeat)
        ↓
T=120s  FOR LESSON 3: (repeat)
        ↓
T=180s  All files ready
        └─ User receives 6 files (3 DOCX + 3 PPTX)
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
┌─────────┐   TOOL:wikipedia:French Revolution   ┌────────┐
│ Planner │ ─────────────────────────────────────>│ Worker │
└─────────┘                                       └────────┘
                                                      │
                                              ┌───────┴────────┐
                                              │ Wikipedia API  │
                                              │ Fetch summary  │
                                              └───────┬────────┘
                                                      │
┌─────────┐   Return: Historical evidence           │
│ Planner │ <─────────────────────────────────────────┘
└─────────┘
```

### Pattern 3: File Generation (PPT Agent)
```
┌─────────┐   {slides: [...], title: ...}   ┌───────────┐
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
│   ├── worker_agent.py             ← 🔧 Executes tasks
│   ├── fact_checker_agent.py       ← ✅ Validates accuracy
│   └── ppt_agent.py                ← 📄 Generates PowerPoints
│
├── bot/                             ← Discord interface
│   └── main.py                     ← Entry point, slash commands
│
├── queues/                          ← Agent communication
│   └── message_bus.py              ← Async queues (task, result, ppt)
│
├── utils/                           ← Shared utilities
│   ├── llm.py                      ← LLM interface
│   ├── tools.py                    ← Wikipedia, fact-check tools
│   └── logger.py                   ← Logging
│
├── outputs/                         ← Generated files
│   ├── lesson-1-topic.docx
│   ├── lesson-1-topic.pptx
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
│  • OpenAI/Anthropic API (LLM)           │
│  • Wikipedia API (Research)             │
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

### 5. Evidence-Based Content
- **Why:** Ensures factual accuracy
- **How:** Wikipedia research + fact-checking
- **Benefit:** Educational quality, trustworthy

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
