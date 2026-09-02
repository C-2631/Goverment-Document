import { useState, useRef, useEffect } from "react";
import { getGujaratiSuggestions } from "../utils/indicTranslit";

/**
 * IndicInput — Text input with Google Indic Gujarati transliteration suggestions
 * Props:
 *   value         {string}   — controlled value
 *   onChange      {fn}       — called with final Gujarati string
 *   onSubmit      {fn}       — called when Enter is pressed
 *   placeholder   {string}   — placeholder text (Gujarati + English)
 *   label         {string}   — field label
 *   multiline     {boolean}  — textarea vs input
 *   disabled      {boolean}  — disabled state
 */
export default function IndicInput({
  value,
  onChange,
  onSubmit,
  placeholder,
  label,
  multiline = false,
  disabled = false,
}) {
  const [rawInput, setRawInput] = useState(value || "");
  const [suggestions, setSuggestions] = useState([]);
  const [showDrop, setShowDrop] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);
  const containerRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    setRawInput(value || "");
  }, [value]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowDrop(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleInputChange = (e) => {
    const raw = e.target.value;
    setRawInput(raw);
    onChange(raw);

    // If user types Gujarati directly — pass through immediately
    if (/[\u0A80-\u0AFF]/.test(raw)) {
      setSuggestions([]);
      setShowDrop(false);
      return;
    }

    // Debounce API call by 300ms
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      if (raw.trim().length < 2) {
        setSuggestions([]);
        setShowDrop(false);
        return;
      }
      setLoading(true);
      const sugs = await getGujaratiSuggestions(raw);
      setLoading(false);
      if (sugs && sugs.length > 0) {
        setSuggestions(sugs);
        setShowDrop(true);
      }
    }, 300);
  };

  const handleSelect = (suggestion) => {
    setRawInput(suggestion);
    onChange(suggestion);
    setSuggestions([]);
    setShowDrop(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      let finalVal = rawInput;
      if (showDrop && suggestions.length > 0) {
        finalVal = suggestions[0];
        setRawInput(suggestions[0]);
        onChange(suggestions[0]);
        setSuggestions([]);
        setShowDrop(false);
      }
      if (onSubmit) {
        onSubmit(finalVal);
      }
    }
  };

  const InputEl = multiline ? "textarea" : "input";

  return (
    <div ref={containerRef} style={{ position: "relative", width: "100%" }}>
      {label && (
        <label
          style={{
            display: "block",
            fontSize: 12,
            fontWeight: 600,
            color: "#1a3a5c",
            marginBottom: 4,
            fontFamily: "'Noto Serif Gujarati', serif",
          }}
        >
          {label}
        </label>
      )}

      <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
        <InputEl
          ref={inputRef}
          value={rawInput}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowDrop(true)}
          placeholder={placeholder || "Type in English or ગુજરાતી..."}
          disabled={disabled}
          rows={multiline ? 2 : undefined}
          style={{
            width: "100%",
            border: "1.5px solid #bcd",
            borderRadius: 12,
            padding: "11px 36px 11px 14px",
            fontSize: 15.5,
            fontFamily: "'Noto Serif Gujarati', 'Segoe UI', serif",
            outline: "none",
            resize: "none",
            backgroundColor: disabled ? "#f5f5f5" : "white",
            color: "#1a2a3a",
            boxShadow: "inset 0 1px 3px rgba(0,0,0,0.04)",
          }}
        />
        {/* Indic indicator / loader */}
        <div
          style={{
            position: "absolute",
            right: 12,
            fontSize: 12,
            color: "#888",
            pointerEvents: "none",
          }}
        >
          {loading ? "⏳" : "🔤"}
        </div>
      </div>

      {/* Suggestions dropdown */}
      {showDrop && suggestions.length > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: "calc(100% + 6px)", // Open upwards above input bar
            left: 0,
            right: 0,
            background: "white",
            border: "1.5px solid #bcd",
            borderRadius: 12,
            boxShadow: "0 6px 20px rgba(0,0,0,0.15)",
            zIndex: 9999,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              fontSize: 11,
              fontWeight: 600,
              color: "#1a3a5c",
              padding: "7px 14px",
              background: "#f0f7ff",
              borderBottom: "1px solid #e0ecf8",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>🔡 Gujarati Indic Suggestions:</span>
            <span style={{ fontSize: 10, color: "#888" }}>Click to apply</span>
          </div>
          <div style={{ maxHeight: 180, overflowY: "auto" }}>
            {suggestions.map((s, i) => (
              <div
                key={i}
                onMouseDown={(e) => {
                  e.preventDefault();
                  handleSelect(s);
                }}
                style={{
                  padding: "10px 14px",
                  cursor: "pointer",
                  fontSize: 15,
                  fontFamily: "'Noto Serif Gujarati', serif",
                  borderBottom: i < suggestions.length - 1 ? "1px solid #f0f4f8" : "none",
                  transition: "background 0.15s",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "#e8f4fc")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "white")}
              >
                <span style={{ fontWeight: 600, color: "#1a3a5c" }}>{s}</span>
                <span style={{ fontSize: 11, color: "#999" }}>↵</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
