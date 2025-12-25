import sys
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()
sys.path.append(os.path.dirname(__file__))
from shared.database import SupabaseDB

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def main():
    db = SupabaseDB()
    
    # Check if user exists
    result = db.client.table("users").select("*").eq("email", "test@relayx.ai").execute()
    
    if result.data:
        print("User already exists:")
        print(f"ID: {result.data[0]['id']}")
        print(f"Email: {result.data[0]['email']}")
        print(f"Name: {result.data[0].get('name', 'N/A')}")
        
        # Update password
        password_hash = hash_password("test123")
        update_result = db.client.table("users").update({
            "password_hash": password_hash
        }).eq("email", "test@relayx.ai").execute()
        
        print("\n✅ Password updated to: test123")
    else:
        print("User does not exist. Creating...")
        
        # Create user
        password_hash = hash_password("test123")
        user_data = {
            "email": "test@relayx.ai",
            "password_hash": password_hash,
            "name": "Test User",
            "company": "RelayX Demo"
        }
        
        result = db.client.table("users").insert(user_data).execute()
        print("\n✅ User created successfully!")
        print(f"ID: {result.data[0]['id']}")
        print(f"Email: {result.data[0]['email']}")
        print(f"Password: test123")

if __name__ == "__main__":
    main()
