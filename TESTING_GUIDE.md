# Testing Guide

## Quick Test Checklist

### ✅ Before Testing
- [ ] Install dependencies: `pip install discord.py python-dotenv python-pptx python-docx openai`
- [ ] Configure `.env` with Discord token and API keys
- [ ] Ensure `outputs/` directory exists

---

## 1. Test Request Reviewer Agent (Standalone)

### Run Test Cases
```bash
cd agents
python request_reviewer_agent.py
```

### Expected Output
```
Testing Request Reviewer Agent
==================================================

Request: Create 3 lessons on the French Revolution
Valid: True
Message: ✅ Request approved: ...

Request: What's the weather today?
Valid: False
Message: ❌ Request Rejected: Not History-Related...

Request: Teach me about Ancient Rome
Valid: True
Message: ✅ Request approved: ...

Request: Write a Python function to sort a list
Valid: False
Message: ❌ Request Rejected: Not History-Related...

Request: Explain World War II
Valid: True
Message: ✅ Request approved: ...

Request: What's the best pizza place nearby?
Valid: False
Message: ❌ Request Rejected: Not History-Related...

Request: Make a presentation on the Industrial Revolution
Valid: True
Message: ✅ Request approved: ...
```

### What to Check
- ✅ History requests return `True`
- ✅ Non-history requests return `False`
- ✅ Rejection messages are helpful and clear
- ✅ No errors or exceptions

---

## 2. Test Full System via Discord

### Start the Bot
```bash
python bot/main.py
```

### Expected Console Output
```
Bot is online as YourBot#1234
[Main] Planner + PPT agent started.
[Planner] Enhanced History Planner Started.
[PPT Agent] Started.
Synced X commands.
```

### Test Case 1: Valid History Request
**Command:**
```
/task Create 3 lessons on Ancient Rome
```

**Expected Flow:**
1. Bot responds: "🔍 Reviewing your request..."
2. Bot responds: "✅ Request validated - Processing your history task..."
3. Bot shows progress messages
4. Bot delivers 6 files:
   - `lesson-1-*.docx` and `lesson-1-*.pptx`
   - `lesson-2-*.docx` and `lesson-2-*.pptx`
   - `lesson-3-*.docx` and `lesson-3-*.pptx`

**What to Check:**
- ✅ Request approved without rejection
- ✅ Planner creates 3 lessons
- ✅ Each lesson has both DOCX and PPTX
- ✅ Files exist in `outputs/` directory
- ✅ DOCX contains continuous text (30 sections)
- ✅ PPTX contains 30 content slides + 1 title slide
- ✅ Content is historically accurate

---

### Test Case 2: Invalid Non-History Request
**Command:**
```
/task What's the weather today?
```

**Expected Response:**
```
🔍 Reviewing your request...

❌ **Request Rejected: Not History-Related**

This request appears to be about current events or weather, not historical topics.

**This system only processes history-related educational content.**

Examples of valid requests:
- "Create 3 lessons on the French Revolution"
- "Teach me about Ancient Egypt"
- "Make a presentation on World War II"
- "Explain the Renaissance period"

Please reformulate your request to focus on a historical topic.
```

**What to Check:**
- ✅ Request immediately rejected
- ✅ Helpful rejection message shown
- ✅ Examples provided
- ✅ No files generated
- ✅ No processing time wasted

---

### Test Case 3: Another Invalid Request
**Command:**
```
/task Write a Python function to sort a list
```

**Expected Response:**
```
❌ **Request Rejected: Not History-Related**

This request is about programming/computer science, not historical topics.

[Same helpful message as above]
```

---

### Test Case 4: Borderline Request (History of Tech)
**Command:**
```
/task Teach me about the history of computers
```

**Expected Response:**
```
✅ Request validated - Processing your history task...
[Proceeds to generate content]
```

**What to Check:**
- ✅ Request approved (has "history" aspect)
- ✅ Content focuses on historical development
- ✅ Files generated successfully

---

### Test Case 5: Multiple Lessons
**Command:**
```
/task Create 5 lessons on World War II
```

