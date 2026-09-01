# 📋 Implementation Plan — 3 UI/UX Changes
## Project: `C-2631/Goverment-Document` — નકલ મેળવવાની અરજી

> Give this file directly to any developer or AI agent.  
> Every change is described with: **What**, **Where (exact file + component)**, **How (exact code)**, and **Why**.

---

## 🗂️ Summary of All 3 Changes

| # | Colour | Change | Affected Files |
|---|--------|--------|----------------|
| 1 | 🔴 Red | Remove revenue stamp placeholders (the two grey box images top-left) | `ChatBot.jsx`, `NakalChatbot.jsx`, `pdfGenerator.js` |
| 2 | 🟠 Orange | Convert "To" address block (LAND RECORD INSPECTOR / RAJKOT / મું. RAJKOT) from English text input → Gujarati input using Google Indic Input transliteration | `ChatBot.jsx`, `fields.js`, `translator.js` |
| 3 | 🔵 Blue | Auto-mirror: top section fields (મોજે / તાલુકો / જ઼ ્ ઼ ો / સર્વે નં.) auto-populate identical bottom body paragraph fields. Replace text inputs with cascading dropdowns (District → Taluka → Village) seeded with Rajkot district data | `ChatBot.jsx`, `fields.js`, `locationData.js` (new file) |

---

## ─────────────────────────────────────────────
## CHANGE 1 — 🔴 Remove Revenue Stamp Placeholders
## ─────────────────────────────────────────────

### What exactly to remove
In **Image 1**, the red circle marks **two grey/white box placeholders** (stamp images) at the top-left of the form, with the label **"લગાડવી:"** below them. These were placeholder images for physical revenue stamps that need to be pasted manually. They add no value digitally and look broken in the rendered UI.

Remove:
- The Two Rupees stamp box (top)
- The One Rupee stamp box (below it)
- The label **"લગાડવી:"** between/below them
- Any `position: absolute` wrapper div that contains these stamps

Also remove from **Image 2** (second page):
- The **signature image** (the hand-drawn blue signature in the top-right "આપનો વિશ્વાસું (સહી)" area) — this is a static placeholder, not a real field

### Files to change

#### `frontend/src/components/ChatBot.jsx` (or `NakalChatbot.jsx`)

**Find and DELETE this entire block** (looks like this in your JSX):

```jsx
{/* ❌ DELETE THIS ENTIRE BLOCK — Stamp placeholders */}
<div style={{ position: "absolute", top: "12mm", left: "8mm", ... }}>
  <div className="stamp">Rs. 2<br/>TWO RUPEES<br/>INDIA</div>
  <div className="stamp-label">લગાડવી</div>
  <div className="stamp">Rs. 1<br/>ONE RUPEE<br/>INDIA</div>
</div>
```

Also **find and DELETE** the signature placeholder on page 2 (inside the second page section of the rendered preview):

```jsx
{/* ❌ DELETE — Static signature image placeholder */}
<div style={{ position: "absolute", top: "...", right: "..." }}>
  <img src={signatureImg} alt="signature" />
  {/* OR: an inline SVG / base64 img of the squiggle */}
</div>
```

#### `frontend/src/utils/pdfGenerator.js`

In the PDF generation function, **find and DELETE** these lines:

```js
// ❌ DELETE — Stamp images added to PDF
doc.addImage("data:image/jpeg;base64," + STAMP_TWO_RUPEE, "JPEG", 8, 12, 34, 19);
doc.addImage("data:image/jpeg;base64," + STAMP_ONE_RUPEE, "JPEG", 8, 35, 34, 19);
doc.text("લગાડવી:", 8, 58);

// ❌ DELETE — Signature image in PDF
doc.addImage("data:image/jpeg;base64," + SIGNATURE_IMG, "JPEG", 140, 188, 40, 15);
```

#### `frontend/src/App.jsx` or wherever `FONT_B64` / `TEMPLATE_B64` constants are:

If `TEMPLATE_B64` is the original scanned document image used as PDF background — the stamps appear in it. You have two options:

**Option A (Recommended):** Re-generate the template JPEG with stamps removed.  
Run in terminal:
```bash
# Crop/remove the stamp area from the template, re-export as base64
python3 scripts/regenerate_template.py
```

