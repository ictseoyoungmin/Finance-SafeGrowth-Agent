import { useState, type FormEvent } from "react";

import { useAuth } from "./AuthContext";

export function LoginPage() {
  // Tester credentials are public demo defaults; prefill so the reviewer can
  // log in with one click. Admin keeps a clean field — the password is held
  // by the operator and never echoed in the UI default.
  const [id, setId] = useState("tester");
  const [password, setPassword] = useState("tester");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (isSubmitting) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await login(id.trim(), password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "로그인에 실패했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const switchToAdmin = () => {
    setId("admin");
    setPassword("");
    setError(null);
  };

  const switchToTester = () => {
    setId("tester");
    setPassword("tester");
    setError(null);
  };

  return (
    <div className="login-frame">
      <main className="login-card" aria-label="로그인">
        <header className="login-card__head">
          <span className="login-card__kicker">Compliance AI</span>
          <h1>JB SafeGrowth 검토 콘솔</h1>
          <p>준법감시팀 데모 계정으로 진입합니다.</p>
        </header>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="login-field">
            <span>아이디</span>
            <input
              type="text"
              value={id}
              onChange={(event) => setId(event.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label className="login-field">
            <span>비밀번호</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error ? (
            <div className="login-error" role="alert">
              {error}
            </div>
          ) : null}

          <button type="submit" className="login-submit" disabled={isSubmitting}>
            {isSubmitting ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <footer className="login-helpers">
          <button type="button" className="login-helper" onClick={switchToTester}>
            tester 자동완성
          </button>
          <button type="button" className="login-helper" onClick={switchToAdmin}>
            admin 으로 전환
          </button>
        </footer>
      </main>
    </div>
  );
}
