from app.agent.state import AgentState
from app.schemas.agent import HumanPrompt
from app.schemas.tools import RequestHumanReviewArgs, RequestHumanReviewResult


class RequestHumanReviewTool:
    name = "request_human_review"
    description = (
        "Pause the agent and ask a human reviewer for input. Use this when the agent "
        "needs missing information, wants to confirm a decision, or wants approval. "
        "Provide a clear `question`. Optional `options` is a short list of choices the "
        "human can pick from. Optional `proposed_action` is a structured suggestion "
        "(e.g. {\"decision\": \"approve\", \"selected_revision\": \"marketing\"}). "
        "Calling this tool ends the current run iteration and transitions the run to "
        "the awaiting_human state until /v1/agent/runs/{run_id}/respond is called."
    )
    args_model = RequestHumanReviewArgs
    result_model = RequestHumanReviewResult

    def run(self, args: RequestHumanReviewArgs, state: AgentState) -> RequestHumanReviewResult:
        prompt = HumanPrompt(
            question=args.question,
            options=list(args.options) if args.options else None,
            proposed_action=dict(args.proposed_action) if args.proposed_action else None,
        )
        state.pending_human = prompt
        state.status = "awaiting_human"
        return RequestHumanReviewResult(
            awaiting_human=True,
            question=prompt.question,
            options=prompt.options,
            proposed_action=prompt.proposed_action,
        )
