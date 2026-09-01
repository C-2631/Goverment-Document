import { useState, useRef, useEffect, useCallback } from "react";
import IndicInput from "./IndicInput";
import LocationDropdowns from "./LocationDropdowns";

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
  const [totalFields] = useState(14); // 14 steps (Zone B body fields are auto-mirrored)
  const bottomRef = useRef(null);

  // Field definitions to detect active question and auto-mirroring
  const FIELD_KEYS = [
    "applicant_name",
    "address",
    "mobile",
    "date",
    "to_officer",
    "office_village",
    "subject_moje",
    "subject_taluko",
    "subject_jillo",
    "subject_survey_no",
    "copy_details",
    "copy_quantity",
    "mtr_no",
    "online_app_no",
    "surveyor_name",
    "measurement_date",
    "deposit_fee",
    "behalf_name",
  ];

  // Helper to find the current active field
  const getCurrentField = () => {
    for (const key of FIELD_KEYS) {
      const val = formData[key];
      if (val === undefined || val === null || String(val).trim() === "") {
        return key;
      }
    }
    return null;
  };

  const currentField = getCurrentField();

  // Count filled main fields for progress
  const filledCount = [
    "applicant_name",
    "address",
    "mobile",
    "date",
    "to_officer",
    "office_village",
    "subject_moje",
    "subject_survey_no",
    "copy_details",
    "copy_quantity",
    "mtr_no",
    "online_app_no",
    "deposit_fee",
    "behalf_name",
  ].filter((k) => formData[k] && String(formData[k]).trim() !== "" && formData[k] !== "-").length;

  const pct = Math.min(100, Math.round((filledCount / totalFields) * 100));

  // Auto-scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentField]);

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
          setMessages([
            {
              r: "bot",
              t: `નમસ્તે! 🙏 નકલ મેળવવાની અરજી ફોર્મ ભરવા માટે આપનું સ્વાગત છે.

Welcome! Let's fill in the Nakal Application Form.

${data.initial_question}`,
            },
          ]);
        }
      } catch (err) {
        setMessages([
          {
            r: "bot",
            t: "⚠️ Could not connect to server. Please make sure the backend is running.",
          },
        ]);
      }
    };
    initSession();
  }, []);

  const addMsg = useCallback((msgs) => setMessages((p) => [...p, ...msgs]), []);

  // Standard message sender
  const handleSend = async (customVal) => {
    const raw = (customVal !== undefined ? customVal : input).trim();
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
        if (
          data.reply.includes("અભિનંદન") ||
          data.reply.includes("All form details are completed")
        ) {
          setDone(true);
        }
      }
    } catch (err) {
      addMsg([{ r: "bot", t: "⚠️ Error communicating with server. Please try again." }]);
    }
    setLoading(false);
  };

  // Skip optional field
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
        if (
          data.reply.includes("અભિનંદન") ||
          data.reply.includes("All form details are completed")
        ) {
          setDone(true);
        }
      }
    } catch (err) {
      addMsg([{ r: "bot", t: "⚠️ Error communicating with server. Please try again." }]);
    }
    setLoading(false);
  };

  // Change 3: Handling Cascading Location Selection & Auto-Mirroring
  const handleLocationComplete = async ({ jillo, taluko, moje }) => {
    if (!apiKey) return;

    const locFields = {
      subject_moje: moje,
      body_moje: moje,
      subject_taluko: taluko,
      body_taluko: taluko,
      subject_jillo: jillo,
      body_jillo: jillo,
    };

    // Optimistically update local form data
    setFormData((prev) => ({ ...prev, ...locFields }));

    const locationSummary = `મોજે ${moje}, તાલુકો ${taluko}, જિલ્લો ${jillo}`;
    addMsg([{ r: "user", t: `📍 સ્થળ: ${locationSummary}` }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-KEY": apiKey,
        },
        body: JSON.stringify({ message: locationSummary }),
      });
      const data = await res.json();

      // Merge server response WITH optimistic location data to prevent overwrite
      setFormData((prev) => ({
        ...(data.form_data || prev),
        ...locFields,
      }));

      if (data.reply) {
        addMsg([{ r: "bot", t: data.reply }]);
        if (
          data.reply.includes("અભિનંદન") ||
          data.reply.includes("All form details are completed")
        ) {
          setDone(true);
        }
      }
    } catch (err) {
      // Even on error, keep the optimistic location data
      addMsg([
        {
          r: "bot",
          t: `✓ સ્થળ સેવ થયું: મોજે ${moje}, તાલુકો ${taluko}, જિલ્લો ${jillo}\n\nજમીનનો સર્વે નંબર જણાવો (દા.ત. ૧૨૪/૧):\n(English) Please enter land survey number (e.g. 124/1):`,
        },
      ]);
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
      setMessages([
        {
          r: "bot",
          t: `🔄 New form started!

${data.initial_question || ""}`,
        },
      ]);
    } catch (err) {
      addMsg([{ r: "bot", t: "⚠️ Could not create new session." }]);
    }
  };

  // Quick suggestion chips based on active question
  const getSuggestionsForField = (field) => {
    switch (field) {
      case "to_officer":
        return [
          "લેન્ડ રેકોર્ડ ઇન્સ્પેક્ટર",
          "મામલતદાર શ્રી",
          "દફતરદાર શ્રી",
          "નાયબ મામલતદાર",
        ];
      case "office_village":
        return ["રાજકોટ", "ગોંડલ", "જેતપુર", "મોરબી", "જામનગર"];
      case "copy_details":
        return [
          "ટીપ્પણ શીટ",
          "માપણી શીટ",
          "ટીપ્પણ તથા માપણી શીટ",
          "ગામ નમૂના ૭/૧૨ નકલ",
        ];
      case "copy_quantity":
        return ["૧", "૨", "૩", "૫"];
      case "date":
        return ["today"];
      default:
        return [];
    }
  };

  const chips = getSuggestionsForField(currentField);

  // Field labels for display
  const FIELD_LABELS = {
    applicant_name: "અરજદારનું નામ",
    address: "સરનામું",
    mobile: "મોબાઈલ",
    date: "તારીખ",
    to_officer: "પ્રતિશ્રી (અધિકારી)",
    office_village: "કચેરી મું.",
    subject_moje: "મોજે (ગામ)",
    subject_taluko: "તાલુકો",
    subject_jillo: "જીલ્લો",
    subject_survey_no: "સર્વે નં.",
    copy_details: "માંગેલ રેકોર્ડ",
    copy_quantity: "નકલ નંગ",
    mtr_no: "MTR No.",
    online_app_no: "ઓનલાઈન અરજી નં.",
    surveyor_name: "સર્વેયર",
    measurement_date: "માપણી તારીખ",
    deposit_fee: "ડીપોઝીટ",
    behalf_name: "વતી વ્યક્તિ",
  };

  // Styles
  const C = {
    page: {
      minHeight: "100vh",
      background: "linear-gradient(160deg,#eef3f8 0%,#dde7f0 100%)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "16px 12px",
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
    h1: { fontSize: 20, fontWeight: 700 },
    h2: { fontSize: 13, opacity: 0.85, marginTop: 4 },
    bar: { marginTop: 12 },
    barLbl: { fontSize: 12.5, opacity: 0.85, marginBottom: 4 },
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
      maxHeight: "50vh",
      padding: "18px 16px",
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
      fontSize: 15,
      lineHeight: 1.65,
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
      flexDirection: "column",
      gap: 10,
      boxShadow: "0 4px 18px rgba(0,0,0,0.08)",
    },
    chipsRow: {
      display: "flex",
      flexWrap: "wrap",
      gap: 6,
      alignItems: "center",
    },
    chipBtn: {
      background: "#e8f4fc",
      border: "1px solid #bcd",
      borderRadius: 20,
      padding: "4px 12px",
      fontSize: 13,
      fontFamily: "'Noto Serif Gujarati', serif",
      color: "#1a3a5c",
      fontWeight: 600,
      cursor: "pointer",
      transition: "all 0.15s",
    },
    controlsRow: {
      display: "flex",
      gap: 10,
      alignItems: "center",
    },
    skipBtn: {
      background: "#e4ecf4",
      border: "none",
      borderRadius: 12,
      padding: "0 16px",
      height: 46,
      cursor: "pointer",
      color: "#555",
      fontSize: 13.5,
      fontWeight: 600,
    },
    sendBtn: (dis) => ({
      background: dis ? "#aaa" : "#1a3a5c",
      border: "none",
      borderRadius: 12,
      color: "white",
      padding: "0 22px",
      height: 46,
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
      fontSize: 16.5,
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
      fontSize: 13.5,
      fontWeight: 700,
      color: "#1a3a5c",
      marginBottom: 8,
    },
    chipsGrid: { display: "flex", flexWrap: "wrap", gap: 8 },
    chip: {
      background: "white",
      border: "1px solid #c8dff0",
      borderRadius: 8,
      padding: "4px 10px",
      fontSize: 13,
    },
    chipLbl: { color: "#1a3a5c", fontWeight: 700 },
    footer: {
      marginTop: 10,
      fontSize: 12,
      color: "#888",
      textAlign: "center",
    },
  };

  // Determine if active question is Location (Change 3)
  const isLocationStep =
    currentField === "subject_moje" ||
    currentField === "subject_taluko" ||
    currentField === "subject_jillo";

  return (
    <div style={C.page}>
      {/* Header */}
      <div style={C.header}>
        <div style={C.h1}>નકલ મેળવવાની અરજી — Chatbot Form</div>
        <div style={C.h2}>
          પરિશિષ્ટ નં.-૫ • Chatbot Form Filler • Google Indic Transliteration
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

      {/* Chat messages */}
      <div style={C.chat}>
        {messages.map((m, i) => (
          <div key={i} style={C.bubbleWrap(m.r)}>
            <div style={C.bubble(m.r)}>{m.t}</div>
          </div>
        ))}
        {loading && (
          <div style={C.bubbleWrap("bot")}>
            <div style={{ ...C.bubble("bot"), color: "#888", fontStyle: "italic" }}>
              ⏳ Processing...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div style={C.inputArea}>
        {!done ? (
          <>
            {/* Quick-select pill chips */}
            {chips.length > 0 && !isLocationStep && (
              <div style={C.chipsRow}>
                <span style={{ fontSize: 11.5, color: "#666", fontWeight: 600 }}>
                  ઝડપી પસંદગી (Quick Select):
                </span>
                {chips.map((chipText, i) => (
                  <button
                    key={i}
                    type="button"
                    style={C.chipBtn}
                    onClick={() => handleSend(chipText)}
                    disabled={loading}
                  >
                    {chipText}
                  </button>
                ))}
              </div>
            )}

            {/* Change 3: Location Cascading Dropdowns */}
            {isLocationStep ? (
              <LocationDropdowns
                initialValues={{
                  jillo: formData.subject_jillo || "રાજકોટ",
                  taluko: formData.subject_taluko || "રાજકોટ",
                  moje: formData.subject_moje || "",
                }}
                onComplete={handleLocationComplete}
              />
            ) : (
              /* Change 2: Google Indic Input Transliteration Component */
              <div style={C.controlsRow}>
                <div style={{ flex: 1 }}>
                  <IndicInput
                    value={input}
                    onChange={(val) => setInput(val)}
                    onSubmit={() => handleSend()}
                    disabled={loading || !apiKey}
                    placeholder="Type in English or ગુજરાતી... (e.g. Land Record Inspector)"
                  />
                </div>
                <button
                  type="button"
                  onClick={handleSkip}
                  disabled={loading}
                  style={C.skipBtn}
                >
                  Skip
                </button>
                <button
                  type="button"
                  onClick={() => handleSend()}
                  disabled={loading || !input.trim()}
                  style={C.sendBtn(loading || !input.trim())}
                >
                  ➤
                </button>
              </div>
            )}
          </>
        ) : (
          <div style={{ display: "flex", gap: 10, width: "100%", flexDirection: "column" }}>
            <div style={{ display: "flex", gap: 10 }}>
              <button
                onClick={handleDownload}
                disabled={downloading}
                style={{ ...C.pdfBtn(downloading), flex: 1 }}
              >
                {downloading ? "📄 Generating PDF..." : "📥 Download Filled PDF"}
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

      {/* Summary Chips Preview */}
      {Object.keys(formData).length > 0 && (
        <div style={C.summary}>
          <div style={C.sumHdr}>📋 Collected Data Preview:</div>
          <div style={C.chipsGrid}>
            {Object.entries(formData)
              .filter(
                ([key, v]) =>
                  v &&
                  String(v).trim() !== "" &&
                  v !== "-" &&
                  !key.startsWith("body_") // Don't duplicate mirrored fields in preview chips
              )
              .map(([key, val]) => (
                <div key={key} style={C.chip}>
                  <span style={C.chipLbl}>{FIELD_LABELS[key] || key}: </span>
                  <span style={{ fontFamily: "'Noto Serif Gujarati',serif" }}>
                    {val}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div style={C.footer}>
        Powered by FastAPI • Noto Sans Gujarati • Server-side PDF Generation
      </div>
    </div>
  );
}