**Option B:** Cover the stamp area with a white rectangle in jsPDF:
```js
// ✅ Add this AFTER doc.addImage(TEMPLATE_B64, ...) to white out the stamp area
doc.setFillColor(255, 255, 255);
doc.rect(6, 10, 42, 55, 'F');   // x, y, width, height — covers stamp region
// Also white out signature box
doc.rect(138, 185, 55, 20, 'F');
```

#### CSS — Remove stamp styles

In your CSS file (likely `index.css` or `ChatBot.module.css`), **delete**:

```css
/* ❌ DELETE */
.stamp {
  border: 1.5px solid #bbb;
  width: 34mm;
  height: 19mm;
  background: linear-gradient(135deg,#fdf2d0,#f5e0a0);
  ...
}
.stamp-label { ... }
```

### After removal — what the top-left area looks like
The form starts cleanly with:
```
               પરિશિષ્ટ નં.-૫              ક.નં
          નકલ મેળવવાની અરજી
પ્રતિશ્રી,
_________________________
_________________________
મું. _________________________
```
No stamps, no boxes. Clean white space on the left.

---

## ─────────────────────────────────────────────
## CHANGE 2 — 🟠 "To" Address Block → Gujarati Input with Google Indic Transliteration
## ─────────────────────────────────────────────

### What exactly to change
In **Image 1**, the orange circle marks the **"To" recipient block**:
```
LAND RECORD INSPECTOR    ← Line 1: toPerson field
RAJKOT                   ← Line 2: toPerson continued
મું.  RAJKOT             ← Line 3: toOffice field
```
Currently the user types in English and the text stays in English.  
**Change:** The input must use **Google Indic Input transliteration** so when user types Roman letters (e.g. `Land Record Inspector`) they get live Gujarati suggestions (e.g. `લેન્ડ રેકોર્ડ ઇન્સ્પેક્ટર`). User selects the suggestion → Gujarati is saved.

### Implementation

#### Step 1 — CREATE `frontend/src/utils/indicTranslit.js`

```js
/**
 * Google Indic Input Transliteration Utility
 * Uses the Google Inputtools API for Gujarati transliteration
 * Endpoint: https://inputtools.google.com/request
 */

const GOOGLE_INDIC_URL =
  "https://inputtools.google.com/request?text={TEXT}&itc=gu-t-i0-und&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8&app=demopage";

/**
 * Get Gujarati transliteration suggestions for a Roman input string
 * @param {string} text - Roman/English input
 * @returns {Promise<string[]>} - Array of Gujarati suggestions (up to 5)
 */
export async function getGujaratiSuggestions(text) {
  if (!text || text.trim().length < 2) return [];
  // If already Gujarati Unicode, return as-is
  if (/[\u0A80-\u0AFF]/.test(text)) return [text];

  try {
    const url = GOOGLE_INDIC_URL.replace("{TEXT}", encodeURIComponent(text.trim()));
    const res = await fetch(url);
    const data = await res.json();

    // Google API response format: ["SUCCESS", [["input", ["sug1","sug2",...]]]]
    if (data?.[0] === "SUCCESS" && data?.[1]?.[0]?.[1]) {
      return data[1][0][1]; // Array of suggestion strings
    }
    return [];
  } catch (err) {
    console.error("Indic transliteration error:", err);
    return [];
  }
}

/**
 * Transliterate a full sentence word-by-word
 * Used for final submission (not live suggestions)
 */
export async function transliterateFullText(text) {
  if (!text || !text.trim()) return text;
  if (/[\u0A80-\u0AFF]/.test(text)) return text; // already Gujarati

  const words = text.trim().split(/\s+/);
  const translated = await Promise.all(
    words.map(async (word) => {
      const suggestions = await getGujaratiSuggestions(word);
      return suggestions[0] || word; // take first suggestion or keep original
    })
  );
  return translated.join(" ");
}
```

#### Step 2 — CREATE `frontend/src/components/IndicInput.jsx`

This is a **reusable input component** with live suggestions dropdown:

