# નકલ મેળવવાની અરજી — Chatbot + PDF System

## Overview

A React.js chatbot where the user fills in their details (in Gujarati or English). On submit, a pixel-perfect PDF of "પરિશિષ્ટ નં.-૫ — નકલ મેળવવાની અરજી" is generated with the user's data typed into the exact blank fields, in correct Gujarati script, with proper fonts and alignment.

---

## Architecture

```
nakal-app/
├── public/
│   └── index.html
├── src/
│   ├── App.jsx                  ← Root component, step router
│   ├── components/
│   │   ├── ChatBot.jsx          ← Conversational form UI
│   │   ├── FormField.jsx        ← Single chat bubble + input
│   │   ├── Preview.jsx          ← Live document preview panel
│   │   └── SubmitButton.jsx     ← Download PDF trigger
│   ├── data/
│   │   └── fields.js            ← All form fields with Gujarati labels & positions
│   ├── utils/
│   │   ├── translator.js        ← English → Gujarati transliteration via Claude API
│   │   └── pdfGenerator.js      ← jsPDF + absolute positioning of text on PDF
│   └── index.js
├── server/
│   └── translate.js             ← Node/Express proxy for Claude API (translation)
├── PLAN.md                      ← This file
└── package.json
```

---

## Form Fields (document blanks → input keys)

| Field Key         | Gujarati Label                     | PDF Position (x,y mm) | Max Width |
|-------------------|------------------------------------|------------------------|-----------|
| `applicantName`   | અરજદારનું નામ                     | 105, 38                | 90mm      |
| `address1`        | સરનામું (line 1)                   | 105, 44                | 90mm      |
| `address2`        | સરનામું (line 2)                   | 105, 50                | 90mm      |
| `mobile`          | મોબાઈલ                            | 105, 56                | 90mm      |
| `date`            | તારીખ                             | 105, 62                | 90mm      |
| `toPerson`        | પ્રતિશ્રી (to whom)               | 20, 82                 | 70mm      |
| `toOffice`        | કચેરી / મું.                      | 20, 88                 | 70mm      |
| `moje`            | મોજે                              | 42, 102                | 40mm      |
| `taluko`          | તાલુકો                            | 105, 102               | 50mm      |
| `jillo`           | જ઼ ્ ઼ (જ઼ ્ ઼ ્ ો )                   | 20, 108                | 55mm      |
| `surveyNo`        | સર્વે નં.                          | 95, 108                | 40mm      |
| `signatory`       | સહી કરનાર                        | 90, 120                | 70mm      |
| `mojeSavi`        | મોજે (body)                       | 44, 128                | 40mm      |
| `talukoSavi`      | તાલુકો (body)                     | 100, 128               | 50mm      |
| `jilloSavi`       | જ઼ ્ ઼ ો (body)                       | 20, 134                | 50mm      |
| `surveyNoSavi`    | સર્વે નં. (body)                   | 80, 134                | 35mm      |
| `nakalCount`      | ખરી નકલ નંગ                      | 108, 140               | 20mm      |
| `mtrNo`           | MTR No.                           | 42, 200                | 120mm     |
| `onlineArjiNo`    | ઓન લાઈન અરજી નં.                  | 60, 206                | 100mm     |
| `surveyorName`    | સર્વેયર શ્રી નું નામ              | 58, 212                | 70mm      |
| `mapaniDate`      | માપણી તારીખ                      | 155, 212               | 40mm      |
| `depositAmt`      | ડીપોઝીટ ₹                        | 65, 220                | 50mm      |
| `proxyName`       | નકલો મારા વતી શ્રી (line 2)       | 90, 232                | 80mm      |
| `proxyName3`      | નકલો મારા વતી શ્રી (line 3)       | 90, 238                | 80mm      |

---

## Translation Strategy

### Claude API — English → Gujarati

When a user types in English (detected by script/charset), the app calls the Claude API:

```
POST https://api.anthropic.com/v1/messages
{
  model: "claude-sonnet-4-6",
  max_tokens: 200,
  messages: [{
    role: "user",
    content: "Translate the following into proper Gujarati script only (no romanization, no explanation). 
              Return ONLY the Gujarati text:\n\n\"${userInput}\""
  }]
}
```

- Detection: if input contains only ASCII characters → send to Claude for translation
- If input already contains Gujarati Unicode (0A80–0AFF range) → use as-is
- Output is sanitized and used directly in PDF