**What to Check:**
- ✅ System creates exactly 5 lessons
- ✅ 10 files total (5 DOCX + 5 PPTX)
- ✅ Each lesson covers different aspects
- ✅ No content repetition across lessons
- ✅ Chronological or thematic progression

---

## 3. Test Individual Agents (Advanced)

### Test Worker Agent

```python
# Create test file: test_worker.py
import asyncio
from agents.worker_agent import run_worker_step

async def test_worker():
    # Test Wikipedia tool
    result = await run_worker_step("TOOL:wikipedia:French Revolution")
    print("Wikipedia Result:")
    print(result[:200])  # First 200 chars
    print("...")
    
    # Test fact-check tool
    claim = "Louis XVI was executed in 1793"
    evidence = "Louis XVI of France was executed on January 21, 1793."
    result = await run_worker_step(f"TOOL:factcheck:{claim}|||{evidence}")
    print("\nFact-Check Result:")
    print(result)

asyncio.run(test_worker())
```

**Run:**
```bash
python test_worker.py
```

**Expected:**
- ✅ Wikipedia returns historical summary
- ✅ Fact-check validates the claim
- ✅ No errors

---

### Test Fact-Checker Agent

```python
# Create test file: test_fact_checker.py
import asyncio
from agents.fact_checker_agent import fact_checker_agent

async def test_fact_checker():
    evidence = """
    The French Revolution began in 1789 with the Storming of the Bastille.
    Louis XVI was executed in 1793. The Revolution ended in 1799 with
    Napoleon's rise to power.
    """
    
    # Test correct fact
    result = await fact_checker_agent(
        "Louis XVI was executed in 1793",
        evidence
    )
    print("Test 1 (Correct):")
    print(result)
    print()
    
    # Test incorrect fact
    result = await fact_checker_agent(
        "Louis XVI was executed in 1799",
        evidence
    )
    print("Test 2 (Incorrect):")
    print(result)

asyncio.run(test_fact_checker())
```

**Expected:**
- ✅ Correct fact gets GO verdict
- ✅ Incorrect fact gets NO-GO verdict with correction

---

## 4. Test File Generation

### Test DOCX Generation

**Check generated DOCX files:**
1. Open `outputs/lesson-*.docx`
2. Verify:
   - ✅ Title at top
   - ✅ Continuous paragraph text (NOT bullet points)
   - ✅ ~30 sections of content
   - ✅ Each section is 3-5 sentences
   - ✅ Academic language (no "dreamy" phrasing)
   - ✅ Historically accurate content

---

### Test PPTX Generation

**Check generated PPTX files:**
1. Open `outputs/lesson-*.pptx`
2. Verify:
   - ✅ Slide 1: Title slide (lesson title + subtitle)
   - ✅ Slides 2-31: Content slides (30 total)
   - ✅ Each slide has:
     - Clear, factual title
     - 2-4 bullet points
     - Bullets are keywords/short phrases (≤6 words)
   - ✅ No complete sentences in bullets
   - ✅ Logical flow through the topic

---

## 5. Performance Testing

### Test Response Time

**Small Request (1 lesson):**
```
/task Create 1 lesson on Julius Caesar
```
**Expected Time:** ~20-30 seconds

**Medium Request (3 lessons):**
```
/task Create 3 lessons on the French Revolution
```
**Expected Time:** ~60-90 seconds

**Large Request (5 lessons):**
```
/task Create 5 lessons on World War II
```
**Expected Time:** ~150-200 seconds

### What to Monitor
- ✅ Console shows progress messages
- ✅ No errors or timeouts
- ✅ Memory usage stays reasonable
- ✅ All files generated successfully

---

## 6. Edge Case Testing

### Test Case: Very Short Request
```
/task Rome
```
**Expected:** System interprets as 1 lesson on Roman history

---

### Test Case: Ambiguous Request
```
/task Tell me about Caesar
```
**Expected:** 
- Request approved (historical figure)
- Content about Julius Caesar (most famous)

---

