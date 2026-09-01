/**
 * Google Indic Input Transliteration Utility
 * Uses Google Inputtools API for Gujarati transliteration
 * Endpoint: https://inputtools.google.com/request
 */

const GOOGLE_INDIC_URL =
  "https://inputtools.google.com/request?text={TEXT}&itc=gu-t-i0-und&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8&app=demopage";

// Comprehensive Local Dictionary for Real-Estate, Addresses, Designations & Places
export const LOCAL_DICTIONARY = {
  // Administrative designations
  "land record inspector": "લેન્ડ રેકોર્ડ ઇન્સ્પેક્ટર",
  "land record": "લેન્ડ રેકોર્ડ",
  "inspector": "ઇન્સ્પેક્ટર",
  "mamlatdar": "મામલતદાર શ્રી",
  "mamlatdar shri": "મામલતદાર શ્રી",
  "daftardar": "દફતરદાર શ્રી",
  "daftardar shri": "દફતરદાર શ્રી",
  "nayab mamlatdar": "નાયબ મામલતદાર",
  "talati": "તલાટી મંત્રી",
  "collector": "જિલ્લા કલેક્ટર",
  "surveyor": "સર્વેયર શ્રી",
  "prant adhikari": "પ્રાંત અધિકારી",

  // Real estate, housing, building & address terms
  "avenue": "એવન્યુ",
  "green avenue": "ગ્રીન એવન્યુ",
  "green": "ગ્રીન",
  "neel": "નીલ",
  "neels": "નીલ્સ",
  "residency": "રેસિડેન્સી",
  "complex": "કોમ્પ્લેક્સ",
  "heights": "હાઇટ્સ",
  "plaza": "પ્લાઝા",
  "arcade": "આર્કેડ",
  "enclave": "એન્ક્લેવ",
  "apartment": "એપાર્ટમેન્ટ",
  "apartments": "એપાર્ટમેન્ટ્સ",
  "flat": "ફ્લેટ",
  "flats": "ફ્લેટ્સ",
  "villa": "વિલા",
  "villas": "વિલાસ",
  "bungalow": "બંગલો",
  "bungalows": "બંગલોઝ",
  "tenament": "ટેનામેન્ટ",
  "tenaments": "ટેનામેન્ટ્સ",
  "heritage": "હેરિટેજ",
  "paradise": "પેરાડાઇઝ",
  "garden": "ગાર્ડન",
  "gardens": "ગાર્ડન્સ",
  "circle": "સર્કલ",
  "square": "સ્ક્વેર",
  "park": "પાર્ક",
  "nagar": "નગર",
  "colony": "કોલોની",
  "society": "સોસાયટી",
  "estate": "એસ્ટેટ",
  "tower": "ટાવર",
  "towers": "ટાવર્સ",
  "road": "રોડ",
  "street": "શેરી",
  "cross road": "ક્રોસ રોડ",
  "bypass": "બાયપાસ",
  "ring road": "રીંગ રોડ",
  "regency": "રીજન્સી",
  "pride": "પ્રાઇડ",
  "elegance": "એલિગન્સ",
  "silver": "સિલ્વર",
  "gold": "ગોલ્ડ",
  "diamond": "ડાયમંડ",
  "sun": "સન",
  "sky": "સ્કાય",
  "star": "સ્ટાર",
  "royal": "રોયલ",
  "classic": "ક્લાસિક",
  "elite": "એલિટ",
  "blue": "બ્લુ",
  "white": "વ્હાઇટ",
  "city": "સીટી",
  "town": "ટાઉન",
  "township": "ટાઉનશીપ",
  "hub": "હબ",
  "point": "પોઇન્ટ",
  "block": "બ્લોક",
  "house": "મકાન",
  "plot": "પ્લોટ",
  "near": "પાસે",
  "opp": "સામે",
  "opposite": "સામે",

  // Major cities & offices
  "rajkot": "રાજકોટ",
  "gondal": "ગોંડલ",
  "jetpur": "જેતપુર",
  "dhoraji": "ધોરાજી",
  "upleta": "ઉપલેટા",
  "jasdan": "જસદણ",
  "morbi": "મોરબી",
  "jamnagar": "જામનગર",
  "surendranagar": "સુરેન્દ્રનગર",
  "junagadh": "જૂનાગઢ",
  "amreli": "અમરેલી",
  "ahmedabad": "અમદાવાદ",

  // Document types
  "tippan": "ટીપ્પણ શીટ",
  "tippan sheet": "ટીપ્પણ શીટ",
  "mapani sheet": "માપણી શીટ",
  "mapani": "માપણી શીટ",
  "sketch": "સ્કેચ / નકશો",
  "7/12": "૭/૧૨ નકલ",
  "8a": "૮-અ નકલ",

  // Common villages
  "vad vajdi": "વાજડી વડ",
  "vajdi vad": "વાજડી વડ",
  "vajdi virda": "વાજડી વીરડા",
  "metoda": "મેટોડા",
  "shapar veraval": "શાપર વેરાવળ",
  "kangasiyali": "કાંગશીયાળી",
  "kothariya": "કોઠારીયા",
  "kuvadva": "કુવાડવા",
  "bedi": "બેડી",
  "ribda": "રીબડા",
  "khandheri": "ખંઢેરી",
  "gunda": "ગુંદા",
  "ghanteshwar": "ઘંટેશ્વર",
  "hadmatala": "હડમતાળા",
};

