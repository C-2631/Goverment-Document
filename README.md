# 📄 Nakal Form Filler — AI Chatbot to Government PDF

> **પરિશિષ્ટ નં.-૫ • નકલ મેળવવાની અરજી ફોર્મ (DLR Land Record Copy Application)**
> An AI-powered bilingual conversational form filler and server-side PDF generator that turns chat conversations into official Gujarat Government Land Record Application PDFs.

---

## 🌟 Features

- **🗣️ Bilingual Conversational Assistant**: Chat in English or Gujarati (`ગુજરાતી`) to fill official government forms step-by-step.
- **🗺️ Comprehensive Gujarat & Rajkot Location Intelligence**:
  - Pre-built authentic Gujarati mappings for all **600+ villages, talukas, and towns** across Rajkot District (e.g. `Vad Vajdi` ➔ `વાજડી વડ`, `Vajdi Virda` ➔ `વાજડી વીરડા`, `Shapar Veraval` ➔ `શાપર વેરાવળ`, `Metoda` ➔ `મેટોડા`, `Bedi` ➔ `બેડી`, `Gunda` ➔ `ગુંદા`, `Khandheri` ➔ `ખંઢેરી`, etc.).
  - Google Translate integration with custom override dictionaries to prevent proper noun mistranslations.
  - Automatic phonetic transliteration with single `'a'` vs `'aa'` distinction.
- **📄 Pixel-Perfect Government PDF Generation**:
  - Generates official Gujarat Land Record (**DLR Parishisht-5**) PDFs using ReportLab canvas overlay on government templates.
  - Authentic **Noto Sans Gujarati** typography embedded with sub-millimeter coordinate alignment.
  - Pre-configured applicant/officer signatures and dynamic Gujarati numeral formatting (`૦-૯`).
- **📱 Clean Modern UI**:
  - Interactive progress indicator.
  - Live summary card previewing collected Gujarati data.
  - Instant PDF preview and one-click download.

---

## 🛠️ Architecture & Tech Stack

```
Chatbot to PDF/
├── backend/                  # FastAPI Application
│   ├── fonts/                # Embedded Noto Sans Gujarati TTF Fonts
│   ├── templates/            # Official DLR Parishisht-5 PDF Template
│   ├── signatures/           # Signature assets
│   ├── chatbot.py            # Chatbot state-machine & translation pipeline
│   ├── pdf_engine.py         # ReportLab + pypdf overlay generator
│   ├── database.py           # SQLite session & history management
│   ├── main.py               # REST API endpoints & CORS configuration
│   └── requirements.txt      # Python dependencies
│
└── frontend/                 # React + Vite Application
    ├── src/
    │   ├── components/
    │   │   └── NakalChatbot.jsx  # Main responsive chat interface
    │   ├── App.jsx
    │   └── main.jsx
    ├── package.json
    ├── vite.config.js
    └── vercel.json           # Vercel deployment config
```

### Stack
- **Frontend**: React 19, Vite, Modern CSS (Inline & Noto Serif Gujarati font)
- **Backend**: FastAPI, Uvicorn, SQLite
- **PDF Generation**: ReportLab, PyPDF
- **Translation**: Google Translate API (`client=gtx`) + Phonetic Rule Engine + Overrides Map

---

## 🚀 Quick Start (Local Development)

### 1. Clone the Repository
```bash
git clone https://github.com/<YOUR-USERNAME>/<YOUR-REPO-NAME>.git
cd "Chatbot to PDF"
```

### 2. Run Backend
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Backend API will be live at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### 3. Run Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend will be running at `http://localhost:5173` (or `http://localhost:3000`).

---

## 🌐 Deployment

### Deploy Backend on [Render](https://render.com)
1. Create a new **Web Service** on Render and connect your repository.
2. Set:
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Copy your deployed backend URL (e.g. `https://chatbot-pdf-backend.onrender.com`).

### Deploy Frontend on [Vercel](https://vercel.com)
1. Import your repository on Vercel.
2. Set:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Add Environment Variable:
   - `VITE_API_BASE_URL` = `https://<YOUR-RENDER-BACKEND-URL>/api`
4. Click **Deploy**.

---

## 📋 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/session` | `POST` | Creates a new user session & returns session key |
| `/api/session` | `GET` | Retrieves current session state & form fields |
| `/api/chat` | `POST` | Processes user message & returns next question |
| `/api/form-data` | `PUT` | Updates form fields directly |
| `/api/pdf/preview` | `GET` | Opens generated filled PDF in browser preview |
| `/api/pdf/download`| `GET` | Downloads the final Parishisht-5 PDF document |

---

## 📄 License
This project is open source and available under the [MIT License](LICENSE).
