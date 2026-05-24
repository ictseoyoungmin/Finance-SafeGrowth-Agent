import type { ReactNode } from "react";

import type { RiskLevel } from "../../features/compliance/types";

interface RiskMarkProps {
  children: ReactNode;
  severity: RiskLevel;
  label: string;
  index?: number;
}

export function RiskMark({ children, severity, label, index }: RiskMarkProps) {
  return (
    <mark className={`risk-mark risk-${severity.toLowerCase()}`} title={label}>
      {index ? <span className="risk-mark-index">{index}</span> : null}
      {children}
    </mark>
  );
}
