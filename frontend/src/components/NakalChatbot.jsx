import { useState, useRef, useEffect, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

export default function NakalChatbot() {
  const [apiKey, setApiKey] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [formData, setFormData] = useState({});
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [totalFields] = useState(17);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Count filled fields for progress
  const filledCount = Object.values(formData).filter(
    (v) => v && String(v).trim() !== "" && v !== "-"
  ).length;
  const pct = Math.round((filledCount / totalFields) * 100);

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input
  useEffect(() => {
    if (!done && !loading) inputRef.current?.focus();
  }, [done, loading, messages]);

  // Initialize session on mount
  useEffect(() => {
    const initSession = async () => {
      try {
        const res = await fetch(`${API_BASE}/session`, { method: "POST" });
        const data = await res.json();
        setApiKey(data.user_api_key);
        setSessionId(data.session_id);
        setFormData(data.form_data || {});
        if (data.initial_question) {
          setMessages([{ r: "bot", t: `નમસ્તે! 🙏 નકલ મેળવવાની અરજી ફોર્મ ભરવા માટે આપનું સ્વાગત છે.\n\nWelcome! Let's fill in the Nakal Application Form.\n\n${data.initial_question}` }]);
        }
      } catch (err) {
        setMessages([{ r: "bot", t: "⚠️ Could not connect to server. Please make sure the backend is running on port 8000." }]);
      }
    };
    initSession();
  }, []);

  const addMsg = useCallback((msgs) => setMessages((p) => [...p, ...msgs]), []);

  const handleSend = async () => {
    const raw = input.trim();
    if (!raw || !apiKey) return;
    addMsg([{ r: "user", t: raw }]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-KEY": apiKey,
        },
        body: JSON.stringify({ message: raw }),
      });
      const data = await res.json();
      setFormData(data.form_data || {});
      if (data.reply) {
        addMsg([{ r: "bot", t: data.reply }]);
        // Check if all fields are done
        if (data.reply.includes("અભિનંદન") || data.reply.includes("All form details are completed")) {
          setDone(true);
        }
      }
    } catch (err) {
      addMsg([{ r: "bot", t: "⚠️ Error communicating with server. Please try again." }]);
    }
    setLoading(false);
  };

  const handleSkip = async () => {
    if (!apiKey) return;
    addMsg([{ r: "user", t: "(skip)" }]);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-KEY": apiKey,
        },
        body: JSON.stringify({ message: "skip" }),
      });
      const data = await res.json();
      setFormData(data.form_data || {});
      if (data.reply) {
        addMsg([{ r: "bot", t: data.reply }]);
        if (data.reply.includes("અભિનંદન") || data.reply.includes("All form details are completed")) {
          setDone(true);
        }
      }
    } catch (err) {
      addMsg([{ r: "bot", t: "⚠️ Error communicating with server. Please try again." }]);
    }
    setLoading(false);
  };

  const handleDownload = async () => {
    if (!apiKey) return;
    setDownloading(true);
    addMsg([{ r: "bot", t: "📄 Generating your filled PDF..." }]);
    try {
      const res = await fetch(`${API_BASE}/pdf/download?api_key=${apiKey}`);
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Parishisht_5_${sessionId ? sessionId.substring(0, 8) : "form"}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      addMsg([{ r: "bot", t: "✅ PDF downloaded successfully!" }]);
    } catch (err) {
      addMsg([{ r: "bot", t: "⚠️ Error generating PDF. Please try again." }]);
    }
    setDownloading(false);
  };

  const handlePreview = () => {
    if (!apiKey) return;
    window.open(`${API_BASE}/pdf/preview?api_key=${apiKey}`, "_blank");
  };

  const handleNewForm = async () => {
    try {
      const res = await fetch(`${API_BASE}/session`, { method: "POST" });
      const data = await res.json();
      setApiKey(data.user_api_key);
      setSessionId(data.session_id);
      setFormData(data.form_data || {});
      setDone(false);
      setMessages([{ r: "bot", t: `🔄 New form started!\n\n${data.initial_question || ""}` }]);
    } catch (err) {
      addMsg([{ r: "bot", t: "⚠️ Could not create new session." }]);
    }
  };

  // Styles (adapted from original NakalChatbot)
  const C = {
    page: {
      minHeight: "100vh",
      background: "linear-gradient(160deg,#eef3f8 0%,#dde7f0 100%)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: 16,
      fontFamily: "'Segoe UI',sans-serif",
    },
    header: {
      width: "100%",
      maxWidth: 680,
      background: "#1a3a5c",
      borderRadius: "16px 16px 0 0",
      padding: "18px 24px",
      color: "white",
      boxShadow: "0 4px 18px rgba(0,0,0,0.22)",
    },
    h1: { fontSize: 21, fontWeight: 700 },
    h2: { fontSize: 13, opacity: 0.85, marginTop: 4 },
    bar: { marginTop: 12 },
    barLbl: { fontSize: 13, opacity: 0.8, marginBottom: 4 },
    barBg: { background: "rgba(255,255,255,0.2)", borderRadius: 10, height: 8 },
    barFill: (p) => ({
      background: "#4fc3f7",
      borderRadius: 10,
      height: 8,
      width: `${p}%`,
      transition: "width 0.4s",
    }),
    chat: {
      width: "100%",
      maxWidth: 680,
      flex: 1,
      background: "white",
      overflowY: "auto",
      maxHeight: "52vh",
      padding: 20,
      display: "flex",
      flexDirection: "column",
      gap: 12,
      boxShadow: "0 1px 8px rgba(0,0,0,0.08)",
    },
    bubbleWrap: (r) => ({
      display: "flex",
      justifyContent: r === "user" ? "flex-end" : "flex-start",
    }),
    bubble: (r) => ({
      maxWidth: "85%",
      padding: "12px 16px",
      fontSize: 15.5,
      lineHeight: 1.7,
      whiteSpace: "pre-wrap",
      borderRadius:
        r === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
      background: r === "user" ? "#1a3a5c" : "#f0f5fa",
      color: r === "user" ? "white" : "#1a2a3a",
      boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
      fontFamily: "'Noto Serif Gujarati','Segoe UI',sans-serif",
    }),
    inputArea: {
      width: "100%",
      maxWidth: 680,
      background: "#f7f9fc",
      borderTop: "1px solid #dde",
      padding: "14px 16px",
      display: "flex",
      gap: 10,
      boxShadow: "0 4px 18px rgba(0,0,0,0.08)",
    },
    textarea: {
      flex: 1,
      border: "1.5px solid #bcd",
      borderRadius: 12,
      padding: "12px 16px",
      fontSize: 15.5,
      resize: "none",
      height: 52,
      fontFamily: "'Noto Serif Gujarati','Segoe UI',sans-serif",
      outline: "none",
    },
    skipBtn: {
      background: "#e4ecf4",
      border: "none",
      borderRadius: 12,
      padding: "0 16px",
      cursor: "pointer",
      color: "#555",
      fontSize: 14,
      fontWeight: 600,
    },
    sendBtn: (dis) => ({
      background: dis ? "#aaa" : "#1a3a5c",
      border: "none",
      borderRadius: 12,
      color: "white",
      padding: "0 22px",
      cursor: dis ? "default" : "pointer",
      fontSize: 22,
      fontWeight: 700,
    }),
    pdfBtn: (dis) => ({
      background: dis
        ? "#aaa"
        : "linear-gradient(135deg,#1a3a5c,#2768a0)",
      border: "none",
      borderRadius: 12,
      color: "white",
      padding: "16px",
      cursor: dis ? "default" : "pointer",
      fontSize: 17,
      fontWeight: 700,
      letterSpacing: 0.5,
      boxShadow: "0 4px 14px rgba(26,58,92,.35)",
    }),
    previewBtn: {
      background: "#e4ecf4",
      border: "none",
      borderRadius: 12,
      color: "#1a3a5c",
      padding: "16px 20px",
      cursor: "pointer",
      fontSize: 15,
      fontWeight: 600,
    },
    newFormBtn: {
      background: "transparent",
      border: "1.5px solid #1a3a5c",
      borderRadius: 12,
      color: "#1a3a5c",
      padding: "12px 24px",
      cursor: "pointer",
      fontSize: 14,
      fontWeight: 600,
      marginTop: 8,
    },
    summary: {
      width: "100%",
      maxWidth: 680,
      background: "#f0f7ff",
      border: "1px solid #c4dcf0",
      borderRadius: "0 0 14px 14px",
      padding: "14px 18px",
      marginTop: 4,
    },
    sumHdr: {
      fontSize: 14,
      fontWeight: 700,
      color: "#1a3a5c",
      marginBottom: 8,
    },
    chips: { display: "flex", flexWrap: "wrap", gap: 8 },
    chip: {
      background: "white",
      border: "1px solid #c8dff0",
      borderRadius: 8,
      padding: "5px 12px",
      fontSize: 14,
    },
    chipLbl: { color: "#1a3a5c", fontWeight: 700 },
    footer: {
      marginTop: 10,
      fontSize: 12,
      color: "#888",
      textAlign: "center",
    },
  };

  // Field labels for display
  const FIELD_LABELS = {
    applicant_name: "અરજદારનું નામ",
    address: "સરનામું",
    mobile: "મોબાઈલ",
    date: "તારીખ",
    to_officer: "પ્રતિશ્રી",
    office_village: "કચેરી મું.",
    subject_moje: "મોજે",
    subject_taluko: "તાલુકો",
    subject_jillo: "જીલ્લો",
    subject_survey_no: "સર્વે નં.",
    copy_details: "રેકોર્ડ",
    copy_quantity: "નકલ નંગ",
    mtr_no: "MTR No.",
    online_app_no: "ઓનલાઈન અરજી નં.",
    surveyor_name: "સર્વેયર",
    measurement_date: "માપણી તારીખ",
    deposit_fee: "ડીપોઝીટ",
    behalf_name: "વતી",
  };

  return (
    <div style={C.page}>
      <div style={C.header}>
        <div style={C.h1}>નકલ મેળવવાની અરજી — Chatbot Form</div>
        <div style={C.h2}>
          પરિશિષ્ટ નં.-૫ • Chatbot Form Filler • Auto-translate to Gujarati
        </div>
        {!done && (
          <div style={C.bar}>
            <div style={C.barLbl}>
              Progress: {filledCount} / {totalFields} fields completed
            </div>
            <div style={C.barBg}>
              <div style={C.barFill(pct)} />
            </div>
          </div>
        )}
      </div>

      <div style={C.chat}>
        {messages.map((m, i) => (
          <div key={i} style={C.bubbleWrap(m.r)}>
            <div style={C.bubble(m.r)}>{m.t}</div>
          </div>
        ))}
        {loading && (
          <div style={C.bubbleWrap("bot")}>
            <div
              style={{ ...C.bubble("bot"), color: "#888", fontStyle: "italic" }}
            >
              ⏳ Processing...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div style={C.inputArea}>
        {!done ? (
          <>
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading || !apiKey}
              placeholder="Type your answer here... (English or ગુજરાતી)"
              style={C.textarea}
            />
            <button onClick={handleSkip} disabled={loading} style={C.skipBtn}>
              Skip
            </button>
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              style={C.sendBtn(loading || !input.trim())}
            >
              ➤
            </button>
          </>
        ) : (
          <div style={{ display: "flex", gap: 10, width: "100%", flexDirection: "column" }}>
            <div style={{ display: "flex", gap: 10 }}>
              <button
                onClick={handleDownload}
                disabled={downloading}
                style={{ ...C.pdfBtn(downloading), flex: 1 }}
              >
                {downloading
                  ? "📄 Generating PDF..."
                  : "📥 Download Filled PDF"}
              </button>
              <button onClick={handlePreview} style={C.previewBtn}>
                👁️ Preview
              </button>
            </div>
            <div style={{ textAlign: "center" }}>
              <button onClick={handleNewForm} style={C.newFormBtn}>
                🔄 Fill Another Form
              </button>
            </div>
          </div>
        )}
      </div>

      {Object.keys(formData).length > 0 && (
        <div style={C.summary}>
          <div style={C.sumHdr}>📋 Collected Data Preview:</div>
          <div style={C.chips}>
            {Object.entries(formData)
              .filter(([, v]) => v && String(v).trim() !== "" && v !== "-")
              .map(([key, val]) => (
                <div key={key} style={C.chip}>
                  <span style={C.chipLbl}>
                    {FIELD_LABELS[key] || key}:{" "}
                  </span>
                  <span
                    style={{
                      fontFamily: "'Noto Serif Gujarati',serif",
                    }}
                  >
                    {val}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
      <div style={C.footer}>
        Powered by FastAPI • Noto Sans Gujarati • Server-side PDF Generation
      </div>
    </div>
  );
}
