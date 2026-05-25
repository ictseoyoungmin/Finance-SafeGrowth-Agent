import { useState, type ReactNode } from "react";

interface HelpHintProps {
  hint: ReactNode;
  label?: string;
  align?: "left" | "right";
}

export function HelpHint({ hint, label = "?", align = "left" }: HelpHintProps) {
  const [open, setOpen] = useState(false);
  return (
    <span className="help-hint">
      <button
        type="button"
        className="help-hint__trigger"
        aria-label={typeof hint === "string" ? `도움말: ${hint}` : "도움말"}
        aria-expanded={open}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={(event) => {
          event.preventDefault();
          setOpen((value) => !value);
        }}
      >
        {label}
      </button>
      {open ? (
        <span className={`help-hint__bubble help-hint__bubble--${align}`} role="tooltip">
          {hint}
        </span>
      ) : null}
    </span>
  );
}
