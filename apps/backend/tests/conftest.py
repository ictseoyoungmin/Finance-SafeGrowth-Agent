import os


os.environ["GEMINI_API_KEY"] = "replace-me"
os.environ["SUPABASE_URL"] = "https://replace-me.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "replace-me"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "replace-me"
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

for proxy_key in (
    "ALL_PROXY",
    "all_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
):
    os.environ.pop(proxy_key, None)
