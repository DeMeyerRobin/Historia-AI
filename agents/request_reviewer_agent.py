# agents/request_reviewer_agent.py
"""
REQUEST REVIEWER AGENT
======================
RESPONSIBILITY: Gate-keeper that validates incoming user requests.

PURPOSE:
- Determines if a request is related to history topics
- Rejects non-history requests with a helpful message
- Approves history-related requests for further processing

This agent ensures the system only processes history-related queries,
preventing misuse and maintaining focus on educational history content.
"""

from utils.llm import generate


def is_history_related(request: str) -> tuple[bool, str]:
    """
    Analyzes a user request to determine if it's history-related.
    
    Args:
        request: The user's input request/query
        
    Returns:
        tuple: (is_valid, message)
            - is_valid: True if history-related, False otherwise
            - message: Explanation or approval message
    """
    
    prompt = f"""
You are a strict request validator for a history education system.

Your job is to determine if the following request is related to HISTORY topics.

ALLOWED topics:
- Historical events, periods, civilizations, wars, revolutions
- Historical figures, leaders, monarchs, explorers
- Cultural history, social movements, political developments
- Ancient, medieval, modern, or contemporary history
- Any educational content about past events and their significance

FORBIDDEN topics:
- Current events or news (after 2024)
- Science (unless historical science topics like "History of Scientific Revolution")
- Mathematics, programming, technology (unless history of these fields)
- Entertainment, games, sports (unless their history)
- General knowledge unrelated to history
- Personal questions or advice

REQUEST TO EVALUATE:
"{request}"

Respond in this EXACT format:
VERDICT: APPROVED or REJECTED
REASON: <one clear sentence explaining your decision>

If the request mentions creating lessons, presentations, or studying a historical topic, APPROVE it.
If it asks about non-history topics or current events, REJECT it.
""".strip()
    
    response = generate(prompt, temperature=0.2, max_tokens=150)
    
    # Parse the response
    lines = response.strip().split('\n')
    verdict_line = ""
    reason_line = ""
    
    for line in lines:
        line = line.strip()
        if line.upper().startswith("VERDICT:"):
            verdict_line = line
        elif line.upper().startswith("REASON:"):
            reason_line = line
    
    # Determine if approved
    is_approved = "APPROVED" in verdict_line.upper()
    
    # Extract reason
    if reason_line:
        reason = reason_line.split(":", 1)[1].strip() if ":" in reason_line else reason_line
    else:
        reason = "No reason provided"
    
    if is_approved:
        return True, f"✅ Request approved: {reason}"
    else:
        rejection_message = f"""
❌ **Request Rejected: Not History-Related**

{reason}

**This system only processes history-related educational content.**

Examples of valid requests:
- "Create 3 lessons on the French Revolution"
- "Teach me about Ancient Egypt"
- "Make a presentation on World War II"
- "Explain the Renaissance period"

Please reformulate your request to focus on a historical topic.
""".strip()
        return False, rejection_message


async def review_request(request: str) -> dict:
    """
    Async wrapper for request review.
    
    Returns:
        dict with keys:
            - approved: bool
            - message: str
            - original_request: str
    """
    is_valid, message = is_history_related(request)
    
    return {
        "approved": is_valid,
        "message": message,
        "original_request": request
    }


if __name__ == "__main__":
    # Test cases
    test_requests = [
        "Create 3 lessons on the French Revolution",
        "What's the weather today?",
        "Teach me about Ancient Rome",
        "Write a Python function to sort a list",
        "Explain World War II",
        "What's the best pizza place nearby?",
        "Make a presentation on the Industrial Revolution"
    ]
    
    print("Testing Request Reviewer Agent\n" + "="*50)
    for req in test_requests:
        print(f"\nRequest: {req}")
        is_valid, msg = is_history_related(req)
        print(f"Valid: {is_valid}")
        print(f"Message: {msg[:100]}...")