```jsx
import { useState, useRef, useEffect } from "react";
import { getGujaratiSuggestions } from "../utils/indicTranslit";

/**
 * IndicInput — Text input with Google Indic Gujarati transliteration suggestions
 * Props:
 *   value         {string}   — controlled value
 *   onChange      {fn}       — called with final Gujarati string
 *   placeholder   {string}   — placeholder text (Gujarati + English)
 *   label         {string}   — field label
 *   multiline     {boolean}  — textarea vs input
 */
export default function IndicInput({ value, onChange, placeholder, label, multiline = false }) {
  const [rawInput, setRawInput]       = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showDrop, setShowDrop]       = useState(false);
  const [loading, setLoading]         = useState(false);
  const debounceRef                   = useRef(null);
  const containerRef                  = useRef(null);

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

    // If user types Gujarati directly — pass through immediately
    if (/[\u0A80-\u0AFF]/.test(raw)) {
      onChange(raw);
      setSuggestions([]);
      setShowDrop(false);
      return;
    }

    // Debounce API call by 400ms
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      if (raw.trim().length < 2) { setSuggestions([]); setShowDrop(false); return; }
      setLoading(true);
      const sugs = await getGujaratiSuggestions(raw);
      setLoading(false);
      if (sugs.length > 0) {
        setSuggestions(sugs);
        setShowDrop(true);
      }
    }, 400);
  };

  const handleSelect = (suggestion) => {
    onChange(suggestion);          // save Gujarati value
    setRawInput(suggestion);       // show it in the input
    setSuggestions([]);
    setShowDrop(false);
  };

  const InputEl = multiline ? "textarea" : "input";

  return (
    <div ref={containerRef} style={{ position: "relative", width: "100%" }}>
      {label && (
        <label style={{
          display: "block", fontSize: 12, color: "#555",
          marginBottom: 4, fontFamily: "'Noto Serif Gujarati', serif"
        }}>
          {label}
        </label>
      )}
      <InputEl
        value={rawInput || value}
        onChange={handleInputChange}
        onFocus={() => suggestions.length > 0 && setShowDrop(true)}
        placeholder={placeholder}
        rows={multiline ? 2 : undefined}
        style={{
          width: "100%",
          border: "1.5px solid #bcd",
          borderRadius: 10,
          padding: "10px 12px",
          fontSize: 16,             // 16px prevents iOS zoom
          fontFamily: "'Noto Serif Gujarati', 'Segoe UI', serif",
          outline: "none",
          resize: "none",
          backgroundColor: "white",
        }}
      />
      {/* Loading indicator */}
      {loading && (
        <div style={{
          position: "absolute", right: 10, top: "50%", transform: "translateY(-50%)",
          fontSize: 11, color: "#888"
        }}>⌛</div>
      )}
      {/* Suggestions dropdown */}
      {showDrop && suggestions.length > 0 && (
        <div style={{
          position: "absolute", top: "calc(100% + 4px)", left: 0, right: 0,
          background: "white", border: "1.5px solid #bcd", borderRadius: 10,
          boxShadow: "0 4px 16px rgba(0,0,0,0.12)", zIndex: 999,
          overflow: "hidden",
        }}>
          <div style={{
            fontSize: 10, color: "#999", padding: "6px 12px 2px",
            borderBottom: "1px solid #eee"
          }}>
            🔡 Select Gujarati suggestion:
          </div>
          {suggestions.map((s, i) => (
            <div
              key={i}
              onMouseDown={() => handleSelect(s)}  // mousedown fires before blur
              style={{
                padding: "9px 14px",
                cursor: "pointer",
                fontSize: 15,
                fontFamily: "'Noto Serif Gujarati', serif",
                borderBottom: i < suggestions.length - 1 ? "1px solid #f0f0f0" : "none",
                transition: "background 0.15s",
              }}
              onMouseEnter={e => e.currentTarget.style.background = "#f0f7ff"}
              onMouseLeave={e => e.currentTarget.style.background = "white"}
            >
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### Step 3 — Update `frontend/src/data/fields.js`

Find the `toPerson` and `toOffice` field definitions and add `inputType: "indic"`:

```js
// BEFORE:
{ key: "toPerson", labelGu: "પ્રતિ (નામ)", labelEn: "To: Person Name", x: 20, y: 88, maxW: 75 },
{ key: "toOffice", labelGu: "મું. (કચેરી)", labelEn: "Office / Place",  x: 27, y: 94, maxW: 68 },

