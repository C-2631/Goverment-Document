// Application State
let sessionId = null;
let userApiKey = localStorage.getItem("form_user_api_key") || "";
let formData = {};
let chatHistory = [];
let initialQuestion = "";

// DOM Elements
const pdfFrame = document.getElementById("pdf-frame");
const pdfPlaceholder = document.getElementById("pdf-placeholder-msg");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessagesContainer = document.getElementById("chat-messages-container");
const chatTypingIndicator = document.getElementById("chat-typing-indicator");
const btnDownload = document.getElementById("btn-download");
const btnSettings = document.getElementById("btn-settings");
const btnManual = document.getElementById("btn-manual");
const btnRefreshPdf = document.getElementById("btn-refresh-pdf");
const manualDrawer = document.getElementById("manual-drawer");
const manualForm = document.getElementById("manual-form");
const btnSaveManual = document.getElementById("btn-save-manual");

const settingsModal = document.getElementById("settings-modal");
const btnCloseSettings = document.getElementById("btn-close-settings");
const btnCloseSettingsOk = document.getElementById("btn-close-settings-ok");
const sUserKey = document.getElementById("s-user-key");
const btnCopyUserKey = document.getElementById("btn-copy-user-key");
const sApiSnippet = document.getElementById("s-api-snippet");

const coordsModal = document.getElementById("coords-modal");
const btnCloseCoords = document.getElementById("btn-close-coords");
const btnTestCoords = document.getElementById("btn-test-coords");
const calibrationImg = document.getElementById("calibration-img");
const displayCoordX = document.getElementById("coord-x");
const displayCoordY = document.getElementById("coord-y");
const btnCopyCoords = document.getElementById("btn-copy-coords");

// Initialize application
window.addEventListener("DOMContentLoaded", async () => {
    // Start or load session
    if (userApiKey) {
        await loadSession();
    } else {
        await startNewSession();
    }
    
    // Setup event listeners
    chatForm.addEventListener("submit", handleChatSubmit);
    btnSettings.addEventListener("click", () => toggleModal(settingsModal, true));
    btnCloseSettings.addEventListener("click", () => toggleModal(settingsModal, false));
    btnCloseSettingsOk.addEventListener("click", () => toggleModal(settingsModal, false));
    btnCopyUserKey.addEventListener("click", copyUserKeyToClipboard);
    
    btnManual.addEventListener("click", toggleManualDrawer);
    btnSaveManual.addEventListener("click", saveManualForm);
    btnRefreshPdf.addEventListener("click", refreshPDF);
    btnDownload.addEventListener("click", downloadPDF);
    
    // Coordinate calibration events
    btnTestCoords.addEventListener("click", () => {
        toggleModal(settingsModal, false);
        toggleModal(coordsModal, true);
    });
    btnCloseCoords.addEventListener("click", () => toggleModal(coordsModal, false));
    calibrationImg.addEventListener("click", calculateCoordinates);
    btnCopyCoords.addEventListener("click", copyCoordinatesToClipboard);
});

// Load existing session details using the saved custom API key
async function loadSession() {
    showPDFLoading();
    try {
        const response = await fetch("/api/session", {
            headers: { "X-API-KEY": userApiKey }
        });
        if (!response.ok) {
            // Key is invalid or expired, start a fresh session
            localStorage.removeItem("form_user_api_key");
            userApiKey = "";
            return await startNewSession();
        }
        const data = await response.json();
        sessionId = data.session_id;
        formData = data.form_data;
        chatHistory = data.chat_history;
        initialQuestion = data.initial_question || "";
        
        // Populate settings inputs
        sUserKey.value = userApiKey;
        sApiSnippet.value = `curl -H "X-API-KEY: ${userApiKey}" http://127.0.0.1:8000/api/v1/form-data`;
        
        // Render chat log
        chatMessagesContainer.innerHTML = "";
        if (chatHistory.length === 0) {
            appendBotMessage(
                "નમસ્તે! હું પરિશિષ્ટ-૫ ફોર્મ ભરવામાં તમારી સહાય કરીશ. તમે અંગ્રેજીમાં લખશો તો પણ જવાબ આપમેળે ગુજરાતીમાં ભરાશે.\n(English) Hello! I will help you fill the form. If you type in English, it will be auto-converted to Gujarati."
            );
            if (initialQuestion) {
                appendBotMessage(initialQuestion);
            }
        } else {
            chatHistory.forEach(msg => {
                appendMessage(msg.sender === "user" ? "user" : "bot", msg.message);
            });
        }
        
        populateManualForm(formData);
        refreshPDF();
    } catch (e) {
        console.error("Error loading session:", e);
        appendMessage("system", "સત્ર શરૂ કરવામાં ભૂલ આવી. કૃપા કરીને રીફ્રેશ કરો.");
    }
}

