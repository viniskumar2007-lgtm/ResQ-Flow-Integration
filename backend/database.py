from supabase import create_client, Client

from config import (
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY,
    SUPABASE_SECRET_KEY
)


# Client for normal Supabase operations
supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
)


# Server-side client for trusted backend operations
supabase_admin: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SECRET_KEY
)


def test_database_connection():
    response = supabase_admin.table("profiles").select("*").limit(1).execute()
    return response.data