import { CheckCircleIcon, ScalesIcon, XCircleIcon } from "../../../components/icons";
import { approvalDecisionLabel } from "../approvalDecisionLabels";
import type { ApprovalDecision } from "../types";

interface ApprovalStampProps {
  decision?: ApprovalDecision | null;
}

type Tone = "pending" | "approved" | "rejected" | "revision";

function toneFor(decision?: ApprovalDecision | null): Tone {
  if (decision === "APPROVED" || decision === "CONDITIONALLY_APPROVED") return "approved";
  if (decision === "REJECTED") return "rejected";
  if (decision === "REVISION_REQUESTED") return "revision";
  return "pending";
}

const STAMP_SIZE = 132;

export function ApprovalStamp({ decision }: ApprovalStampProps) {
  const tone = toneFor(decision);
  const label = decision ? approvalDecisionLabel(decision) : "검토 대기";

  return (
    <div className={`approval-stamp approval-stamp--${tone}`} aria-label={`심의 도장: ${label}`}>
      <svg
        viewBox="0 0 132 132"
        width={STAMP_SIZE}
        height={STAMP_SIZE}
        aria-hidden="true"
        focusable={false}
        className="approval-stamp__svg"
      >
        <defs>
          <path id="approval-stamp-top" d="M 66 66 m -50 0 a 50 50 0 1 1 100 0" />
          <path id="approval-stamp-bot" d="M 66 66 m -50 0 a 50 50 0 1 0 100 0" />
        </defs>

        <circle cx="66" cy="66" r="60" className="approval-stamp__ring approval-stamp__ring--outer" />
        <circle cx="66" cy="66" r="50" className="approval-stamp__ring approval-stamp__ring--inner" />

        <text className="approval-stamp__legend">
          <textPath href="#approval-stamp-top" startOffset="50%" textAnchor="middle">
            COMPLIANCE · REVIEW · STAMP
          </textPath>
        </text>
        <text className="approval-stamp__legend approval-stamp__legend--bottom">
          <textPath href="#approval-stamp-bot" startOffset="50%" textAnchor="middle">
            JB · SAFEGROWTH · AI
          </textPath>
        </text>

        <g transform="translate(46, 36)" className="approval-stamp__glyph">
          {tone === "approved" ? <CheckCircleIcon size={40} /> : null}
          {tone === "rejected" ? <XCircleIcon size={40} /> : null}
          {tone === "revision" ? <ScalesIcon size={40} /> : null}
          {tone === "pending" ? <ScalesIcon size={40} /> : null}
        </g>
      </svg>
      <strong className="approval-stamp__label">{label}</strong>
    </div>
  );
}