// Start a fresh session and obtain a custom API key
async function startNewSession() {
    showPDFLoading();
    try {
        const response = await fetch("/api/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await response.json();
        sessionId = data.session_id;
        userApiKey = data.user_api_key;
        localStorage.setItem("form_user_api_key", userApiKey);
        formData = data.form_data;
        initialQuestion = data.initial_question || "";
        chatHistory = [];
        
        // Populate settings inputs
        sUserKey.value = userApiKey;
        sApiSnippet.value = `curl -H "X-API-KEY: ${userApiKey}" http://127.0.0.1:8000/api/v1/form-data`;
        
        chatMessagesContainer.innerHTML = "";
        appendBotMessage(
            "નમસ્તે! હું પરિશિષ્ટ-૫ ફોર્મ ભરવામાં તમારી સહાય કરીશ. તમે અંગ્રેજીમાં લખશો તો પણ જવાબ આપમેળે ગુજરાતીમાં ભરાશે.\n(English) Hello! I will help you fill the form. If you type in English, it will be auto-converted to Gujarati."
        );
        if (initialQuestion) {
            appendBotMessage(initialQuestion);
        }
        
        populateManualForm(formData);
        refreshPDF();
    } catch (e) {
        console.error("Error creating session:", e);
        appendMessage("system", "કનેક્શન નિષ્ફળ થયું. કૃપા કરીને સર્વર ચાલુ હોવાની ખાતરી કરો.");
    }
}

// Handle Chat Message Submit
async function handleChatSubmit(e) {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    
    chatInput.value = "";
    appendMessage("user", text);
    
    // Show typing loader
    chatTypingIndicator.style.display = "flex";
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    
    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "X-API-KEY": userApiKey
            },
            body: JSON.stringify({
                message: text
            })
        });
        
        const data = await response.json();
        chatTypingIndicator.style.display = "none";
        
        if (response.ok) {
            appendBotMessage(data.reply);
            formData = data.form_data;
            populateManualForm(formData);
            refreshPDF();
        } else {
            appendMessage("system", `ભૂલ: ${data.detail || "પ્રક્રિયા કરવામાં નિષ્ફળ"}`);
        }
    } catch (err) {
        chatTypingIndicator.style.display = "none";
        appendMessage("system", "સર્વર સાથે જોડાણ થઈ શક્યું નથી.");
        console.error("Chat error:", err);
    }
}

// Send Suggestion text
function sendSuggestion(text) {
    chatInput.value = text;
    chatForm.dispatchEvent(new Event("submit"));
}

// Render message bubbles
function appendMessage(sender, text) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", sender);
    msgDiv.innerText = text;
    chatMessagesContainer.appendChild(msgDiv);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

function appendBotMessage(text) {
    appendMessage("bot", text);
}

// Populate drawer form fields
function populateManualForm(data) {
    for (const key in data) {
        const input = document.getElementById(`f-${key}`);
        if (input) {
            input.value = data[key] || "";
        }
    }
}

// Save manual form overrides
async function saveManualForm() {
    const inputs = manualForm.querySelectorAll("input, textarea");
    const updatedData = {};
    inputs.forEach(input => {
        const fieldName = input.id.replace("f-", "");
        updatedData[fieldName] = input.value;
    });
    
    showPDFLoading();
    try {
        const response = await fetch("/api/form-data", {
            method: "PUT",
            headers: { 
                "Content-Type": "application/json",
                "X-API-KEY": userApiKey
            },
            body: JSON.stringify(updatedData)
        });
        
        const data = await response.json();
        if (response.ok) {
            formData = data.form_data;
            populateManualForm(formData);
            refreshPDF();
            appendMessage("system", "ફોર્મની વિગતો અપડેટ કરવામાં આવી છે.");
        } else {
            appendMessage("system", "અપડેટ નિષ્ફળ થયું.");
        }
    } catch (e) {
        console.error("Save error:", e);
        appendMessage("system", "સર્વર જોડાણ નિષ્ફળ.");
    }
}

// Refresh PDF preview panel
function refreshPDF() {
    if (!userApiKey) return;
    
    // Set source with unique timestamp and custom api key in query params for iframe loading
    const url = `/api/pdf/preview?api_key=${userApiKey}&t=${new Date().getTime()}`;
    pdfFrame.src = url;
    
    pdfFrame.onload = () => {
        pdfPlaceholder.style.display = "none";
        pdfFrame.style.display = "block";
        btnDownload.disabled = false;
    };
}

function showPDFLoading() {
    pdfPlaceholder.style.display = "block";
    pdfFrame.style.display = "none";
    btnDownload.disabled = true;
}

// Download PDF trigger
function downloadPDF() {
    if (!userApiKey) return;
    window.open(`/api/pdf/download?api_key=${userApiKey}`, "_blank");
}

// Modal management
function toggleModal(modal, show) {
    modal.style.display = show ? "flex" : "none";
}

function copyUserKeyToClipboard() {
    sUserKey.select();
    sUserKey.setSelectionRange(0, 99999); // For mobile devices
    
    navigator.clipboard.writeText(sUserKey.value).then(() => {
        btnCopyUserKey.innerText = "Copied!";
        setTimeout(() => {
            btnCopyUserKey.innerText = "Copy";
        }, 1500);
    }).catch(err => {
        console.error("Copy failed:", err);
    });
}

// Collapsible drawer toggle
function toggleManualDrawer() {
    manualDrawer.classList.toggle("open");
}

// Coordinate calculation algorithm (from pixels to PDF points)
function calculateCoordinates(e) {
    const rect = calibrationImg.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;
    
    // Standard PDF size is 595.28 x 841.89
    // X goes from left (0) to right (595.28)
    // Y goes from bottom (0) to top (841.89)
    const pdfX = Math.round((clickX / rect.width) * 595.28);
    const pdfY = Math.round((1 - (clickY / rect.height)) * 841.89);
    
    displayCoordX.innerText = pdfX;
    displayCoordY.innerText = pdfY;
}

function copyCoordinatesToClipboard() {
    const x = displayCoordX.innerText;
    const y = displayCoordY.innerText;
    const text = `(${x}, ${y})`;
    
    navigator.clipboard.writeText(text).then(() => {
        btnCopyCoords.innerText = "Copied!";
        setTimeout(() => {
            btnCopyCoords.innerText = "Copy coordinates";
        }, 1500);
    }).catch(err => {
        console.error("Clipboard copy failed:", err);
    });
}
