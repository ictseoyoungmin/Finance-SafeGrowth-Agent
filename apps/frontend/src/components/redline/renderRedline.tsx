import type { ReactNode } from "react";

import { RiskMark } from "./RiskMark";
import type { FlaggedSpan } from "../../features/compliance/types";

export function renderRedline(text: string, flaggedSpans: FlaggedSpan[]) {
  const validSpans = flaggedSpans
    .filter((span) => span.start >= 0 && span.end > span.start && text.slice(span.start, span.end) === span.span_text)
    .sort((left, right) => left.start - right.start);

  if (validSpans.length === 0) {
    return renderFallbackByText(text, flaggedSpans);
  }

  const nodes: ReactNode[] = [];
  let cursor = 0;

  validSpans.forEach((span, index) => {
    if (span.start < cursor) {
      return;
    }

    if (span.start > cursor) {
      nodes.push(text.slice(cursor, span.start));
    }

    nodes.push(
      <RiskMark
        key={`${span.span_text}-${span.start}-${index}`}
        severity={span.severity}
        label={`${span.risk_category}: ${span.reason}`}
      >
        {text.slice(span.start, span.end)}
      </RiskMark>,
    );
    cursor = span.end;
  });

  if (cursor < text.length) {
    nodes.push(text.slice(cursor));
  }

  return nodes;
}

function renderFallbackByText(text: string, flaggedSpans: FlaggedSpan[]) {
  let remaining = text;
  const nodes: ReactNode[] = [];

  flaggedSpans.forEach((span, index) => {
    const matchIndex = remaining.indexOf(span.span_text);
    if (matchIndex < 0) {
      return;
    }

    nodes.push(remaining.slice(0, matchIndex));
    nodes.push(
      <RiskMark
        key={`${span.span_text}-fallback-${index}`}
        severity={span.severity}
        label={`${span.risk_category}: ${span.reason}`}
      >
        {span.span_text}
      </RiskMark>,
    );
    remaining = remaining.slice(matchIndex + span.span_text.length);
  });

  nodes.push(remaining);
  return nodes;
}
