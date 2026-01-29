"""
Pydantic schemas for strict data validation.
Defines the structure of AI-generated report data.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Sentiment(BaseModel):
    """Sentiment analysis result."""
    label: str = Field(..., description="Sentiment label (e.g., 'positive', 'neutral', 'negative')")
    score: int = Field(..., ge=1, le=5, description="Sentiment score from 1 to 5")


class ReportData(BaseModel):
    """Main report data structure returned by AI."""
    client_name: str = Field(..., description="Name of the client")
    topic: str = Field(..., description="Main topic of the conversation")
    main_request: str = Field(..., description="Primary request or need of the client")
    sentiment: Sentiment = Field(..., description="Overall sentiment of the conversation")
    summary: str = Field(..., description="Brief summary of the dialogue")
    key_points: List[str] = Field(..., description="List of key points discussed")
    next_steps: List[str] = Field(..., description="Recommended next steps or action items")
    
    # Новые поля для бизнес-требований
    desired_timeline: Optional[str] = Field(None, description="Desired timeline/deadline mentioned by client")
    budget_range: Optional[str] = Field(None, description="Budget or cost expectations mentioned")
    core_requirements: List[str] = Field(default_factory=list, description="Core requirements - what MUST be in the final product")
    
    @field_validator('key_points', 'next_steps')
    @classmethod
    def validate_non_empty_list(cls, v):
        """Ensure lists are not empty."""
        if not v:
            raise ValueError("List cannot be empty")
        return v


class DesignBrief(BaseModel):
    """Design brief data structure returned by AI."""
    project_name: str = Field(..., description="Project name")
    business: str = Field(..., description="Business domain or type")
    site_goal: str = Field(..., description="Primary goal of the site")
    target_audience: List[str] = Field(..., description="Target audience segments")
    pages: List[str] = Field(..., description="List of required pages")
    style_keywords: List[str] = Field(..., description="Style keywords for design direction")
    colors: List[str] = Field(..., description="Preferred or reference colors")
    must_have: List[str] = Field(..., description="Must-have features or sections")
    avoid: List[str] = Field(..., description="Things to avoid in design")
    content_notes: Optional[str] = Field(None, description="Additional content notes")


# JSON schema for AI prompt
REPORT_SCHEMA_DESCRIPTION = """
{
  "client_name": "string - name of the client",
  "topic": "string - main topic of conversation",
  "main_request": "string - primary request or need",
  "sentiment": {
    "label": "string - sentiment label (positive/neutral/negative)",
    "score": "integer 1-5 - sentiment score"
  },
  "summary": "string - brief summary of the dialogue",
  "key_points": ["string", "string", ...] - list of key points,
  "next_steps": ["string", "string", ...] - recommended action items,
  "desired_timeline": "string or null - desired deadline/timeline if mentioned (e.g., '2 months', 'before inventory')",
  "budget_range": "string or null - budget or cost expectations if mentioned (e.g., 'limited budget', 'cloud pricing')",
  "core_requirements": ["string", "string", ...] - list of core features/requirements that MUST be in final product (can be empty list if none mentioned)
}
"""

DESIGN_BRIEF_SCHEMA_DESCRIPTION = """
{
  "project_name": "string - project name",
  "business": "string - business domain or type",
  "site_goal": "string - primary goal of the site",
  "target_audience": ["string", "string", ...] - target audience segments,
  "pages": ["string", "string", ...] - list of required pages,
  "style_keywords": ["string", "string", ...] - style keywords for design direction,
  "colors": ["string", "string", ...] - preferred or reference colors,
  "must_have": ["string", "string", ...] - must-have features or sections,
  "avoid": ["string", "string", ...] - things to avoid in design,
  "content_notes": "string or null - additional content notes"
}
"""
