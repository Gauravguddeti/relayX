from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from loguru import logger
from shared.database import get_db, SupabaseDB

router = APIRouter()

# ==================== MODELS ====================

class KnowledgeCreate(BaseModel):
    agent_id: str
    title: str
    content: str
    source_file: Optional[str] = None
    source_url: Optional[str] = None  # New: URL source
    file_type: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class KnowledgeFromURL(BaseModel):
    agent_id: str
    url: str
    custom_title: Optional[str] = None  # Optional custom title override

# ==================== ROUTES ====================

@router.get("/api/agents/{agent_id}/knowledge")
async def get_agent_knowledge(agent_id: str, db: SupabaseDB = Depends(get_db)):
    """Get all knowledge base entries for an agent"""
    try:
        knowledge = await db.get_agent_knowledge(agent_id)
        return knowledge
    except Exception as e:
        logger.error(f"Error fetching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/knowledge")
async def add_knowledge(
    knowledge: KnowledgeCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Add knowledge base entry"""
    try:
        result = await db.add_knowledge(
            agent_id=knowledge.agent_id,
            title=knowledge.title,
            content=knowledge.content,
            source_file=knowledge.source_file,
            source_url=knowledge.source_url,
            file_type=knowledge.file_type,
            metadata=knowledge.metadata
        )
        return result
    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/knowledge/from-url")
async def add_knowledge_from_url(
    data: KnowledgeFromURL,
    db: SupabaseDB = Depends(get_db)
):
    """
    Scrape URL and add to knowledge base
    """
    try:
        from shared.url_scraper import scrape_url_for_knowledge
        
        logger.info(f"Scraping URL for agent {data.agent_id}: {data.url}")
        
        # Scrape the URL
        success, title, content, metadata = await scrape_url_for_knowledge(data.url)
        
        if not success:
            error_msg = metadata.get("error", "Failed to scrape URL")
            raise HTTPException(status_code=400, detail=f"Scraping failed: {error_msg}")
        
        # Use custom title if provided
        final_title = data.custom_title or title
        
        # Add URL to metadata
        metadata["scraped_url"] = data.url
        
        # Add to knowledge base
        result = await db.add_knowledge(
            agent_id=data.agent_id,
            title=final_title,
            content=content,
            source_url=data.url,
            file_type="url",
            metadata=metadata
        )
        
        logger.info(f"✅ Added knowledge from URL: {data.url} ({metadata.get('word_count', 0)} words)")
        
        return {
            "success": True,
            "knowledge": result,
            "scraped_data": {
                "url": data.url,
                "title": title,
                "word_count": metadata.get("word_count", 0),
                "domain": metadata.get("domain", "")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping URL {data.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/knowledge/preview-url")
async def preview_url(url: str):
    """
    Preview URL content before adding to knowledge base
    Returns: title, content preview, word count, domain
    """
    logger.info(f"Preview URL request: {url}")
    try:
        from shared.url_scraper import scrape_url_for_knowledge
        
        logger.info(f"Starting scrape for: {url}")
        success, title, content, metadata = await scrape_url_for_knowledge(url)
        
        logger.info(f"Scrape result - Success: {success}, Error: {metadata.get('error', 'None')}")
        
        if not success:
            error_msg = metadata.get("error", "Failed to scrape URL")
            logger.error(f"Scrape failed: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
            
        return {
            "title": title,
            "content_preview": content[:500] + "..." if len(content) > 500 else content,
            "word_count": metadata.get("word_count", 0),
            "domain": metadata.get("domain", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing URL {url}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
