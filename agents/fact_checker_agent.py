# agents/fact_checker_agent.py
"""
FACT-CHECKER AGENT
==================
RESPONSIBILITY: Validates content accuracy against source evidence.

PURPOSE:
- Ensures generated content is factually supported by research evidence
- Provides quality assurance for historical accuracy
- Prevents hallucinations and unsupported claims

PROCESS:
1. Receives text to verify (from Worker or Planner)
2. Receives evidence (Wikipedia summaries, historical sources)
3. Uses LLM to compare text against evidence
4. Returns verdict: GO/NO-GO with confidence level
5. Provides corrections when content is unsupported

OUTPUT FORMAT:
- GO/NO-GO verdict
- Confidence level (High/Medium/Low)
- Reason for verdict
- Corrected version if needed

USAGE:
- Called during content generation pipeline
- Ensures historical accuracy before final output
- Currently integrated but can be used more extensively
"""

from utils.llm import generate

async def fact_checker_agent(text_to_check: str, evidence: str) -> str:
    """
    Fact-Checker Agent:
    - Receives text produced by Worker
    - Receives evidence (e.g., Wikipedia summary output)
    - Uses LLM to assess if the text is supported by the evidence
    - Returns a verdict + optional corrected version
    """

    # If no evidence exists yet, we still return a cautious verdict
    if not evidence or len(evidence.strip()) < 20:
        return (
            "⚠️ Fact-Checker: No evidence provided yet, cannot verify reliably.\n"
            "Verdict: UNKNOWN\n"
            "Notes: Retrieve evidence first (e.g., Wikipedia) to enable verification."
        )

    prompt = f"""
You are a strict fact-checking agent.

Your job:
1) Evaluate whether the "TEXT TO CHECK" is supported by the "EVIDENCE".
2) Output a verdict: GO or NO-GO
3) If anything is not supported, provide a corrected version using ONLY the evidence.

Rules:
- Use ONLY the evidence. If something is not in the evidence, mark it unsupported.
- Be concise.
- Output format EXACTLY:
GO/NO-GO: <GO|NO-GO>
Confidence: <High|Medium|Low>
Reason: <one sentence>
Corrected version (if NO-GO):
<text or N/A>

EVIDENCE:
{evidence}

TEXT TO CHECK:
{text_to_check}
""".strip()

    result = await generate(prompt)
    return f"🛡️ Fact-Checker Result:\n{result}"
