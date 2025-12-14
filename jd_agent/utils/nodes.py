from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from jd_agent.utils.logger import log_state, log_update
from jd_agent.utils.validators import (
    ValidationNodeOutput,
    DraftNodeOutput,
    QualityCheckOutput,
    RewriteNodeOutput,
    ReviewNodeOutput,
    FinalOutputNodeOutput
)
import re
import json

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)


# ---------------------------------------------------------------
# 1. VALIDATION NODE
# ---------------------------------------------------------------
def validation_node(state):
    print("\n========== [VALIDATION NODE] ==========\n")
    log_state("VALIDATION NODE (START)", state)

    system_prompt = """
    You are a job description input validator.
    
    TASK:
    1. Check if required fields are present:
       - Job Title (mandatory)
       - Client/Company Name (mandatory)
       - Experience (recommended)
       - Skills (recommended)
    
    2. Normalize the input by:
       - Structuring the data clearly
       - Filling in defaults where appropriate
       - Correcting obvious typos
       - Ensuring consistency
    
    3. Respond with:
       - "VALID" if all required fields present
       - "INVALID: <reason>" if critical fields missing
    
    Then provide the normalized input in a structured format.
    
    Format your response as:
    VALIDATION: <VALID or INVALID: reason>
    
    NORMALIZED INPUT:
    <structured input>
    """

    result = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User Input:\n{state.user_input}")
    ])

    content = result.content
    
    # Parse validation result
    if "VALIDATION:" in content:
        parts = content.split("NORMALIZED INPUT:", 1)
        validation_line = parts[0].replace("VALIDATION:", "").strip()
        normalized = parts[1].strip() if len(parts) > 1 else state.user_input
    else:
        validation_line = "VALID"
        normalized = content

    validated = ValidationNodeOutput(
        validation_result=validation_line,
        normalized_input=normalized
    )
    
    updates = validated.model_dump()
    log_update("VALIDATION NODE (END)", updates)
    return updates


# ---------------------------------------------------------------
# 2. DRAFT NODE
# ---------------------------------------------------------------
def draft_node(state):
    print("\n========== [DRAFT NODE] ==========\n")
    log_state("DRAFT NODE (START)", state)

    system_prompt = """
    You are an expert HR Job Description writer.
    
    TASK:
    Create a FIRST DRAFT of a professional job description with these sections:
    
    1. **Job Title and Metadata** (Job ID, Work Mode, Location, etc.)
    2. **About Us** (2-3 paragraphs about the company)
    3. **Job Summary** (Brief overview of the role)
    4. **Key Responsibilities** (5-8 bullet points)
    5. **Required Skills** (Technical and soft skills)
    6. **Preferred Qualifications** (Nice-to-have)
    7. **Education** (Educational requirements)
    8. **Experience** (Experience requirements)
    
    IMPORTANT:
    - Use the normalized input provided
    - Keep it professional and clear
    - Make it realistic and achievable
    - Use action verbs for responsibilities
    - Be specific about requirements
    - No generic fluff or buzzwords
    """

    result = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Normalized Input:\n{state.normalized_input}")
    ])

    validated = DraftNodeOutput(draft=result.content)
    updates = validated.model_dump()

    log_update("DRAFT NODE (END)", updates)
    return updates


# ---------------------------------------------------------------
# 3. QUALITY CHECK NODE
# ---------------------------------------------------------------
def quality_check_node(state):
    print("\n========== [QUALITY CHECK NODE] ==========\n")
    log_state("QUALITY CHECK NODE (START)", state)

    system_prompt = """
    You are a job description quality evaluator.
    
    TASK:
    Evaluate the draft JD based on these criteria:
    
    1. **Structure** (30 points): All required sections present and well-organized
    2. **Tone** (25 points): Professional, inclusive, engaging
    3. **Realism** (25 points): Requirements are realistic, not overstuffed
    4. **Clarity** (20 points): Clear, concise, no jargon overload
    
    SCORING:
    - 85-100: Excellent (PASS)
    - 70-84: Good but needs minor improvements (PASS)
    - Below 70: Needs rewrite (FAIL)
    
    Respond ONLY with valid JSON:
    {
      "score": 85,
      "structure_score": 28,
      "tone_score": 23,
      "realism_score": 22,
      "clarity_score": 18,
      "pass": true,
      "issues": ["Issue 1", "Issue 2"]
    }
    
    NO markdown, NO backticks, NO extra text.
    """

    result = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Draft JD:\n{state.draft}")
    ])

    # Clean JSON response
    content = result.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()

    validated = QualityCheckOutput(quality_check=content)
    updates = validated.model_dump()

    log_update("QUALITY CHECK NODE (END)", updates)
    return updates


