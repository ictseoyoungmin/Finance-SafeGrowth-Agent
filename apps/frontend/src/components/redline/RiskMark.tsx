import type { ReactNode } from "react";

import type { RiskLevel } from "../../features/compliance/types";

interface RiskMarkProps {
  children: ReactNode;
  severity: RiskLevel;
  label: string;
}

export function RiskMark({ children, severity, label }: RiskMarkProps) {
  return (
    <mark className={`risk-mark risk-${severity.toLowerCase()}`} title={label}>
      {children}
    </mark>
  );
}
