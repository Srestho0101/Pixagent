import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class Database:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        # Use service role key for server-side operations (bypasses RLS)
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        print(f"Connecting to Supabase with {'service role' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'anon'} key")
        self.client: Client = create_client(self.url, self.key)
    
    def get_client(self) -> Client:
        return self.client

# Singleton instance
db = Database()