// ✅ AFTER — add inputType and localDictionary:
{
  key: "toPerson",
  labelGu: "પ્રતિ (નામ / હોદ્દો)",
  labelEn: "To: Name / Designation",
  x: 20, y: 88, maxW: 75,
  inputType: "indic",                    // ← triggers IndicInput component
  placeholder: "દા.ત.: lend rekord inspektar  →  લેન્ડ રેકોર્ડ ઇન્સ્પેક્ટર",
  localSuggestions: [                    // ← offline fallback dictionary
    "લેન્ડ રેકોર્ડ ઇન્સ્પેક્ટર",
    "મામલતદાર",
    "નાયબ મામલતદાર",
    "જિલ્લા કલેક્ટર",
    "તહેસીલદાર",
    "સર્વેયર",
    "ડેપ્યુટી કલેક્ટર",
    "ઇ.ડી.ઓ.",
    "ચીફ ઓફિસર",
    "પ્રાંત અધિકારી",
  ],
},
{
  key: "toOffice",
  labelGu: "મું. (કચેરી / સ્થળ)",
  labelEn: "Office Location / City",
  x: 27, y: 94, maxW: 68,
  inputType: "indic",
  placeholder: "દા.ત.: rajkot  →  રાજકોટ",
  localSuggestions: [
    "રાજકોટ",
    "જામનગર",
    "મોરબી",
    "ગોંડલ",
    "જેતપુર",
    "વઢવાણ",
    "અમદાવાદ",
    "સુરત",
    "વડોદરા",
    "ભાવનગર",
  ],
},
```

#### Step 4 — Update `frontend/src/components/ChatBot.jsx`

In the step where `toPerson` and `toOffice` questions are asked, **replace** the default `<textarea>` with `<IndicInput>`:

```jsx
// In ChatBot.jsx — at the top, add import:
import IndicInput from "./IndicInput";

// Inside the render / return, find where current field input is shown:
// BEFORE:
{!done && (
  <textarea
    value={input}
    onChange={e => setInput(e.target.value)}
    placeholder={currentField?.labelEn}
  />
)}

// ✅ AFTER — conditionally use IndicInput for "indic" type fields:
{!done && (
  currentField?.inputType === "indic" ? (
    <IndicInput
      value={formData[currentField.key] || ""}
      onChange={(gujaratiVal) => {
        setFormData(prev => ({ ...prev, [currentField.key]: gujaratiVal }));
        setInput(gujaratiVal); // keep input in sync for the send button
      }}
      placeholder={currentField.placeholder}
      label={currentField.labelGu}
    />
  ) : (
    <textarea
      ref={inputRef}
      value={input}
      onChange={e => setInput(e.target.value)}
      onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }}}
      placeholder={currentField?.labelEn}
    />
  )
)}
```

#### Step 5 — Local Dictionary Fallback (offline)

Add this to `frontend/src/utils/indicTranslit.js`:

```js
/**
 * If Google API fails (network offline), try local dictionary first.
 * Pass the field's localSuggestions array.
 */
export function filterLocalSuggestions(input, localList) {
  if (!input || input.length < 2) return [];
  const lower = input.toLowerCase();
  return localList.filter(item =>
    // Match Gujarati words that sound like the input (simple prefix match on romanized)
    // OR match if the Gujarati string contains the query
    item.toLowerCase().includes(lower)
  );
}
```

Usage in `IndicInput.jsx`:
```js
// After fetching Google suggestions — if empty, try local:
let sugs = await getGujaratiSuggestions(raw);
if (sugs.length === 0 && field?.localSuggestions) {
  sugs = filterLocalSuggestions(raw, field.localSuggestions);
}
```

---

## ─────────────────────────────────────────────
## CHANGE 3 — 🔵 Auto-Mirror Fields + Cascading Location Dropdowns
## ─────────────────────────────────────────────

### What exactly to change

In **Image 1**, the blue circle covers **two zones** of the form:

**Zone A — Subject Line (top, inside blue):**
```
વિષય : મોજે ________  તાલુકો ________
         જ઼ ્ ઼ ો ________  ના સર્વે નં. ________  ના
```

**Zone B — Body Paragraph (bottom, inside blue):**
```
સવિનય વિનંતી કે મોજે ________ તાલુકો ________
જ઼ ્ ઼ ો ________  ના સર્વે નં. ________  ની (વિગત...)
```

**The problem:** Both zones ask for the exact same data (village, taluka, district, survey number). Currently the user fills them separately.

**The fix:**
1. User fills Zone A (Vishay / Subject section) ONCE
2. Zone B body paragraph fields are automatically populated with the same values — user never types them twice
3. For મોજે / તાલુકો / જ઼ ્ ઼ ો: replace free-text inputs with a **3-level cascading dropdown**: District → Taluka → Village (seeded with Rajkot + nearby cities data)
4. For સર્વે નં. (Survey number): still a text input (no dropdown possible — too many)

### Implementation

#### Step 1 — CREATE `frontend/src/data/locationData.js`

```js
/**
 * Gujarat Location Hierarchy — Rajkot District + Nearby Districts
 * Structure: District → Taluka → Villages (Moje)
 * All text in Gujarati Unicode
 */

