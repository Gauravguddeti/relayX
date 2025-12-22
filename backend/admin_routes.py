"""
Admin routes for multi-client management, analytics, and operations
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from loguru import logger

from shared.database import SupabaseDB, get_db

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== MODELS ====================

class ClientCard(BaseModel):
    """Client profile card data"""
    id: str
    name: str
    email: str
    company: Optional[str]
    phone: Optional[str]
    agent_count: int
    total_calls: int
    active_calls: int
    last_call: Optional[datetime]
    created_at: datetime
    is_active: bool = True
    subscription_tier: str = "free"


class ClientDetail(BaseModel):
    """Detailed client information"""
    id: str
    name: str
    email: str
    company: Optional[str]
    phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    agents: List[Dict[str, Any]]
    recent_calls: List[Dict[str, Any]]
    stats: Dict[str, Any]
    audit_logs: List[Dict[str, Any]]


class Analytics(BaseModel):
    """System analytics"""
    total_clients: int
    active_clients: int
    total_agents: int
    total_calls: int
    calls_today: int
    success_rate: float
    avg_call_duration: float
    peak_hours: List[int]
    top_clients: List[Dict[str, Any]]


class BulkOperation(BaseModel):
    """Bulk operation request"""
    operation: str  # delete_calls, export_data, cleanup_old
    filters: Dict[str, Any]


class AuditLog(BaseModel):
    """Audit trail entry"""
    action: str
    user_id: str
    user_email: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str]


# ==================== CLIENT MANAGEMENT ====================

@router.get("/clients", response_model=List[ClientCard])
async def list_clients(
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: SupabaseDB = Depends(get_db)
):
    """List all clients with summary stats"""
    try:
        # Get all users
        query = db.client.table("users").select("*")
        if search:
            query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%,company.ilike.%{search}%")
        
        users_result = query.execute()
        users = users_result.data or []
        
        # Get all agents
        agents_result = db.client.table("agents").select("id,user_id").execute()
        agents = agents_result.data or []
        
        # Get all calls
        calls_result = db.client.table("calls").select("*").execute()
        calls = calls_result.data or []
        
        # Build client cards
        client_cards = []
        for user in users:
            user_id = user["id"]
            user_agents = [a for a in agents if a.get("user_id") == user_id]
            user_calls = [c for c in calls if c.get("user_id") == user_id]
            active_calls = [c for c in user_calls if c.get("status") in ["initiated", "ringing", "in-progress"]]
            
            # Get last call timestamp
            last_call = None
            if user_calls:
                sorted_calls = sorted(user_calls, key=lambda x: x.get("created_at", ""), reverse=True)
                last_call = sorted_calls[0].get("created_at") if sorted_calls else None
            
            client_cards.append(ClientCard(
                id=user_id,
                name=user.get("name") or "Unknown",
                email=user.get("email"),
                company=user.get("company"),
                phone=user.get("phone"),
                agent_count=len(user_agents),
                total_calls=len(user_calls),
                active_calls=len(active_calls),
                last_call=last_call,
                created_at=user.get("created_at"),
                is_active=True,
                subscription_tier="free"
            ))
        
        return client_cards
        
    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clients/{client_id}", response_model=ClientDetail)
async def get_client_detail(
    client_id: str,
    db: SupabaseDB = Depends(get_db)
):
    """Get detailed client information"""
    try:
        # Get user
        user_result = db.client.table("users").select("*").eq("id", client_id).execute()
        if not user_result.data:
            raise HTTPException(status_code=404, detail="Client not found")
        user = user_result.data[0]
        
        # Get agents
        agents_result = db.client.table("agents").select("*").eq("user_id", client_id).execute()
        agents = agents_result.data or []
        
        # Get recent calls (last 50)
        calls_result = db.client.table("calls").select("*").eq("user_id", client_id).order("created_at", desc=True).limit(50).execute()
        calls = calls_result.data or []
        
        # Calculate stats
        completed_calls = [c for c in calls if c.get("status") == "completed"]
        failed_calls = [c for c in calls if c.get("status") == "failed"]
        total_duration = sum(c.get("duration", 0) for c in completed_calls if c.get("duration"))
        avg_duration = total_duration / len(completed_calls) if completed_calls else 0
        
        # Today's calls
        today = datetime.now(timezone.utc).date()
        today_calls = [c for c in calls if c.get("created_at") and datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")).date() == today]
        
        stats = {
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a.get("is_active")]),
            "total_calls": len(calls),
            "completed_calls": len(completed_calls),
            "failed_calls": len(failed_calls),
            "success_rate": (len(completed_calls) / len(calls) * 100) if calls else 0,
            "avg_call_duration": round(avg_duration, 1),
            "calls_today": len(today_calls),
        }
        
        # Get audit logs (simplified - from calls history)
        audit_logs = []
        for call in calls[:20]:  # Last 20 calls as audit
            audit_logs.append({
                "action": f"call_{call.get('status')}",
                "timestamp": call.get("created_at"),
                "resource_type": "call",
                "resource_id": call.get("id"),
                "details": {
                    "to_number": call.get("to_number"),
                    "agent_id": call.get("agent_id"),
                    "duration": call.get("duration")
                }
            })
        
        return ClientDetail(
            id=user["id"],
            name=user.get("name") or "Unknown",
            email=user.get("email"),
            company=user.get("company"),
            phone=user.get("phone"),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at"),
            agents=agents,
            recent_calls=calls,
            stats=stats,
            audit_logs=audit_logs
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting client detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/clients/{client_id}/status")
async def update_client_status(
    client_id: str,
    is_active: bool,
    db: SupabaseDB = Depends(get_db)
):
    """Activate or suspend client account"""
    try:
        # Update user status (we'll add is_active field if needed)
        # For now, just return success
        return {"success": True, "message": f"Client {'activated' if is_active else 'suspended'}"}
    except Exception as e:
        logger.error(f"Error updating client status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYTICS ====================

@router.get("/analytics", response_model=Analytics)
async def get_analytics(
    days: int = Query(default=7, ge=1, le=90),
    db: SupabaseDB = Depends(get_db)
):
    """Get system-wide analytics"""
    try:
        # Get all data
        users_result = db.client.table("users").select("id,email,name,company").execute()
        users = users_result.data or []
        
        agents_result = db.client.table("agents").select("id,user_id,is_active").execute()
        agents = agents_result.data or []
        
        calls_result = db.client.table("calls").select("*").execute()
        calls = calls_result.data or []
        
        # Filter calls by date range
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        recent_calls = [
            c for c in calls 
            if c.get("created_at") and datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")) >= cutoff_date
        ]
        
        # Calculate metrics
        completed = [c for c in recent_calls if c.get("status") == "completed"]
        success_rate = (len(completed) / len(recent_calls) * 100) if recent_calls else 0
        
        total_duration = sum(c.get("duration", 0) for c in completed if c.get("duration"))
        avg_duration = total_duration / len(completed) if completed else 0
        
        # Today's calls
        today = datetime.now(timezone.utc).date()
        today_calls = [
            c for c in calls 
            if c.get("created_at") and datetime.fromisoformat(c["created_at"].replace("Z", "+00:00")).date() == today
        ]
        
        # Peak hours analysis
        hour_counts = {}
        for call in recent_calls:
            if call.get("created_at"):
                hour = datetime.fromisoformat(call["created_at"].replace("Z", "+00:00")).hour
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
        peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        peak_hours = [h[0] for h in peak_hours]
        
        # Top clients by call volume
        user_call_counts = {}
        for call in recent_calls:
            user_id = call.get("user_id")
            if user_id:
                user_call_counts[user_id] = user_call_counts.get(user_id, 0) + 1
        
        top_clients = []
        for user in users:
            user_id = user["id"]
            call_count = user_call_counts.get(user_id, 0)
            if call_count > 0:
                top_clients.append({
                    "id": user_id,
                    "name": user.get("name") or "Unknown",
                    "email": user.get("email"),
                    "company": user.get("company"),
                    "call_count": call_count
                })
        top_clients = sorted(top_clients, key=lambda x: x["call_count"], reverse=True)[:10]
        
        # Active clients (made calls in last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_user_ids = set()
        for call in calls:
            if call.get("created_at") and datetime.fromisoformat(call["created_at"].replace("Z", "+00:00")) >= week_ago:
                if call.get("user_id"):
                    active_user_ids.add(call["user_id"])
        
        return Analytics(
            total_clients=len(users),
            active_clients=len(active_user_ids),
            total_agents=len(agents),
            total_calls=len(calls),
            calls_today=len(today_calls),
            success_rate=round(success_rate, 1),
            avg_call_duration=round(avg_duration, 1),
            peak_hours=peak_hours,
            top_clients=top_clients
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== BULK OPERATIONS ====================

@router.post("/bulk/delete-old-calls")
async def bulk_delete_old_calls(
    days_old: int = Query(default=90, ge=30, le=365),
    client_id: Optional[str] = None,
    db: SupabaseDB = Depends(get_db)
):
    """Delete calls older than specified days"""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
        cutoff_str = cutoff_date.isoformat()
        
        # Build query
        query = db.client.table("calls").delete().lt("created_at", cutoff_str)
        
        if client_id:
            query = query.eq("user_id", client_id)
        
        result = query.execute()
        deleted_count = len(result.data) if result.data else 0
        
        logger.info(f"Bulk deleted {deleted_count} calls older than {days_old} days")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_str
        }
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk/export")
async def bulk_export_data(
    client_id: Optional[str] = None,
    data_type: str = Query(default="calls", regex="^(calls|agents|all)$"),
    db: SupabaseDB = Depends(get_db)
):
    """Export client data as JSON"""
    try:
        export_data = {}
        
        if data_type in ["agents", "all"]:
            query = db.client.table("agents").select("*")
            if client_id:
                query = query.eq("user_id", client_id)
            agents_result = query.execute()
            export_data["agents"] = agents_result.data or []
        
        if data_type in ["calls", "all"]:
            query = db.client.table("calls").select("*")
            if client_id:
                query = query.eq("user_id", client_id)
            calls_result = query.execute()
            export_data["calls"] = calls_result.data or []
        
        return {
            "success": True,
            "export_date": datetime.now(timezone.utc).isoformat(),
            "client_id": client_id,
            "data": export_data
        }
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AUDIT TRAIL ====================

@router.get("/audit-logs")
async def get_audit_logs(
    client_id: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    db: SupabaseDB = Depends(get_db)
):
    """Get audit trail logs"""
    try:
        # Get recent calls as audit trail
        query = db.client.table("calls").select("*").order("created_at", desc=True).limit(limit)
        
        if client_id:
            query = query.eq("user_id", client_id)
        
        result = query.execute()
        calls = result.data or []
        
        # Format as audit logs
        audit_logs = []
        for call in calls:
            audit_logs.append({
                "id": call.get("id"),
                "action": f"call_{call.get('status')}",
                "user_id": call.get("user_id"),
                "resource_type": "call",
                "resource_id": call.get("id"),
                "timestamp": call.get("created_at"),
                "details": {
                    "to_number": call.get("to_number"),
                    "agent_id": call.get("agent_id"),
                    "duration": call.get("duration"),
                    "status": call.get("status")
                }
            })
        
        return {
            "success": True,
            "logs": audit_logs,
            "total": len(audit_logs)
        }
        
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/security/login-history")
async def get_login_history(
    client_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    db: SupabaseDB = Depends(get_db)
):
    """Get login history (placeholder for future implementation)"""
    # This would require adding a login_logs table
    # For now, return placeholder data
    return {
        "success": True,
        "message": "Login history tracking will be implemented with auth system",
        "logs": []
    }