---

## PDF Generation (jsPDF)

### Font Setup
- Embed `NotoSerifGujarati-Regular.ttf` as base64 in jsPDF
- Register as custom font: `doc.addFileToVFS() + doc.addFont()`
- Set font before writing any Gujarati text: `doc.setFont('NotoSerifGujarati')`

### Document Template
- The blank A4 document is stored as a base64-encoded background image
- `doc.addImage(templateBase64, 'JPEG', 0, 0, 210, 297)` — full page background
- Then each field value is placed at its absolute (x, y) coordinate

### Text Placement
```js
doc.setFont('NotoSerifGujarati', 'normal');
doc.setFontSize(11);
doc.text(gujaratiValue, x_mm, y_mm, { maxWidth: maxWidth_mm });
```

### Field Overflow
- If text exceeds `maxWidth`, jsPDF wraps to next line automatically
- Multi-line fields (address) have 2 defined y positions

---

## Chatbot UX Flow

```
Step 1:  "નમસ્તે! અરજદારનું નામ શું છે? (What is the applicant's name?)"
         [User types: Ramesh Patel  OR  રમેશ પટેલ]

Step 2:  "સરનામું શું છે? (What is your address?)"

Step 3:  "મોબાઈલ નંબર?"  [numeric keyboard hint]

Step 4:  "તારીખ? (Date)"  [date picker]

Step 5:  "કોને? (To whom is this addressed?)"

Step 6:  "મોજે (Village name)?"

Step 7:  "તાલુકો?"

Step 8:  "જ઼ ્ ઼ ্ ો (District)?"

Step 9:  "સર્વે નં. (Survey Number)?"

Step 10: "ખરી નકલ નંગ (Number of copies required)?"

Step 11: "MTR No. (if applicable)"

Step 12: "ઓન લાઈન અરજી નં. (Online Application No.)"

Step 13: "સર્વેયર નું નામ (Surveyor Name)"

Step 14: "માપણી તારીખ (Measurement Date)"

Step 15: [Preview screen] → [Download PDF button]
```

---

## Changes Made to the Document Template

The original scanned document has these writable blanks:

1. **Top-right block** — અરજદારનું નામ, સરનામું (2 lines), મોબાઈલ, તારીખ
2. **Pratishri block** — 2 lines for addressee name and office
3. **Vishay block** — મોજે, તાલુકો, જ઼ ્ ઼ ો, સર્વે નં.
4. **Body paragraph** — Repeated fields: સહી કરનાર name, મોજે, તાલુકો, જ઼ ્ ઼ ો, સર્વે નં., ખરી નકલ નંગ
5. **Bottom block** — MTR No., ઓન લાઈન અરજી નં., સર્વેયર નામ, માપણી તારીખ, ડીપોઝીટ ₹, proxy names

All blanks are mapped to absolute mm coordinates on the A4 page.

The template itself is **not edited** — only the scanned/rendered JPEG is used as a background layer. User data is drawn on top using jsPDF `doc.text()` at exact pixel positions.

---

## How the PDF is Created (Step-by-Step)

1. **User completes chatbot** → all fields collected in a JS object `formData`
2. **Translation pass** → any English fields sent to Claude API → replaced with Gujarati
3. **PDF init** → `new jsPDF({ unit: 'mm', format: 'a4' })`
4. **Background** → document template added as full-page image
5. **Font** → NotoSerifGujarati embedded and set
6. **Field loop** → for each field key, `doc.text(value, x, y)` placed at predefined coordinates
7. **Save** → `doc.save('nakal_arji.pdf')` triggers browser download

---

## Tech Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Frontend    | React.js (Vite)                     |
| PDF         | jsPDF + embedded Noto Serif Gujarati |
| Translation | Claude API (claude-sonnet-4-6)      |
| Styling     | Tailwind CSS                        |
| Font        | NotoSerifGujarati-Regular.ttf       |

---

## Key Constraints

- **No backend required** — Claude API called directly from browser (API key via env var)
- **Font must be embedded** in jsPDF — not loaded from Google Fonts at runtime
- **All Gujarati text must be Unicode** — no image-based text, no transliteration hacks
- **PDF coordinates must match original document** — test with overlay comparison
- **Mobile-friendly chatbot** — works on phone (Gujarati keyboard supported natively)
