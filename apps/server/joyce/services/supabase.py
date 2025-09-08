from supabase import Client, create_client

from joyce.env import env

supabase_client: Client = create_client(
    supabase_url=env.SUPABASE_URL,
    supabase_key=env.SUPABASE_SECRET_KEY,
)
