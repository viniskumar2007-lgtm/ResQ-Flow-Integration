import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = (
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
)
SUPABASE_SECRET_KEY = (
    os.getenv("SUPABASE_SECRET_KEY")
    or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL is required")

if not SUPABASE_PUBLISHABLE_KEY:
    raise ValueError(
        "SUPABASE_PUBLISHABLE_KEY (or SUPABASE_ANON_KEY) is required"
    )

if not SUPABASE_SECRET_KEY:
    raise ValueError(
        "SUPABASE_SECRET_KEY (or SUPABASE_SERVICE_ROLE_KEY) is required"
    )