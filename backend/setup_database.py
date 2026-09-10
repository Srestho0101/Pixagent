import os
from dotenv import load_dotenv
from supabase import create_client
from passlib.context import CryptContext

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_database():
    url = os.getenv("SUPABASE_URL")
    # Prefer service role, fallback to anon (but you may want to remove fallback)
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Supabase credentials not found in .env file")
        return
    
    # Debug
    is_service = key == os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    print(f"Using {'SERVICE ROLE' if is_service else 'ANON'} key")
    
    client = create_client(url, key)
    
    test_technician = {
        "email": "tech@example.com",
        "name": "Test Technician",
        "password_hash": pwd_context.hash("password123")
    }
    
    try:
        existing = client.table("technicians").select("*").eq("email", test_technician["email"]).execute()
        if existing.data:
            print(f"Technician already exists: {test_technician['email']}")
        else:
            result = client.table("technicians").insert(test_technician).execute()
            print(f"✅ Created test technician: {test_technician['email']}")
            print("Login credentials: email=tech@example.com, password=password123")
    except Exception as e:
        print(f"❌ Error setting up database: {e}")

if __name__ == "__main__":
    setup_database()