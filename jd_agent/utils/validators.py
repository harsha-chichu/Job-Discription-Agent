from pydantic import BaseModel, Field


class ValidationNodeOutput(BaseModel):
    """Output from validation_node"""
    validation_result: str = Field(description="'valid' or error message")
    normalized_input: str = Field(description="Normalized user input")


class DraftNodeOutput(BaseModel):
    """Output from draft_node"""
    draft: str = Field(description="First draft of job description")


class QualityCheckOutput(BaseModel):
    """Output from quality_check_node"""
    quality_check: str = Field(description="JSON with score, issues, and pass status")


class RewriteNodeOutput(BaseModel):
    """Output from rewrite_node"""
    draft: str = Field(description="Rewritten draft")
    rewrite_attempts: int = Field(description="Number of rewrite attempts")


class ReviewNodeOutput(BaseModel):
    """Output from review_node"""
    reviewed: str = Field(description="Polished and ATS-ready version")


class FinalOutputNodeOutput(BaseModel):
    """Output from final_output_node"""
    final_markdown: str = Field(description="Final JD in markdown")
    final_json: str = Field(description="Final JD in JSON")
    final_text: str = Field(description="Final JD in plain text")