import os


os.environ.setdefault("GEMINI_API_KEY", "replace-me")
os.environ.setdefault("LLM_PROVIDER", "openai_compatible")
os.environ.setdefault("OPENAI_BASE_URL", "http://127.0.0.1:18080/v1")
os.environ.setdefault("OPENAI_API_KEY", "local-not-required")
os.environ.setdefault("OPENAI_MODEL", "gemma-4-local")
os.environ.setdefault("SUPABASE_URL", "https://replace-me.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "replace-me")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "replace-me")
os.environ.setdefault("NO_PROXY", "*")
os.environ.setdefault("no_proxy", "*")

for proxy_key in (
    "ALL_PROXY",
    "all_proxy",
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
):
    os.environ.pop(proxy_key, None)