# ---------------------------------------------------------------
# 4. REWRITE NODE
# ---------------------------------------------------------------
def rewrite_node(state):
    print("\n========== [REWRITE NODE] ==========\n")
    log_state("REWRITE NODE (START)", state)

    system_prompt = """
    You are a job description improvement specialist.
    
    TASK:
    Rewrite the draft to address all identified issues:
    - Fix structural problems
    - Improve tone and inclusivity
    - Make requirements more realistic
    - Enhance clarity and remove jargon
    
    Keep the same overall content but improve quality significantly.
    Maintain all necessary sections.
    """

    result = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Current Draft:\n{state.draft}"),
        HumanMessage(content=f"Quality Check Result:\n{state.quality_check}"),
        HumanMessage(content=f"Original Input:\n{state.normalized_input}")
    ])

    validated = RewriteNodeOutput(
        draft=result.content,
        rewrite_attempts=state.rewrite_attempts + 1
    )

    updates = validated.model_dump()
    log_update("REWRITE NODE (END)", updates)
    return updates


# ---------------------------------------------------------------
# 5. REVIEW NODE
# ---------------------------------------------------------------
def review_node(state):
    print("\n========== [REVIEW NODE] ==========\n")
    log_state("REVIEW NODE (START)", state)

    system_prompt = """
    You are a senior HR reviewer specializing in ATS optimization.
    
    TASK:
    Polish the job description for final release:
    
    1. **ATS Optimization**:
       - Use standard section headings
       - Include relevant keywords naturally
       - Avoid tables, columns, graphics (text-only)
       - Use standard bullet points
    
    2. **Consistency Check**:
       - Remove any contradictions
       - Ensure tone is consistent
       - Verify all sections align
    
    3. **Final Polish**:
       - Fix any grammatical issues
       - Improve readability
       - Remove redundancy
       - Strengthen weak phrases
    
    Maintain the structure and content, just polish and optimize.
    """

    result = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Draft to Review:\n{state.draft}")
    ])

    validated = ReviewNodeOutput(reviewed=result.content)
    updates = validated.model_dump()

    log_update("REVIEW NODE (END)", updates)
    return updates


# ---------------------------------------------------------------
# 6. FINAL OUTPUT NODE
# ---------------------------------------------------------------
def final_output_node(state):
    print("\n========== [FINAL OUTPUT NODE] ==========\n")
    log_state("FINAL OUTPUT NODE (START)", state)

    # 1. Generate Markdown version
    markdown_prompt = """
    Format the reviewed job description in clean Markdown:
    - Use proper heading levels (## for sections)
    - Use bullet points (- or *) for lists
    - Use **bold** for emphasis
    - Keep it clean and readable
    """

    markdown_result = llm.invoke([
        SystemMessage(content=markdown_prompt),
        HumanMessage(content=state.reviewed)
    ])

    # 2. Generate JSON version
    json_prompt = """
    Convert the job description into structured JSON format:
    {
      "job_title": "...",
      "job_id": "...",
      "company": "...",
      "location": "...",
      "work_mode": "...",
      "employment_type": "...",
      "about_us": "...",
      "summary": "...",
      "responsibilities": ["...", "..."],
      "required_skills": ["...", "..."],
      "preferred_qualifications": ["...", "..."],
      "education": "...",
      "experience": "..."
    }
    
    Respond ONLY with valid JSON.
    """

    json_result = llm.invoke([
        SystemMessage(content=json_prompt),
        HumanMessage(content=state.reviewed)
    ])

    # Clean JSON
    json_content = json_result.content.strip()
    if json_content.startswith("```"):
        json_content = json_content.split("```")[1]
        if json_content.startswith("json"):
            json_content = json_content[4:]
    json_content = json_content.strip()

    # 3. Generate plain text version
    text_prompt = """
    Convert the job description to plain text format:
    - No markdown formatting
    - Use line breaks for readability
    - Use simple dashes for lists
    - Keep it clean and printable
    """

    text_result = llm.invoke([
        SystemMessage(content=text_prompt),
        HumanMessage(content=state.reviewed)
    ])

    validated = FinalOutputNodeOutput(
        final_markdown=markdown_result.content,
        final_json=json_content,
        final_text=text_result.content
    )

    updates = validated.model_dump()
    log_update("FINAL OUTPUT NODE (END)", updates)
    return updates