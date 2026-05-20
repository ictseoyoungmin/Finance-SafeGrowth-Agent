from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any


DEMO_PAYLOAD = {
    "product_type": "투자상품",
    "channel": "앱 푸시",
    "target_customer": "40대 예비 은퇴자",
    "language": "ko",
    "original_text": (
        "프리미엄 JB 투자 플랜은 반드시 연 12% 수익을 안전하게 누릴 수 있으며, "
        "원금 보장 혜택으로 처음 투자하는 고객도 부담 없이 시작할 수 있습니다."
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live Gemini rewrite smoke through FastAPI TestClient.")
    parser.add_argument("--env", default="../../.env", help="dotenv file to load before importing the app")
    parser.add_argument("--mode", default="marketing_balanced")
    args = parser.parse_args()

    load_env(Path(args.env))

    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "replace-me":
        print("GEMINI_API_KEY is not configured in the selected env file.", file=sys.stderr)
        return 2

    from fastapi.testclient import TestClient

    from app.main import app
    from app.services.rewrite_service import FALLBACK_REWRITE

    client = TestClient(app)

    analyze_response = client.post("/v1/compliance/analyze", json=DEMO_PAYLOAD)
    analyze_response.raise_for_status()
    analyze = analyze_response.json()

    rewrite_response = client.post(
        "/v1/compliance/rewrite",
        json={"content_id": analyze["content_id"], "mode": args.mode},
    )
    rewrite_response.raise_for_status()
    rewrite = rewrite_response.json()

    fallback_like = is_fallback_like(rewrite, FALLBACK_REWRITE.model_dump(mode="json"))

    print("rewrite_live_smoke")
    print(f"env_file={Path(args.env).resolve()}")
    print(f"gemini_model={os.environ.get('GEMINI_MODEL', '<unset>')}")
    print(f"gemini_api_key=<set len={len(gemini_key)}>")
    print(f"content_id={analyze['content_id']}")
    print(f"risk_level={analyze['risk_level']}")
    print(f"risk_categories={', '.join(analyze['risk_categories'])}")
    print(f"fallback_like={fallback_like}")
    print("revised_text_conservative:")
    print(rewrite["revised_text_conservative"])
    print("revised_text_marketing:")
    print(rewrite["revised_text_marketing"])
    print("changes:")
    for change in rewrite["changes"]:
        print(f"- {change['original']} -> {change['replacement']} ({change['reason']})")

    if fallback_like:
        print(
            "Rewrite response matched deterministic fallback text. Gemini live rewrite was not verified.",
            file=sys.stderr,
        )
        return 3

    return 0


def load_env(path: Path) -> None:
    if not path.exists():
        print(f"Env file not found: {path}", file=sys.stderr)
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


def is_fallback_like(rewrite: dict[str, Any], fallback: dict[str, Any]) -> bool:
    return (
        rewrite.get("revised_text_conservative") == fallback.get("revised_text_conservative")
        and rewrite.get("revised_text_marketing") == fallback.get("revised_text_marketing")
    )


if __name__ == "__main__":
    raise SystemExit(main())
