import type { ReactNode, SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement> & { size?: number };

function Base({ size = 18, children, ...rest }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable={false}
      {...rest}
    >
      {children}
    </svg>
  );
}

export function DocumentIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
      <path d="M9 13h6" />
      <path d="M9 17h4" />
    </Base>
  );
}

export function RiskIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 3 2 20h20Z" />
      <path d="M12 10v4" />
      <path d="M12 17v.01" />
    </Base>
  );
}

export function EvidenceIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 5a2 2 0 0 1 2-2h9v18H6a2 2 0 0 1-2-2z" />
      <path d="M15 3h3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-3" />
      <path d="M7 8h5" />
      <path d="M7 12h5" />
    </Base>
  );
}

export function CompareIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M7 4 3 8l4 4" />
      <path d="M3 8h13" />
      <path d="m17 20 4-4-4-4" />
      <path d="M21 16H8" />
    </Base>
  );
}

export function ApproveIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 2 4 5v6c0 5 3.5 9 8 11 4.5-2 8-6 8-11V5z" />
      <path d="m9 12 2 2 4-4" />
    </Base>
  );
}

export function ArchiveIcon(props: IconProps) {
  return (
    <Base {...props}>
      <rect x="3" y="3" width="18" height="4" rx="1" />
      <path d="M5 7v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7" />
      <path d="M10 12h4" />
    </Base>
  );
}

export function ChevronIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="m6 9 6 6 6-6" />
    </Base>
  );
}

export function ArrowLeftIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M19 12H5" />
      <path d="m12 19-7-7 7-7" />
    </Base>
  );
}

export function ScalesIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M12 3v18" />
      <path d="M5 21h14" />
      <path d="M5 6h14" />
      <path d="M5 6 2 13a3 3 0 0 0 6 0z" />
      <path d="M19 6l-3 7a3 3 0 0 0 6 0z" />
    </Base>
  );
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8 12 3 3 5-6" />
    </Base>
  );
}

export function XCircleIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="m9 9 6 6" />
      <path d="m15 9-6 6" />
    </Base>
  );
}
