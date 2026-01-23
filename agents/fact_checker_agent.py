# agents/fact_checker_agent.py
"""
FACT-CHECKER AGENT
==================
RESPONSIBILITY: Validates content accuracy against source evidence.

PURPOSE:
- Ensures generated content is factually supported by research evidence
- Uses LLM to verify content against Britannica/Wikipedia sources
- Provides quality assurance for historical accuracy
- Prevents hallucinations and unsupported claims

PROCESS:
1. Receives text to verify (from Planner)
2. Receives evidence (Britannica/Wikipedia summaries)
3. Uses LLM to compare text against evidence
4. Returns verdict with confidence level
5. Provides feedback on unsupported claims

OUTPUT FORMAT:
- GO/NO-GO verdict
- Confidence level (High/Medium/Low)
- Reason for verdict
- Warnings about unsupported content if needed

USAGE:
- Called during content generation pipeline
- Ensures historical accuracy before final output
"""

from utils.llm import generate

async def fact_checker_agent(text_to_check: str, evidence: str) -> str:
    """
    Fact-Checker Agent:
    - Receives text produced by content generation
    - Receives evidence (e.g., Britannica/Wikipedia summaries)
    - Uses LLM to assess if the text is supported by the evidence
    - Returns a verdict + feedback
    """

    # If no evidence exists yet, we still return a cautious verdict
    if not evidence or len(evidence.strip()) < 20:
        return (
            "⚠️ Fact-Checker: No evidence provided yet, cannot verify reliably.\n"
            "Verdict: UNKNOWN\n"
            "Notes: Retrieve evidence first (e.g., Britannica) to enable verification."
        )

    prompt = f"""
You are a strict fact-checking agent for educational content.

Your job:
1) Evaluate whether the "TEXT TO CHECK" is supported by the "EVIDENCE".
2) Output a verdict: GO or NO-GO
3) If parts are not supported, provide specific warnings.

Rules:
- Content should be based on or consistent with the evidence
- Historical facts (dates, names, events) must match the evidence
- Be reasonable: paraphrasing and educational expansion is acceptable
- Only flag content that contradicts the evidence or makes unsupported major claims
- Output format EXACTLY:

GO/NO-GO: <GO|NO-GO>
Confidence: <High|Medium|Low>
Reason: <one sentence explanation>
Warnings (if any): <specific issues or "None">

EVIDENCE:
{evidence}

TEXT TO CHECK:
{text_to_check}
""".strip()

    result = await generate(prompt, max_tokens=500)
    return f"🛡️ Fact-Checker Result:\n{result}"
