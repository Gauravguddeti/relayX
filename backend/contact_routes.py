"""
Contact management routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import csv
import io
from loguru import logger

from shared.database import SupabaseDB
from auth import get_current_user_id

router = APIRouter(prefix="/contacts", tags=["contacts"])

# ============================================================================
# Models
# ============================================================================

class Contact(BaseModel):
    id: Optional[str] = None
    user_id: str
    name: str
    phone: str
    email: Optional[str] = None
    company: Optional[str] = None

class ContactResponse(BaseModel):
    contacts: List[dict]
    total: int

# ============================================================================
# Database dependency
# ============================================================================

# This will be injected from main.py
supabase_db = None

def get_db():
    if not supabase_db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return supabase_db

def init_db(db: SupabaseDB):
    global supabase_db
    supabase_db = db

# ============================================================================
# Routes
# ============================================================================

@router.get("")
async def get_contacts(
    user_id: str,
    current_user: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Get all contacts for a user"""
    try:
        # Verify user can only access their own contacts
        if user_id != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        result = db.client.table("contacts").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        contacts = result.data or []
        
        return {
            "contacts": contacts,
            "total": len(contacts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_contact(
    contact: Contact,
    current_user: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Create a new contact"""
    try:
        # Verify user can only create contacts for themselves
        if contact.user_id != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if contact already exists
        existing = db.client.table("contacts").select("id").eq("user_id", contact.user_id).eq("phone", contact.phone).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Contact with this phone number already exists")

        # Create contact
        contact_data = contact.dict(exclude_none=True)
        result = db.client.table("contacts").insert(contact_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create contact")
        
        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_contacts(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    current_user: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Upload contacts from CSV file"""
    try:
        # Verify user can only upload contacts for themselves
        if user_id != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Read CSV file
        content = await file.read()
        csv_text = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        
        contacts_to_add = []
        errors = []
        
        # Get existing phones to avoid duplicates
        existing_result = db.client.table("contacts").select("phone").eq("user_id", user_id).execute()
        existing_phones = {c['phone'] for c in (existing_result.data or [])}
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Required field
                if 'phone' not in row or not row['phone']:
                    errors.append(f"Row {row_num}: Missing phone number")
                    continue
                
                phone = row['phone'].strip()
                
                # Skip if already exists
                if phone in existing_phones:
                    continue
                
                # Get name (required)
                name = row.get('name', '').strip()
                if not name:
                    errors.append(f"Row {row_num}: Missing name")
                    continue
                
                contact_data = {
                    'user_id': user_id,
                    'name': name,
                    'phone': phone,
                    'email': row.get('email', '').strip() or None,
                    'company': row.get('company', '').strip() or None
                }
                
                contacts_to_add.append(contact_data)
                existing_phones.add(phone)  # Mark as added to avoid duplicates within CSV
                
            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
        
        # Insert contacts
        added_count = 0
        if contacts_to_add:
            result = db.client.table("contacts").insert(contacts_to_add).execute()
            added_count = len(result.data) if result.data else 0
        
        logger.info(f"Uploaded {added_count} contacts for user {user_id}")
        
        return {
            "added_count": added_count,
            "skipped_duplicates": len(csv_text.splitlines()) - 1 - len(errors) - added_count,
            "errors": errors
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: str = Depends(get_current_user_id),
    db: SupabaseDB = Depends(get_db)
):
    """Delete a contact"""
    try:
        # Verify contact belongs to user
        result = db.client.table("contacts").select("user_id").eq("id", contact_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        if result.data[0]['user_id'] != current_user:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete contact
        db.client.table("contacts").delete().eq("id", contact_id).execute()
        
        logger.info(f"Deleted contact {contact_id} for user {current_user}")
        
        return {"message": "Contact deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))
