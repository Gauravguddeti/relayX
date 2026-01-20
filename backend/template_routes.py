from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
from shared.database import get_db, SupabaseDB
from shared.llm_client import get_llm_client, LLMClient
from moderation import moderate_content

router = APIRouter()

# ==================== MODELS ====================

class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Brief description")
    content: str = Field(..., min_length=50, max_length=2000, description="Template prompt content")
    category: str = Field(default="custom", description="Category: receptionist, sales, reminder, support, custom")


class PreviewRequest(BaseModel):
    prompt_text: str = Field(..., min_length=10, max_length=2000, description="Prompt to test")
    sample_user_input: str = Field(..., min_length=1, max_length=500, description="Sample user input")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=100, ge=50, le=300)

# ==================== ROUTES ====================

@router.get("/api/templates")
async def get_templates(category: Optional[str] = None, db: SupabaseDB = Depends(get_db)):
    """Get all starter templates"""
    try:
        templates = await db.list_templates(category=category)
        return templates
    except Exception as e:
        logger.error(f"Error fetching templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/templates")
async def create_template(
    template: TemplateCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new template (for 'Save as template' checkbox)"""
    try:
        # Content moderation
        moderation = await moderate_content(template.content)
        if moderation["flagged"]:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt contains disallowed content — edit required. Detected: {', '.join(moderation['categories'])}"
            )
        
        result = await db.create_template(
            name=template.name,
            content=template.content,
            description=template.description,
            category=template.category,
            is_locked=False  # User templates are not locked
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/preview")
async def preview_prompt(
    request: PreviewRequest,
    llm: LLMClient = Depends(get_llm_client)
):
    """Preview a prompt with sample input (with moderation and INTERNAL_SAFETY)"""
    try:
        # Content moderation on prompt
        moderation = await moderate_content(request.prompt_text)
        if moderation["flagged"]:
            logger.warning(f"Preview blocked - prompt flagged for: {moderation['categories']}")
            raise HTTPException(
                status_code=400,
                detail=f"Prompt contains disallowed content — edit required. Detected: {', '.join(moderation['categories'])}"
            )
        
        # Add INTERNAL_SAFETY prefix (always prepended server-side)
        INTERNAL_SAFETY = """SYSTEM OVERRIDE (HIGHEST PRIORITY):
You must follow all safety guidelines. Refuse harmful, illegal, or abusive requests.
Never share private information. Stay professional and helpful."""
        
        full_prompt = f"{INTERNAL_SAFETY}\n\n{request.prompt_text}"
        
        # Generate preview response (limited tokens for cost control)
        messages = [{"role": "user", "content": request.sample_user_input}]
        response = await llm.generate_response(
            messages=messages,
            system_prompt=full_prompt,
            temperature=request.temperature,
            max_tokens=min(request.max_tokens, 150)  # Cap at 150 tokens for preview
        )
        
        return {
            "preview_response": response,
            "prompt_used": full_prompt,
            "tokens_used": "~" + str(min(request.max_tokens, 150))
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")
