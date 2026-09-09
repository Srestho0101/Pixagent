import os
from dotenv import load_dotenv
from supabase import create_client
from passlib.context import CryptContext

load_dotenv()

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def setup_database():
    """Initialize database with test data"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: Supabase credentials not found in .env file")
        return
    
    client = create_client(url, key)
    
    # Create test technician
    test_technician = {
        "email": "tech@example.com",
        "name": "Test Technician",
        "password_hash": pwd_context.hash("password123")
    }
    
    try:
        # Check if technician already exists
        existing = client.table("technicians").select("*").eq("email", test_technician["email"]).execute()
        
        if existing.data and len(existing.data) > 0:
            print(f"Technician already exists: {test_technician['email']}")
        else:
            result = client.table("technicians").insert(test_technician).execute()
            print(f"Created test technician: {test_technician['email']}")
            print("Login credentials: email=tech@example.com, password=password123")
    
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == "__main__":
    setup_database()