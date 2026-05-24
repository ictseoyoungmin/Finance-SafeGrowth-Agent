from typing import Any

from app.integrations.llm.base import LlmMessage
from app.schemas.agent import AgentRunRequest, AgentStep


SYSTEM_PROMPT = (
    "You are JB SafeGrowth, the compliance review AI Agent for JB Financial Group. "
    "Your job is to review Korean financial advertisement copy for regulatory risk, "
    "cite the relevant guidelines, and propose safer rewrites. Reply in Korean.\n"
    "\n"
    "Tool playbook:\n"
    "- If a content_id is provided but the original text is missing, call fetch_content first.\n"
    "- Always call scan_rules before judging risk.\n"
    "- If scan_rules reports any HIGH or MEDIUM finding, call search_regulation with the "
    "  reported risk_categories and the product_type from the content.\n"
    "- If any flagged span exists, call draft_rewrite to obtain conservative and marketing variants.\n"
    "- If you need a missing input, want approval, or want a human to choose between revisions, "
    "  call request_human_review with a clear question. The run will pause until the user replies.\n"
    "- End every run by calling finalize_report exactly once. Choose decision in "
    "  {approve, reject, revise, none}, supply selected_revision when applicable, and write a short summary.\n"
    "\n"
    "Safety rules:\n"
    "- Do not invent regulation names. Cite evidence_id values returned by search_regulation.\n"
    "- Do not return raw rewrite text in the summary; the rewrite is already attached to the report.\n"
    "- Never mark a HIGH-risk advertisement as approved without an explicit human approval step.\n"
)


def build_user_text(request: AgentRunRequest) -> str:
    parts: list[str] = []
    if request.user_message:
        parts.append(request.user_message.strip())
    elif request.text:
        parts.append(request.text.strip())

    metadata_lines: list[str] = []
    if request.content_id is not None:
        metadata_lines.append(f"content_id: {request.content_id}")
    if request.product_type:
        metadata_lines.append(f"product_type: {request.product_type}")
    if request.channel:
        metadata_lines.append(f"channel: {request.channel}")
    if request.target_customer:
        metadata_lines.append(f"target_customer: {request.target_customer}")
    if request.language:
        metadata_lines.append(f"language: {request.language}")
    metadata_lines.append(f"mode: {request.mode}")

    if metadata_lines:
        parts.append("\n".join(["[context]", *metadata_lines]))

    if not parts:
        parts.append("Please review the supplied content for compliance risk.")

    return "\n\n".join(parts)


def build_messages(request: AgentRunRequest, steps: list[AgentStep]) -> list[LlmMessage]:
    messages: list[LlmMessage] = [
        {"role": "user", "parts": [{"text": build_user_text(request)}]}
    ]

    for step in steps:
        if step.step_type == "tool_call" and step.tool_name:
            messages.append(
                {
                    "role": "model",
                    "parts": [
                        {
                            "functionCall": {
                                "name": step.tool_name,
                                "args": (step.payload or {}).get("args", {}),
                            }
                        }
                    ],
                }
            )
        elif step.step_type == "tool_result" and step.tool_name:
            messages.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "functionResponse": {
                                "name": step.tool_name,
                                "response": (step.payload or {}).get("result", {}),
                            }
                        }
                    ],
                }
            )
        elif step.step_type == "human_response":
            messages.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "functionResponse": {
                                "name": "request_human_review",
                                "response": dict(step.payload or {}),
                            }
                        }
                    ],
                }
            )

    return messages


def build_contents(request: AgentRunRequest, steps: list[AgentStep]) -> list[dict[str, Any]]:
    return build_messages(request, steps)
