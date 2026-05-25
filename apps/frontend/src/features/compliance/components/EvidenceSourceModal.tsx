import { useEffect, useState } from "react";

import { ApiNotAvailableError, fetchRegulationVersion } from "../api";
import type { RegulationVersionDetail } from "../types";

interface EvidenceSourceModalProps {
  versionId: string;
  evidenceTitle?: string;
  onClose: () => void;
}

type LoadState =
  | { status: "loading" }
  | { status: "ready"; detail: RegulationVersionDetail }
  | { status: "error"; message: string };

const RAW_TEXT_PREVIEW = 1500;

export function EvidenceSourceModal({ versionId, evidenceTitle, onClose }: EvidenceSourceModalProps) {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    fetchRegulationVersion(versionId)
      .then((detail) => {
        if (cancelled) return;
        setState({ status: "ready", detail });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        let message = "규정 원문을 불러오지 못했습니다.";
        if (error instanceof ApiNotAvailableError) {
          message =
            "이 환경에는 규정 원문 조회 API가 아직 배포되지 않았습니다. 백엔드 업데이트 후 다시 시도해 주세요.";
        } else if (error instanceof Error) {
          message = `규정 원문을 불러오지 못했습니다 (${error.message}).`;
        }
        setState({ status: "error", message });
      });
    return () => {
      cancelled = true;
    };
  }, [versionId]);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="DB 인스턴스 상세">
      <div className="modal-card">
        <header className="modal-card__head">
          <div>
            <p className="modal-card__kicker">DB 인스턴스</p>
            <h2>{evidenceTitle ?? "규정 원문"}</h2>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            닫기 ✕
          </button>
        </header>

        {state.status === "loading" ? (
          <p className="loading-block" aria-busy>
            DB 인스턴스를 불러오는 중...
          </p>
        ) : null}

        {state.status === "error" ? (
          <div className="notice" role="alert">
            {state.message}
            <small className="modal-card__error-cid">요청한 버전 ID: {versionId}</small>
          </div>
        ) : null}

        {state.status === "ready" ? (
          <>
            <dl className="modal-card__meta">
              <div>
                <dt>버전 ID</dt>
                <dd className="is-mono">{state.detail.id}</dd>
              </div>
              <div>
                <dt>버전 라벨</dt>
                <dd>{state.detail.version_label ?? "—"}</dd>
              </div>
              <div>
                <dt>시행일</dt>
                <dd>{state.detail.effective_date ?? "—"}</dd>
              </div>
              <div>
                <dt>출처</dt>
                <dd className="is-mono">{state.detail.source_id}</dd>
              </div>
              <div>
                <dt>해시</dt>
                <dd className="is-mono">{state.detail.content_hash}</dd>
              </div>
              <div>
                <dt>청크 수</dt>
                <dd>{state.detail.chunk_count}</dd>
              </div>
              {state.detail.ingested_at ? (
                <div>
                  <dt>수집 시각</dt>
                  <dd>{formatTimestamp(state.detail.ingested_at)}</dd>
                </div>
              ) : null}
              {state.detail.superseded_by ? (
                <div>
                  <dt>대체된 버전</dt>
                  <dd className="is-mono">{state.detail.superseded_by}</dd>
                </div>
              ) : null}
            </dl>

            <div className="modal-card__body">
              <p className="modal-card__body-label">원문 (preview)</p>
              <pre className="modal-card__raw">
                {truncate(state.detail.raw_text ?? "원문이 저장되어 있지 않습니다.", RAW_TEXT_PREVIEW)}
              </pre>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function truncate(text: string, max: number): string {
  if (text.length <= max) return text;
  return text.slice(0, max - 1).trimEnd() + "…";
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