// Known Google Indic distortion corrections
export const FIX_DISTORTIONS = {
  "વેણુએ": "એવન્યુ",
  "વેન્યુ": "એવન્યુ",
  "અવેણુએ": "એવન્યુ",
};

/**
 * Get Gujarati transliteration suggestions for a Roman input string
 * Uses Google Input Tools API + Local dictionary words & distortion fixers
 * @param {string} text - Roman/English input
 * @returns {Promise<string[]>} - Array of clean Gujarati suggestions
 */
export async function getGujaratiSuggestions(text) {
  if (!text || text.trim().length < 2) return [];

  // If already pure Gujarati Unicode, return as-is
  if (/^[\u0A80-\u0AFF\s\d\.,\/-]+$/.test(text.trim())) {
    return [text];
  }

  const raw = text.trim();
  const clean = raw.toLowerCase();

  // 1. Direct full-phrase match in dictionary
  if (LOCAL_DICTIONARY[clean]) {
    return [LOCAL_DICTIONARY[clean]];
  }

  // 2. Word-by-word substitution base using dictionary
  const words = raw.split(/\s+/);
  let hasWordMatch = false;
  const substitutedWords = words.map((w) => {
    const lw = w.toLowerCase();
    if (LOCAL_DICTIONARY[lw]) {
      hasWordMatch = true;
      return LOCAL_DICTIONARY[lw];
    }
    return w;
  });
  const dictSubstitutedPhrase = substitutedWords.join(" ");

  let suggestions = [];

  // 3. Query Google Indic Input Tools API
  try {
    const url = GOOGLE_INDIC_URL.replace("{TEXT}", encodeURIComponent(raw));
    const res = await fetch(url);
    const data = await res.json();

    if (data?.[0] === "SUCCESS" && data?.[1]?.[0]?.[1]) {
      suggestions = data[1][0][1];
    }
  } catch (err) {
    console.warn("Google Indic Input network fallback:", err);
  }

  // 4. Post-process Google Indic suggestions to fix known distortions (e.g. વેણુએ -> એવન્યુ)
  suggestions = suggestions.map((sug) => {
    let fixed = sug;
    for (const [bad, good] of Object.entries(FIX_DISTORTIONS)) {
      fixed = fixed.split(bad).join(good);
    }
    // Also fix any English words that might remain
    for (const [en, gu] of Object.entries(LOCAL_DICTIONARY)) {
      const reg = new RegExp(`\\b${en}\\b`, "gi");
      fixed = fixed.replace(reg, gu);
    }
    return fixed;
  });

  // 5. If dictionary produced a clean transliterated phrase, ensure it's #1!
  if (hasWordMatch) {
    let cleanBase = dictSubstitutedPhrase;
    for (const [bad, good] of Object.entries(FIX_DISTORTIONS)) {
      cleanBase = cleanBase.split(bad).join(good);
    }
    suggestions = [cleanBase, ...suggestions.filter((s) => s !== cleanBase)];
  }

  // De-duplicate suggestions
  const unique = Array.from(new Set(suggestions.filter(Boolean)));
  return unique.slice(0, 5);
}

/**
 * Filter local suggestions list
 */
export function filterLocalSuggestions(input, localList) {
  if (!input || input.length < 2 || !localList) return [];
  const lower = input.toLowerCase();
  return localList.filter((item) => item.toLowerCase().includes(lower));
}
