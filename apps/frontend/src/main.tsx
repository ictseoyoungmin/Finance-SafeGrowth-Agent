import React from "react";
import ReactDOM from "react-dom/client";

import "./styles.css";

function App() {
  return (
    <main className="app-shell">
      <section className="workspace">
        <p className="eyebrow">JB SafeGrowth Agent</p>
        <h1>Compliance review workspace</h1>
        <p>
          Slice 0 scaffold is running. The Week 1 flow will add content input,
          redline review, evidence, rewrite, and approval screens here.
        </p>
        <div className="status-row" aria-label="bootstrap status">
          <span>Frontend ready</span>
          <span>Backend API: {import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}</span>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