### Test Case: Modern History
```
/task Create 3 lessons on the Cold War
```
**Expected:** 
- Request approved
- Content focuses on historical events (1947-1991)

---

### Test Case: Very Recent History (Borderline)
```
/task Teach me about 2020 pandemic
```
**Expected:** 
- Might be rejected (too recent, not enough historical distance)
- OR approved if framed as historical event
- Depends on LLM interpretation

---

### Test Case: History of Non-History Topic
```
/task History of mathematics
```
**Expected:** 
- Request approved (history aspect)
- Content about mathematical development through ages

---

## 7. Error Handling Testing

### Test: Missing Wikipedia Article
```
/task Create a lesson on Obscure Historical Figure XYZ123
```
**Expected:**
- Worker returns "No specific evidence found"
- Planner proceeds with limited information
- System doesn't crash

---

### Test: API Timeout (Simulate)
**Temporarily disconnect internet or set very low timeout**
**Expected:**
- Graceful error message
- User notified of issue
- System doesn't crash

---

### Test: Invalid LLM Response
**Simulate with malformed prompt**
**Expected:**
- System uses fallback parsing
- Returns "Failed to generate" message
- User notified, system continues

---

## 8. Regression Testing Checklist

After any code changes, verify:

- [ ] Request Reviewer still validates correctly
- [ ] History requests still approved
- [ ] Non-history requests still rejected
- [ ] Planner creates correct number of lessons
- [ ] Worker fetches Wikipedia data
- [ ] DOCX files generated with continuous text
- [ ] PPTX files generated with 30 slides
- [ ] Files saved to outputs/ directory
- [ ] No errors in console
- [ ] Discord bot responds correctly

---

## 9. Common Issues & Solutions

### Issue: Bot doesn't respond to `/task`
**Solution:**
- Check Discord token in `.env`
- Verify bot has permissions in Discord server
- Check console for error messages

---

### Issue: All requests rejected
**Solution:**
- Check LLM API key in `.env`
- Verify `utils/llm.py` configuration
- Test request_reviewer standalone

---

### Issue: No files generated
**Solution:**
- Check `outputs/` directory exists
- Verify file permissions
- Check console for PPT agent errors
- Install: `pip install python-pptx python-docx`

---

### Issue: Wikipedia errors
**Solution:**
- Check internet connection
- Verify Wikipedia API not blocked
- Try with different historical topics

---

### Issue: DOCX not opening
**Solution:**
- Verify `python-docx` installed correctly
- Check file not corrupted
- Try different historical topic

---

### Issue: PPTX has wrong slide count
**Solution:**
- Check `SLIDE_TARGET` setting in planner_agent.py
- Verify slide generation prompt
- Check PPT agent logs

---

## 10. Testing Best Practices

### Do:
✅ Test both valid and invalid requests  
✅ Verify file contents, not just existence  
✅ Check console logs for errors  
✅ Test edge cases and ambiguous requests  
✅ Monitor performance with different request sizes  
✅ Verify no content repetition across lessons  

### Don't:
❌ Only test with one type of request  
❌ Assume files are correct without opening them  
❌ Ignore console warnings  
❌ Skip edge case testing  
❌ Forget to check historical accuracy  

---

## Test Results Template

```markdown
## Test Results - [Date]

### Environment
- Python version: 
- Dependencies: discord.py, python-pptx, python-docx, openai
- LLM provider: 

### Test Case Results

| Test Case | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Valid history request | Approved + files | | |
| Invalid non-history | Rejected with message | | |
| 3-lesson request | 6 files (3 DOCX + 3 PPTX) | | |
| DOCX content | Continuous text, 30 sections | | |
| PPTX content | 31 slides (1 title + 30 content) | | |
| Request Reviewer standalone | All tests pass | | |

### Issues Found
1. [Description]
2. [Description]

### Notes
[Any additional observations]
```

---

## Automated Testing (Future Enhancement)

Consider adding:
- Unit tests for each agent
- Integration tests for full workflow
- Mocked LLM responses for consistent testing
- CI/CD pipeline with automated tests

---

**Happy Testing! 🧪**
