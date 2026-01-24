# agents/quizzer_agent.py
"""
QUIZZER AGENT
=============
RESPONSIBILITY: Generates age-appropriate quiz questions based on lesson content.

PURPOSE:
- Creates comprehension questions for two age groups (14 and 18 years)
- Ensures questions are answerable from the lesson material
- Provides variety in question types and difficulty

AGE GROUPS:
- 14 years: Basic factual recall questions (names, dates, events)
- 18 years: Analytical and critical thinking questions (causes, effects, analysis)

OUTPUT:
- Approximately 10 questions (5 per age group)
- Questions based on Teacher's Guide content
- Formatted for educational assessment
"""

from utils.llm import generate


def _quiz_generation_prompt(unit_title: str, lesson_summaries: str, age: int, num_questions: int = 10) -> str:
    """Generate prompt for creating quiz questions."""
    
    # Determine difficulty level based on age (14-18)
    if age <= 14:
        difficulty_desc = "basic factual recall"
        question_guidance = """
- Simple factual recall questions: names, dates, places, events
- Short answer format (1-2 sentences expected)
- Clear, direct questions with concrete answers
- Example: "What was the name of the treaty signed in 1951?"
- Example: "Who proposed the Schuman Declaration?"
- Example: "In what year did the European Union officially form?"""
    elif age <= 16:
        difficulty_desc = "moderate comprehension and basic analysis"
        question_guidance = """
- Mix of factual recall and basic comprehension
- Some questions require explanation of concepts
- Questions about key events and their immediate significance
- Example format: "What were the main goals of [specific event from lesson]?"
- Example format: "Why was [specific treaty/event] significant?"
- Example format: "Describe the impact of [specific event from lesson]."""
    else:  # 17-18
        difficulty_desc = "analytical and critical thinking"
        question_guidance = """
- Analytical and critical thinking questions
- Require explanation, comparison, or analysis
- Questions about causes, effects, significance, connections
- Example format: "Explain the main differences between [concept A] and [concept B] from the lesson."
- Example format: "Analyze how [event A] influenced [event B]."
- Example format: "Compare the goals of [two events/treaties from the lesson]."""
    
    return f"""
You are an expert history teacher creating a quiz for {age}-year-old students who have completed a lesson unit.

**Unit Title:** {unit_title}

**Lesson Content:**
{lesson_summaries}

Generate EXACTLY {num_questions} questions appropriate for {age}-year-old students ({difficulty_desc}).

**REQUIREMENTS FOR AGE {age}:**
{question_guidance}

**FORMAT:**
Return STRICT JSON:
{{
  "questions": [
    "Question 1?",
    "Question 2?",
    "Question 3?"
  ]
}}

**CRITICAL RULES:**
1. All questions MUST be answerable using ONLY the lesson content provided above
2. Do NOT ask about information not covered in the lessons
3. Do NOT use example topics from the prompt - use topics from the ACTUAL lesson content
4. Questions must test understanding of the actual material taught
5. Difficulty must be appropriate for {age}-year-old students
6. Generate EXACTLY {num_questions} questions
7. Use proper punctuation (question marks for questions or dots for statements)
8. VERIFY each question can be answered from the lesson content before including it
""".strip()


async def generate_quiz(unit_title: str, lesson_summaries: list[str], age: int) -> dict:
    """
    Generates age-appropriate quiz questions based on lesson content.
    
    Args:
        unit_title: The title of the unit/topic
        lesson_summaries: List of lesson summary texts
        age: Age of the students (14-18)
        
    Returns:
        dict with keys:
            - questions: List of questions for the specified age
            - age: The age group
    """
    # Validate age
    age = max(14, min(18, age))  # Clamp between 14-18
    
    # Combine lesson summaries
    combined_summaries = "\n\n=== LESSON ===\n\n".join(lesson_summaries)
    
    # Truncate if too long (to avoid token limits)
    if len(combined_summaries) > 4000:
        combined_summaries = combined_summaries[:4000] + "...\n[Content truncated for length]"
    
    print(f"[Quizzer] Generating quiz questions for {age}-year-olds: {unit_title}")
    
    # Generate questions
    prompt = _quiz_generation_prompt(unit_title, combined_summaries, age, num_questions=10)
    response = await generate(prompt, max_tokens=1500, temperature=0.5)
    
    # Parse JSON response
    import json
    import re
    
    # Try to extract JSON from response
    response = response.strip()
    match = re.search(r"```json\s*(.*?)\s*```", response, flags=re.DOTALL)
    if match:
        response = match.group(1)
    
    try:
        quiz_data = json.loads(response)
        
        questions = quiz_data.get("questions", [])
        
        # Validate we got questions
        if not questions:
            questions = ["Error: No questions generated"]
            
        return {
            "questions": questions,
            "age": age
        }
        
    except json.JSONDecodeError:
        print(f"[Quizzer] ERROR: Failed to parse quiz JSON. Raw: {response[:200]}...")
        return {
            "questions": ["Error generating quiz questions - check logs"],
            "age": age
        }


def format_quiz_for_docx(unit_title: str, quiz_data: dict) -> str:
    """
    Formats quiz questions as text for DOCX export.
    
    Args:
        unit_title: The title of the unit
        quiz_data: Dict containing questions and age
        
    Returns:
        Formatted text string ready for DOCX
    """
    age = quiz_data.get("age", 14)
    output = [
        f"QUIZ: {unit_title}",
        "=" * 60,
        "",
        f"Questions for Age {age} Students",
        "-" * 60,
        ""
    ]
    
    for i, q in enumerate(quiz_data.get("questions", []), 1):
        output.append(f"{i}. {q}")
        output.append("")
    
    return "\n".join(output)
