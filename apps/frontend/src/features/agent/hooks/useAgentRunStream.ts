import { useEffect } from "react";

import { getAgentRun, subscribeAgentStream } from "../api";
import type { AgentRunDetail } from "../types";

export function useAgentRunStream(
  runId: string | undefined,
  onUpdate: (detail: AgentRunDetail) => void,
) {
  useEffect(() => {
    if (!runId) return;

    let cancelled = false;
    const refresh = async () => {
      if (cancelled) return;
      try {
        onUpdate(await getAgentRun(runId));
      } catch {
        return;
      }
    };

    const source = subscribeAgentStream(runId, refresh);
    const interval = window.setInterval(refresh, 1200);
    void refresh();

    return () => {
      cancelled = true;
      source?.close();
      window.clearInterval(interval);
    };
  }, [runId, onUpdate]);
}
