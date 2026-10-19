import React, { useEffect, useRef, useState } from "react";
import { Bot, CheckCircle2, CircleHelp, Cpu, Send, ShieldCheck, Trash2, Wifi, Wrench } from "lucide-react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "http://127.0.0.1:5000/api" : "/api");
const SUGGESTIONS = [
  "My Wi-Fi is not working",
  "I cannot log in to my account",
  "My laptop is very slow",
  "The application keeps crashing",
];

const initialMessage = {
  id: 1,
  role: "assistant",
  data: {
    title: "Welcome to your troubleshooting assistant",
    answer: "Describe the technical issue you are facing. I will match it to a troubleshooting guide and suggest practical checks.",
    steps: [
      "Choose one of the example issues or type your own.",
      "Do not share passwords, OTPs, or other sensitive information.",
    ],
    follow_up: "What problem can I help you investigate?",
    category: "welcome",
  },
};

export default function App() {
  const [messages, setMessages] = useState([initialMessage]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [repairStates, setRepairStates] = useState({});
  const [engineStatus, setEngineStatus] = useState("checking");
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE_URL}/health`)
      .then((response) => {
        if (!response.ok) throw new Error("Backend unavailable");
        return response.json();
      })
      .then((data) => active && setEngineStatus(data.engine || "local_rules"))
      .catch(() => active && setEngineStatus("offline"));
    return () => { active = false; };
  }, []);

  async function sendMessage(text = input) {
    const message = text.trim();
    if (!message || loading) return;

    setError("");
    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", text: message },
    ]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "The request could not be completed.");
      }

      setMessages((current) => [
        ...current,
        { id: Date.now() + 1, role: "assistant", data },
      ]);
    } catch (err) {
      setError(
        err.message.includes("Failed to fetch")
          ? "Cannot reach the backend. Start the Flask server at 127.0.0.1:5000 and try again."
          : err.message
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  async function runRepair(repair, stateKey) {
    const confirmed = window.confirm(
      `${repair.title}\n\n${repair.description}\n\nRun this approved repair on this computer?`
    );
    if (!confirmed) return;

    setRepairStates((current) => ({ ...current, [stateKey]: { status: "running" } }));
    try {
      const response = await fetch(`${API_BASE_URL}/repairs/${encodeURIComponent(repair.id)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmed: true }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "The repair could not be completed.");
      setRepairStates((current) => ({
        ...current,
        [stateKey]: { status: data.status, message: data.message },
      }));
    } catch (err) {
      setRepairStates((current) => ({ ...current, [stateKey]: { status: "error", message: err.message } }));
    }
  }

  function clearChat() {
    setMessages([{ ...initialMessage, id: Date.now() }]);
    setError("");
    setInput("");
    setRepairStates({});
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Bot size={23} /></div>
          <div>
            <div className="brand-name">FixFlow</div>
            <div className="brand-subtitle">Troubleshooting assistant</div>
          </div>
        </div>

        <div className="sidebar-label">QUICK START</div>
        <div className="suggestion-list">
          {SUGGESTIONS.map((item) => (
            <button className="suggestion" key={item} onClick={() => sendMessage(item)} disabled={loading}>
              <span className="suggestion-dot" />
              {item}
            </button>
          ))}
        </div>

        <div className="sidebar-note">
          <ShieldCheck size={17} />
          <div>
            <strong>Privacy first</strong>
            <p>Never enter passwords, OTPs, or confidential data.</p>
          </div>
        </div>

        <div className="sidebar-footer">
          <span className={`status-dot ${engineStatus === "offline" ? "offline" : ""}`} />
          {engineStatus === "checking" ? "Checking service…" :
            engineStatus === "offline" ? "Backend offline" :
              engineStatus === "hosted_model" ? "Hosted model configured" : "Local rules ready"}
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-title">
            <span className="mobile-brand"><Bot size={20} /></span>
            <div>
              <h1>Technical Support</h1>
              <p>Guided diagnostics for common issues</p>
            </div>
          </div>
          <button className="clear-button" onClick={clearChat} title="Clear conversation">
            <Trash2 size={16} /> <span>Clear chat</span>
          </button>
        </header>

        <div className="chat-area">
          <div className="date-divider"><span>START A CONVERSATION</span></div>

          {messages.map((message) => (
            <div className={`message-row ${message.role}`} key={message.id}>
              {message.role === "assistant" && (
                <div className="avatar assistant-avatar"><Bot size={18} /></div>
              )}
              <div className={`message-content ${message.role}`}>
                {message.role === "user" ? (
                  <div className="user-bubble">{message.text}</div>
                ) : (
                  <article className="answer-card">
                    <div className="answer-heading">
                      <div className="answer-icon">
                        {message.data.category === "network" ? <Wifi size={18} /> :
                          message.data.category === "unknown" ? <CircleHelp size={18} /> : <Cpu size={18} />}
                      </div>
                      <div>
                        <div className="eyebrow">TROUBLESHOOTING GUIDE</div>
                        <h2>{message.data.title}</h2>
                      </div>
                    </div>
                    {message.data.category !== "welcome" && (
                      <div className={`engine-state ${message.data.engine === "hosted_model" ? "hosted" : "local"}`}>
                        {message.data.engine === "hosted_model" ? "Hosted AI model" : "Local rules fallback"}
                      </div>
                    )}
                    {message.data.model_notice && <p className="model-notice">{message.data.model_notice}</p>}
                    <p className="answer-intro">{message.data.answer}</p>
                    <ol className="steps-list">
                      {message.data.steps.map((step, index) => (
                        <li key={`${message.id}-${index}`}>
                          <span className="step-number">{index + 1}</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                    {message.data.follow_up && (
                      <div className="follow-up">
                        <CheckCircle2 size={17} />
                        <div><strong>To narrow it down</strong><p>{message.data.follow_up}</p></div>
                      </div>
                    )}
                    {message.data.repairs?.length > 0 && (
                      <section className="repair-tools" aria-label="Available automated repairs">
                        <h3><Wrench size={15} /> Available repair</h3>
                        {message.data.repairs.map((repair) => {
                          const stateKey = `${message.id}:${repair.id}`;
                          const repairState = repairStates[stateKey];
                          return (
                            <div className="repair-option" key={repair.id}>
                              <div className="repair-copy">
                                <strong>{repair.title}</strong>
                                <p>{repair.description}</p>
                              </div>
                              <button
                                className="repair-button"
                                onClick={() => runRepair(repair, stateKey)}
                                disabled={repairState?.status === "running"}
                              >
                                {repairState?.status === "running" ? "Working…" : "Run fix"}
                              </button>
                              {repairState?.message && (
                                <p className={`repair-result ${repairState.status === "error" ? "failed" : "success"}`} role="status">
                                  {repairState.message}
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </section>
                    )}
                    <div className="category-label">Category: {message.data.category}</div>
                  </article>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="avatar assistant-avatar"><Bot size={18} /></div>
              <div className="typing-card"><span /><span /><span /> Checking troubleshooting rules…</div>
            </div>
          )}
          {error && <div className="error-banner" role="alert">{error}</div>}
          <div ref={endRef} />
        </div>

        <div className="composer-wrap">
          <form className="composer" onSubmit={(event) => { event.preventDefault(); sendMessage(); }}>
            <input
              ref={inputRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Describe your technical issue…"
              aria-label="Describe your technical issue"
              maxLength={1000}
              disabled={loading}
            />
            <button className="send-button" type="submit" disabled={!input.trim() || loading} aria-label="Send message">
              <Send size={18} />
            </button>
          </form>
          <div className="composer-foot">
            <span><ShieldCheck size={13} /> AI or local guidance; automated repairs require your approval.</span>
            <span>{input.length}/1000</span>
          </div>
        </div>
      </section>
    </main>
  );
}
