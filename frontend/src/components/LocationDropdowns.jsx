import { useState, useEffect } from "react";
import { DISTRICTS, getTalukas, getVillages, DEFAULT_DIST } from "../data/locationData";

/**
 * LocationDropdowns — Cascading 3-level dropdown
 * District (જિલ્લો) ➔ Taluka (તાલુકો) ➔ Village (મોજે)
 *
 * Props:
 *   initialValues: { jillo, taluko, moje }
 *   onChange: fn({ jillo, taluko, moje })
 *   onComplete: fn({ jillo, taluko, moje }) — when user clicks Continue
 *   disabled: boolean
 */
export default function LocationDropdowns({
  initialValues = {},
  onChange,
  onComplete,
  disabled = false,
  submitting: externalSubmitting,
}) {
  const [district, setDistrict] = useState(initialValues.jillo || DEFAULT_DIST);
  const [taluko, setTaluko] = useState(initialValues.taluko || "રાજકોટ");
  const [village, setVillage] = useState(initialValues.moje || "");
  const [customVillage, setCustomVillage] = useState("");
  const [internalSubmitting, setInternalSubmitting] = useState(false);

  const submitting = externalSubmitting !== undefined ? externalSubmitting : internalSubmitting;

  const talukas = getTalukas(district);
  const villages = getVillages(district, taluko);

  // Sync initial values only when primitive strings change
  useEffect(() => {
    if (initialValues.jillo) setDistrict(initialValues.jillo);
    if (initialValues.taluko) setTaluko(initialValues.taluko);
    if (initialValues.moje) setVillage(initialValues.moje);
  }, [initialValues.jillo, initialValues.taluko, initialValues.moje]);

  // When district changes ➔ reset taluka and village
  const handleDistrictChange = (e) => {
    const d = e.target.value;
    setDistrict(d);
    const newTalukas = getTalukas(d);
    const firstTaluka = newTalukas.length > 0 ? newTalukas[0].gu : "";
    setTaluko(firstTaluka);
    setVillage("");
    setCustomVillage("");
    if (onChange) {
      onChange({ jillo: d, taluko: firstTaluka, moje: "" });
    }
  };

  // When taluka changes ➔ reset village
  const handleTalukaChange = (e) => {
    const t = e.target.value;
    setTaluko(t);
    setVillage("");
    setCustomVillage("");
    if (onChange) {
      onChange({ jillo: district, taluko: t, moje: "" });
    }
  };

  // When village dropdown changes
  const handleVillageChange = (e) => {
    const v = e.target.value;
    setVillage(v);
    setCustomVillage("");
    if (onChange) {
      onChange({ jillo: district, taluko, moje: v });
    }
  };

  // When custom village text input changes
  const handleCustomVillageChange = (e) => {
    const cv = e.target.value;
    setCustomVillage(cv);
    setVillage(cv);
    if (onChange) {
      onChange({ jillo: district, taluko, moje: cv });
    }
  };

  const handleProceed = () => {
    const finalVillage = (customVillage || village || "").trim();
    if (!district || !taluko || !finalVillage) {
      alert("મહેરબાની કરીને જિલ્લો, તાલુકો અને મોજે ગામ પસંદ કરો / લખો.");
      return;
    }
    setInternalSubmitting(true);
    if (onComplete) {
      onComplete({ jillo: district, taluko, moje: finalVillage });
    }
    setTimeout(() => {
      setInternalSubmitting(false);
    }, 3000);
  };

  const selectStyle = {
    width: "100%",
    border: "1.5px solid #bcd",
    borderRadius: 10,
    padding: "10px 12px",
    fontSize: 15,
    fontFamily: "'Noto Serif Gujarati', 'Segoe UI', serif",
    outline: "none",
    backgroundColor: "white",
    color: "#1a2a3a",
    cursor: "pointer",
  };

  const labelStyle = {
    display: "block",
    fontSize: 12.5,
    fontWeight: 600,
    color: "#1a3a5c",
    marginBottom: 4,
    fontFamily: "'Noto Serif Gujarati', serif",
  };

  const isBtnDisabled = (!village && !customVillage) || submitting || disabled;

  return (
    <div
      style={{
        background: "#f0f7ff",
        border: "1.5px solid #c4dcf0",
        borderRadius: 14,
        padding: 16,
        display: "flex",
        flexDirection: "column",
        gap: 12,
        boxShadow: "0 2px 10px rgba(26,58,92,0.06)",
        width: "100%",
      }}
    >
      <div
        style={{
          fontSize: 13,
          fontWeight: 700,
          color: "#1a3a5c",
          borderBottom: "1px solid #d4e4f2",
          paddingBottom: 6,
          display: "flex",
          alignItems: "center",
          gap: 6,
        }}
      >
        <span>📍</span>
        <span>જમીનનું સ્થળ પસંદ કરો (Select Land Location):</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
        {/* District */}
        <div>
          <label style={labelStyle}>૧. જિલ્લો (District):</label>
          <select
            value={district}
            onChange={handleDistrictChange}
            style={selectStyle}
            disabled={disabled || submitting}
          >
            {DISTRICTS.map((d) => (
              <option key={d.gu} value={d.gu}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        {/* Taluka */}
        <div>
          <label style={labelStyle}>૨. તાલુકો (Taluka):</label>
          <select
            value={taluko}
            onChange={handleTalukaChange}
            style={{ ...selectStyle, backgroundColor: district ? "white" : "#f5f5f5" }}
            disabled={!district || disabled || submitting}
          >
            {talukas.map((t) => (
              <option key={t.gu} value={t.gu}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Village */}
      <div>
        <label style={labelStyle}>૩. મોજે (Village / City):</label>
        <select
          value={villages.some((v) => v.gu === village) ? village : ""}
          onChange={handleVillageChange}
          style={{ ...selectStyle, backgroundColor: taluko ? "white" : "#f5f5f5" }}
          disabled={!taluko || disabled || submitting}
        >
          <option value="">-- મોજે ગામ પસંદ કરો --</option>
          {villages.map((v) => (
            <option key={v.gu} value={v.gu}>
              {v.label}
            </option>
          ))}
        </select>

        {/* Custom village input fallback */}
        <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11.5, color: "#666", whiteSpace: "nowrap" }}>
            અથવા અન્ય ગામ:
          </span>
          <input
            type="text"
            placeholder="જો ગામ યાદીમાં ન હોય તો અહીં લખો..."
            value={customVillage || (!villages.some((v) => v.gu === village) ? village : "")}
            onChange={handleCustomVillageChange}
            disabled={disabled || submitting}
            style={{
              flex: 1,
              border: "1px dashed #9bc",
              borderRadius: 8,
              padding: "6px 10px",
              fontSize: 13.5,
              fontFamily: "'Noto Serif Gujarati', serif",
              outline: "none",
              background: "white",
            }}
          />
        </div>
      </div>

      {/* Proceed button */}
      <button
        type="button"
        onClick={handleProceed}
        disabled={isBtnDisabled}
        style={{
          marginTop: 4,
          background: isBtnDisabled
            ? "#9cb7d4"
            : "linear-gradient(135deg,#1a3a5c,#2768a0)",
          color: "white",
          border: "none",
          borderRadius: 10,
          padding: "12px",
          fontSize: 15,
          fontWeight: 700,
          cursor: isBtnDisabled ? "not-allowed" : "pointer",
          boxShadow: "0 2px 8px rgba(26,58,92,0.2)",
          transition: "background 0.2s",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
        }}
      >
        {submitting ? (
          <span>⏳ કન્ફર્મ થઈ રહ્યું છે... (Saving Location...)</span>
        ) : (
          <span>✓ સ્થળ કન્ફર્મ કરો & આગળ વધો (Confirm Location)</span>
        )}
      </button>
    </div>
  );
}