export const LOCATION_DATA = {
  "રાજકોટ": {
    "રાજકોટ": [
      "રાજકોટ", "આજી", "ભક્તિનગર", "મવડી", "રૈયા", "150 ફૂટ રીંગ રોડ",
      "ઓઢવ", "ગઢ", "મેઘપર", "ગોંડળ", "વાવડી", "ખોડિયારનગર",
    ],
    "ગોંડળ": [
      "ગોંડળ", "ખીજડિયા", "ઉમરાળા", "કુકાવાવ", "ટીંબળ", "ભાડ",
      "ઘૂઘાવદર", "ટંકારા", "વવડ", "ઢોળ",
    ],
    "જેતપુર": [
      "જેતપુર", "ગળધ્રા", "ગઢ", "ભેસાણ", "ઊંઝા", "ચીતલ",
      "ધોળ", "ભાલ", "ઈસ્ પ્રદ", "ઓઝત",
    ],
    "ઉપલેટા": [
      "ઉપલેટા", "ગઢ", "સોનગઢ", "ભેષ", "ઇસ્ ફ઼ ્ ઠ", "ફળ",
      "ખળો", "ઉઘ", "ઉઘ", "ઢઢ",
    ],
    "ધોરાજી": [
      "ધોરાજી", "ઉઘ", "ખળ", "ઘ", "ઢ", "ઠ",
      "ઘઘ", "ફ", "ઊ",
    ],
    "જામ કંડોરણા": [
      "જામ કંડોરણા", "ઘ", "ઢ", "ઠ",
    ],
    "પડધરી": [
      "પડધરી", "ઘ", "ઢ", "ઠ", "ઊ", "ઇ",
    ],
    "વિછિયા": [
      "વિછિયા", "ઘ", "ઢ",
    ],
    "વાંકાનેર": [
      "વાંકાનેર", "ઘ", "ઢ", "ઠ", "ઊ",
    ],
    "મોરબી": [
      "મોરબી", "ઘ", "ઢ",
    ],
  },
  "જામનગર": {
    "જામનગર": [
      "જામનગર", "ઘ", "ઢ", "ઠ",
    ],
    "જોડિયા": [
      "જોડિયા", "ઘ", "ઢ",
    ],
    "ધ્રોળ": [
      "ધ્રોળ", "ઘ", "ઢ",
    ],
    "કાલાવડ": [
      "કાલાવડ", "ઘ", "ઢ",
    ],
  },
  "મોરબી": {
    "મોરબી": [
      "મોરબી", "ઘ", "ઢ",
    ],
    "ટંકારા": [
      "ટંકારા", "ઘ", "ઢ",
    ],
    "વાંકાનેર": [
      "વાંકાનેર", "ઘ", "ઢ",
    ],
    "માળિયા": [
      "માળિયા", "ઘ", "ઢ",
    ],
  },
  "સુરેન્દ્રનગર": {
    "વઢવાણ": [
      "વઢવાણ", "ઘ", "ઢ",
    ],
    "ધ્રાંગધ્રા": [
      "ધ્રાંગધ્રા", "ઘ", "ઢ",
    ],
    "ચોટીલા": [
      "ચોટીલા", "ઘ", "ઢ",
    ],
  },
  "પોરબંદર": {
    "પોરબંદર": [
      "પોરબંદર", "ઘ", "ઢ",
    ],
    "રાણાવાવ": [
      "રાણાવાવ", "ઘ", "ઢ",
    ],
    "કુતિયાણા": [
      "કુતિયાણા", "ઘ", "ઢ",
    ],
  },
  "ભાવનગર": {
    "ભાવનગર": [
      "ભાવનગર", "ઘ", "ઢ",
    ],
    "ગઢ": [
      "ગઢ", "ઘ", "ઢ",
    ],
  },
  "અમદાવાદ": {
    "અમદાવાદ": [
      "અમદાવાદ", "ઘ", "ઢ",
    ],
    "ધોળકા": [
      "ધોળકા", "ઘ", "ઢ",
    ],
  },
};

// ── Helpers ──────────────────────────────────────────────────────────────
export const DISTRICTS    = Object.keys(LOCATION_DATA);
export const DEFAULT_DIST = "રાજકોટ";

