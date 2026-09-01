/**
 * Google Indic Input Transliteration Utility
 * Uses Google Inputtools API for Gujarati transliteration
 * Endpoint: https://inputtools.google.com/request
 */

const GOOGLE_INDIC_URL =
  "https://inputtools.google.com/request?text={TEXT}&itc=gu-t-i0-und&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8&app=demopage";

// Comprehensive Local Fallback Dictionary for Offline / Network issues
export const LOCAL_DICTIONARY = {
  // Administrative designations
  "land record inspector": "લેન્ડ રેકોર્ડ ઇન્સ્પેક્ટર",
  "mamlatdar": "મામલતદાર શ્રી",
  "mamlatdar shri": "મામલતદાર શ્રી",
  "daftardar": "દફતરદાર શ્રી",
  "daftardar shri": "દફતરદાર શ્રી",
  "nayab mamlatdar": "નાયબ મામલતદાર",
  "talati": "તલાટી મંત્રી",
  "collector": "જિલ્લા કલેક્ટર",
  "surveyor": "સર્વેયર શ્રી",
  "prant adhikari": "પ્રાંત અધિકારી",

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
  "hadmatala": "હડમતાળા",
};

/**
 * Get Gujarati transliteration suggestions for a Roman input string
 * @param {string} text - Roman/English input
 * @returns {Promise<string[]>} - Array of Gujarati suggestions (up to 5)
 */
export async function getGujaratiSuggestions(text) {
  if (!text || text.trim().length < 2) return [];

  // If already Gujarati Unicode, return as-is
  if (/[\u0A80-\u0AFF]/.test(text)) return [text];

  const clean = text.trim().toLowerCase();
  const directMatch = LOCAL_DICTIONARY[clean];

  try {
    const url = GOOGLE_INDIC_URL.replace("{TEXT}", encodeURIComponent(text.trim()));
    const res = await fetch(url);
    const data = await res.json();

    // Google API response format: ["SUCCESS", [["input", ["sug1","sug2",...]]]]
    if (data?.[0] === "SUCCESS" && data?.[1]?.[0]?.[1]) {
      const sugs = data[1][0][1];
      if (directMatch && !sugs.includes(directMatch)) {
        return [directMatch, ...sugs];
      }
      return sugs;
    }
  } catch (err) {
    console.warn("Indic transliteration API network error, falling back to local dictionary:", err);
  }

  // Fallback to local dictionary
  if (directMatch) return [directMatch];

  const matched = Object.entries(LOCAL_DICTIONARY)
    .filter(([k]) => k.includes(clean) || clean.includes(k))
    .map(([, v]) => v);

  return matched.slice(0, 5);
}

/**
 * Filter local suggestions list
 */
export function filterLocalSuggestions(input, localList) {
  if (!input || input.length < 2 || !localList) return [];
  const lower = input.toLowerCase();
  return localList.filter((item) => item.toLowerCase().includes(lower));
}
