from langgraph.graph import StateGraph, START, END
from jd_agent.utils.state import JDState
from jd_agent.utils.nodes import (
    validation_node,
    draft_node,
    quality_check_node,
    rewrite_node,
    review_node,
    final_output_node
)
import json


def should_proceed_after_validation(state: JDState):
    """
    Route after validation.
    Returns:
        "draft" - if input is valid
        "end" - if input is invalid
    """
    if state.validation_result and state.validation_result.upper().startswith("VALID"):
        print("✅ Input validated successfully. Proceeding to draft.")
        return "draft"
    else:
        print(f"❌ Validation failed: {state.validation_result}")
        print("⛔ Ending workflow due to invalid input.")
        return "end"


def should_rewrite_or_review(state: JDState):
    """
    Route after quality check.
    Returns:
        "rewrite" - if quality check fails and attempts < 3
        "review" - if quality check passes or max attempts reached
    """
    
    # Prevent infinite loops
    if state.rewrite_attempts >= 3:
        print("⚠️ MAX REWRITE ATTEMPTS (3) REACHED — Proceeding to review.")
        return "review"
    
    try:
        # Clean and parse JSON
        check_content = state.quality_check.strip()
        
        if check_content.startswith("```"):
            lines = check_content.split("```")
            if len(lines) >= 2:
                check_content = lines[1]
                if check_content.startswith("json"):
                    check_content = check_content[4:]
        
        check_content = check_content.strip()
        check = json.loads(check_content)
        
        score = check.get("score", 0)
        passes = check.get("pass", False)
        issues = check.get("issues", [])
        
        print(f"\n📊 Quality Check Results:")
        print(f"   Score: {score}/100")
        print(f"   Structure: {check.get('structure_score', 0)}/30")
        print(f"   Tone: {check.get('tone_score', 0)}/25")
        print(f"   Realism: {check.get('realism_score', 0)}/25")
        print(f"   Clarity: {check.get('clarity_score', 0)}/20")
        
        if passes:
            print("✅ Quality check PASSED. Proceeding to review.")
            return "review"
        else:
            print(f"❌ Quality check FAILED. Issues: {', '.join(issues)}")
            print(f"🔄 Rewrite attempt {state.rewrite_attempts + 1}/3")
            return "rewrite"
            
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse quality_check JSON: {e}")
        print(f"Raw content (first 200 chars): {state.quality_check[:200]}")
        
        # Default: rewrite on first attempt, review after
        if state.rewrite_attempts < 1:
            print("🔄 Attempting rewrite due to parse error")
            return "rewrite"
        else:
            print("⚠️ Parse error on retry - proceeding to review")
            return "review"
            
    except Exception as e:
        print(f"⚠️ Unexpected error in routing: {e}")
        return "review"


def build_agent():
    """Build the LangGraph agent with the new flow."""
    
    graph = StateGraph(JDState)

    # Add nodes
    graph.add_node("validation", validation_node)
    graph.add_node("draft", draft_node)
    graph.add_node("quality_check", quality_check_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("review", review_node)
    graph.add_node("final_output", final_output_node)

    # Flow: START -> Validation
    graph.add_edge(START, "validation")

    # Conditional: Validation -> Draft or END
    graph.add_conditional_edges(
        "validation",
        should_proceed_after_validation,
        {
            "draft": "draft",
            "end": END
        }
    )

    # Flow: Draft -> Quality Check
    graph.add_edge("draft", "quality_check")

    # Conditional: Quality Check -> Rewrite or Review
    graph.add_conditional_edges(
        "quality_check",
        should_rewrite_or_review,
        {
            "rewrite": "rewrite",
            "review": "review"
        }
    )

    # Flow: Rewrite -> Quality Check (loop back)
    graph.add_edge("rewrite", "quality_check")

    # Flow: Review -> Final Output -> END
    graph.add_edge("review", "final_output")
    graph.add_edge("final_output", END)

    return graph.compile()


# Create the agent instance
agent = build_agent()