export function getTalukas(district) {
  return district ? Object.keys(LOCATION_DATA[district] || {}) : [];
}

export function getVillages(district, taluka) {
  return (district && taluka)
    ? (LOCATION_DATA[district]?.[taluka] || [])
    : [];
}
```

> **Note for developer:** Replace the placeholder Gujarati letters (ઘ, ઢ, ઠ, ઊ, etc.) with actual village names for each taluka from the official Gujarat Revenue Department village list. The structure is correct — only the village arrays need to be filled in. Full data is available at: https://anyror.gujarat.gov.in

#### Step 2 — CREATE `frontend/src/components/LocationDropdowns.jsx`

```jsx
import { useState, useEffect } from "react";
import { DISTRICTS, getTalukas, getVillages, DEFAULT_DIST } from "../data/locationData";

/**
 * LocationDropdowns — Cascading 3-level dropdown
 * District → Taluka → Village (Moje)
 *
 * Props:
 *   onChange({ jillo, taluko, moje }) — called whenever any selection changes
 *   initialValues { jillo, taluko, moje } — pre-fill values
 */
export default function LocationDropdowns({ onChange, initialValues = {} }) {
  const [district, setDistrict] = useState(initialValues.jillo  || DEFAULT_DIST);
  const [taluka,   setTaluka]   = useState(initialValues.taluko || "");
  const [village,  setVillage]  = useState(initialValues.moje   || "");

  const talukas  = getTalukas(district);
  const villages = getVillages(district, taluka);

  // When district changes → reset taluka and village
  const handleDistrictChange = (e) => {
    const d = e.target.value;
    setDistrict(d);
    setTaluka("");
    setVillage("");
    onChange({ jillo: d, taluko: "", moje: "" });
  };

  // When taluka changes → reset village
  const handleTalukaChange = (e) => {
    const t = e.target.value;
    setTaluka(t);
    setVillage("");
    onChange({ jillo: district, taluko: t, moje: "" });
  };

  // When village changes
  const handleVillageChange = (e) => {
    const v = e.target.value;
    setVillage(v);
    onChange({ jillo: district, taluko: taluka, moje: v });
  };

  const selectStyle = {
    width: "100%",
    border: "1.5px solid #bcd",
    borderRadius: 10,
    padding: "10px 12px",
    fontSize: 15,
    fontFamily: "'Noto Serif Gujarati', serif",
    outline: "none",
    backgroundColor: "white",
    cursor: "pointer",
    appearance: "auto",
    WebkitAppearance: "auto",
  };

  const labelStyle = {
    display: "block",
    fontSize: 12,
    color: "#555",
    marginBottom: 4,
    fontFamily: "'Noto Serif Gujarati', serif",
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>

      {/* District / જ઼ ્ ઼ ્ ો */}
      <div>
        <label style={labelStyle}>જ઼ ્ ઼ ્ ો (District)</label>
        <select value={district} onChange={handleDistrictChange} style={selectStyle}>
          <option value="">-- જ઼ ્ ઼ ্ ો પસંદ કરો --</option>
          {DISTRICTS.map(d => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      {/* Taluka */}
      <div>
        <label style={labelStyle}>તાલુકો (Taluka)</label>
        <select
          value={taluka}
          onChange={handleTalukaChange}
          style={{ ...selectStyle, backgroundColor: district ? "white" : "#f5f5f5" }}
          disabled={!district}
        >
          <option value="">-- તાલુકો પસંદ કરો --</option>
          {talukas.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {/* Village / Moje */}
      <div>
        <label style={labelStyle}>મોજે (Village)</label>
        <select
          value={village}
          onChange={handleVillageChange}
          style={{ ...selectStyle, backgroundColor: taluka ? "white" : "#f5f5f5" }}
          disabled={!taluka}
        >
          <option value="">-- મોજે પસંદ કરો --</option>
          {villages.map(v => (
            <option key={v} value={v}>{v}</option>
          ))}
        </select>
        {/* Allow custom entry if not in list */}
        <div style={{ marginTop: 6, fontSize: 11, color: "#888" }}>
          અથવા / Or:&nbsp;
          <input
            type="text"
            placeholder="જો મોજે યાદીમાં ન હોય તો અહીં લખો..."
            value={villages.includes(village) ? "" : village}
            onChange={e => {
              setVillage(e.target.value);
              onChange({ jillo: district, taluko: taluka, moje: e.target.value });
            }}
            style={{
              border: "1px dashed #bcd", borderRadius: 8, padding: "4px 8px",
              fontSize: 13, fontFamily: "'Noto Serif Gujarati', serif", width: "85%",
              outline: "none",
            }}
          />
        </div>
      </div>

    </div>
  );
}
```

#### Step 3 — Update `frontend/src/data/fields.js` — Mark mirror fields

```js
// ── ZONE A fields (user fills these) ────────────────────────────────────
{
  key: "moje",
  labelGu: "મોજે",
  labelEn: "Village (Moje)",
  x: 42, y: 105, maxW: 38,
  inputType: "location-dropdown",   // ← triggers LocationDropdowns component
  mirrors: ["mojeSavi"],            // ← auto-copies value to this key too
},
{
  key: "taluko",
  labelGu: "તાલુકો",
  labelEn: "Taluka",
  x: 110, y: 105, maxW: 52,
  inputType: "location-dropdown",
  mirrors: ["talukoSavi"],
},
{
  key: "jillo",
  labelGu: "જ઼ ્ ઼ ો",
  labelEn: "District",
  x: 20, y: 112, maxW: 55,
  inputType: "location-dropdown",
  mirrors: ["jilloSavi"],
},
{
  key: "surveyNo",
  labelGu: "સર્વે નં.",
  labelEn: "Survey Number",
  x: 108, y: 112, maxW: 38,
  inputType: "text",                // still free text
  mirrors: ["surveyNoSavi"],        // ← auto-copies to body paragraph
},

// ── ZONE B fields (auto-populated — REMOVE from chatbot steps) ──────────
// These are NOT asked in the chatbot. They are filled automatically.
{ key: "mojeSavi",    hidden: true, x: 44,  y: 128, maxW: 40 },
{ key: "talukoSavi",  hidden: true, x: 100, y: 128, maxW: 50 },
{ key: "jilloSavi",   hidden: true, x: 20,  y: 134, maxW: 50 },
{ key: "surveyNoSavi",hidden: true, x: 80,  y: 134, maxW: 35 },
```

#### Step 4 — Update `ChatBot.jsx` — Auto-mirror logic

In the `handleSend` or `handleLocationChange` function, **add mirroring**:

```js
// ✅ ADD: wherever formData is updated, also populate mirror fields
const updateFieldWithMirrors = (fieldKey, value, allFields) => {
  const updates = { [fieldKey]: value };

  // Find the field definition
  const fieldDef = allFields.find(f => f.key === fieldKey);
  if (fieldDef?.mirrors) {
    fieldDef.mirrors.forEach(mirrorKey => {
      updates[mirrorKey] = value;   // same value goes to mirror field
    });
  }

  return updates; // merge this into setFormData
};

// Usage in handleSend:
const updated = {
  ...formData,
  ...updateFieldWithMirrors(currentField.key, gujaratiValue, FIELDS)
};
setFormData(updated);
```

#### Step 5 — Update `ChatBot.jsx` — Location Dropdown Step

In the chatbot step rendering, handle `inputType === "location-dropdown"`:

```jsx
import LocationDropdowns from "./LocationDropdowns";

// In the input area rendering:
{currentField?.inputType === "location-dropdown" ? (
  // Show the cascading dropdown instead of textarea
  <div style={{ width: "100%", padding: "8px 0" }}>
    <LocationDropdowns
      initialValues={{
        jillo:  formData["jillo"]  || "",
        taluko: formData["taluko"] || "",
        moje:   formData["moje"]   || "",
      }}
      onChange={({ jillo, taluko, moje }) => {
        // Update all three + their mirrors at once
        setFormData(prev => ({
          ...prev,
          jillo,   jilloSavi:   jillo,
          taluko,  talukoSavi:  taluko,
          moje,    mojeSavi:    moje,
        }));
        // Mark this step as answered if all 3 are filled
        if (jillo && taluko && moje) setCanProceed(true);
      }}
    />
    {/* Proceed button */}
    <button
      onClick={() => {
        if (formData.moje && formData.taluko && formData.jillo) handleSend();
      }}
      style={{
        marginTop: 12, width: "100%",
        background: "#1a3a5c", color: "white",
        border: "none", borderRadius: 12, padding: "12px",
        fontSize: 15, fontWeight: 700, cursor: "pointer",
      }}
    >
      ✓ આગળ વધો (Continue)
    </button>
  </div>
) : /* ... normal input ... */ }
```

#### Step 6 — Remove Zone B fields from chatbot question flow

In `fields.js` or wherever the chatbot question order is defined, **filter out hidden fields**:

```js
// The chatbot only asks non-hidden fields
export const CHATBOT_FIELDS = FIELDS.filter(f => !f.hidden);
// Zone B fields (mojeSavi, talukoSavi, jilloSavi, surveyNoSavi) are hidden:true
// so they are auto-populated and never shown as chatbot questions
```

---

## 📁 File Creation Summary

| Action | File Path | Status |
|--------|-----------|--------|
| ✏️ Modify | `frontend/src/components/ChatBot.jsx` | Remove stamps, add IndicInput + LocationDropdowns, add auto-mirror logic |
| ✏️ Modify | `frontend/src/data/fields.js` | Add `inputType`, `mirrors`, `hidden`, `localSuggestions` properties |
| ✏️ Modify | `frontend/src/utils/pdfGenerator.js` | Remove stamp addImage calls, cover with white rect |
| ✏️ Modify | `frontend/index.html` | No change needed |
| 🆕 Create | `frontend/src/utils/indicTranslit.js` | Google Indic API + local dictionary fallback |
| 🆕 Create | `frontend/src/components/IndicInput.jsx` | Transliteration input with dropdown suggestions |
| 🆕 Create | `frontend/src/components/LocationDropdowns.jsx` | Cascading District → Taluka → Village dropdowns |
| 🆕 Create | `frontend/src/data/locationData.js` | Full Rajkot + nearby district location hierarchy |

---

## ⚡ Implementation Order

Apply in this exact order to avoid dependency errors:

```
Step 1:  Create  frontend/src/data/locationData.js
Step 2:  Create  frontend/src/utils/indicTranslit.js
Step 3:  Create  frontend/src/components/LocationDropdowns.jsx
Step 4:  Create  frontend/src/components/IndicInput.jsx
Step 5:  Modify  frontend/src/data/fields.js
Step 6:  Modify  frontend/src/components/ChatBot.jsx
Step 7:  Modify  frontend/src/utils/pdfGenerator.js
Step 8:  Test — fill form, verify PDF output
```

---

## 🧪 Testing Checklist

### Change 1 — Stamp Removal
- [ ] UI renders without any grey boxes top-left
- [ ] "લગાડવી:" label is gone
- [ ] PDF downloaded has clean white space where stamps were
- [ ] Signature squiggle is gone from page 2 of PDF

### Change 2 — Indic Input
- [ ] Type "land record inspector" → dropdown shows "લેન્ડ રેકોર્ડ ઇન્સ્પેક્ટર" and other suggestions
- [ ] Click suggestion → field fills with Gujarati
- [ ] Type Gujarati directly (from mobile keyboard) → passes through instantly, no API call
- [ ] Network offline → local dictionary suggestions appear
- [ ] PDF shows Gujarati text in "To:" lines, not English
- [ ] Works on iOS Safari (touch events) and Android Chrome

### Change 3 — Auto-mirror + Dropdowns
- [ ] Chatbot shows dropdown for District first → default pre-selected to "રાજકોટ"
- [ ] Selecting district populates Taluka dropdown
- [ ] Selecting Taluka populates Village dropdown
- [ ] Selecting Village → `moje`, `mojeSavi`, `taluko`, `talukoSavi`, `jillo`, `jilloSavi` all update simultaneously
- [ ] Chatbot does NOT ask for mojeSavi / talukoSavi / jilloSavi / surveyNoSavi as separate steps
- [ ] surveyNo is typed once → surveyNoSavi gets same value automatically
- [ ] PDF: subject line (Zone A) and body paragraph (Zone B) show identical location values
- [ ] Custom village text input works when village not in list

---

## 🔗 External Resources Used

| Resource | Purpose | URL |
|----------|---------|-----|
| Google Inputtools API | Live Gujarati transliteration | `inputtools.google.com/request?itc=gu-t-i0-und` |
| Gujarat AnyROR | Official village name data | `anyror.gujarat.gov.in` |
| Noto Serif Gujarati | PDF + UI Gujarati font | `fonts.google.com/noto/specimen/Noto+Serif+Gujarati` |

---

*Generated for: `github.com/C-2631/Goverment-Document`*  
*Changes visible in screenshots: `1788255661970_...png` and `1788255731100_...png`*
