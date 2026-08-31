import datetime
import json
import re
import urllib.parse
import urllib.request
from database import add_chat_message, get_form_data, update_form_data

FIELD_QUESTIONS = [
    (
        "applicant_name",
        "અરજદારનું પૂરું નામ જણાવો (દા.ત. રમેશભાઈ પટેલ):",
        "Please enter applicant full name (e.g. Rameshbhai Patel):",
    ),
    ("address", "અરજદારનું પૂરું સરનામું જણાવો:", "Please enter the full address:"),
    (
        "mobile",
        "અરજદારનો ૧૦-અંકનો મોબાઇલ નંબર જણાવો:",
        "Please enter applicant 10-digit mobile number:",
    ),
    (
        "date",
        "અરજીની તારીખ જણાવો (DD-MM-YYYY) (અથવા આજની તારીખ માટે 'today' લખો):",
        "Please enter application date (DD-MM-YYYY) (or type 'today'):",
    ),
    (
        "to_officer",
        "અરજી કયા અધિકારીશ્રીને કરવાની છે? (દા.ત. મામલતદાર શ્રી / દફતરદાર શ્રી):",
        "To which officer is this application addressed? (e.g. Mamlatdar Shri / Daftardar Shri):",
    ),
    (
        "office_village",
        "કચેરી કયા ગામ/શહેરમાં આવેલી છે તે જણાવો (મું. ગામનું નામ):",
        "Please enter office village/town/city:",
    ),
    (
        "subject_moje",
        "નકલ મેળવવા માટેની જમીન કયા ગામમાં આવેલી છે (મોજે) તે જણાવો:",
        "Please enter land village (Moje):",
    ),
    ("subject_taluko", "જમીનનો તાલુકો જણાવો:", "Please enter land taluka:"),
    ("subject_jillo", "જમીનનો જીલ્લો જણાવો:", "Please enter land district:"),
    (
        "subject_survey_no",
        "જમીનનો સર્વે નંબર જણાવો (દા.ત. ૧૨૪/૧):",
        "Please enter land survey number (e.g. 124/1):",
    ),
    (
        "copy_details",
        "કયા રેકોર્ડની નકલ મેળવવી છે તે જણાવો (દા.ત. ટીપ્પણ / માપણી શીટ / સ્કેચ):",
        "Which record copies are needed? (e.g. Tippan / Measurement Sheet / Sketch):",
    ),
    (
        "copy_quantity",
        "જોઈતી નકલોની સંખ્યા (નંગ) જણાવો (દા.ત. ૧):",
        "Please enter number of copies required (e.g. 1):",
    ),
    (
        "mtr_no",
        "MTR નંબર જણાવો (અથવા સ્કીપ કરવા 'skip' લખો):",
        "Please enter MTR number (or type 'skip'):",
    ),
    (
        "online_app_no",
        "ઓનલાઇન અરજી નંબર જણાવો (અથવા સ્કીપ કરવા 'skip' લખો):",
        "Please enter online application number (or type 'skip'):",
    ),
    (
        "surveyor_name",
        "સર્વેયર શ્રીનું નામ જણાવો (અથવા સ્કીપ કરવા 'skip' લખો):",
        "Please enter surveyor name (or type 'skip'):",
    ),
    (
        "measurement_date",
        "માપણી તારીખ જણાવો (DD-MM-YYYY) (અથવા સ્કીપ કરવા 'skip' લખો):",
        "Please enter measurement date (DD-MM-YYYY) (or type 'skip'):",
    ),
    (
        "deposit_fee",
        "ડીપોઝીટ ફીની રકમ (રૂા.) જણાવો (અથવા સ્કીપ કરવા 'skip' લખો):",
        "Please enter deposit fee amount (INR) (or type 'skip'):",
    ),
    (
        "behalf_name",
        "જો કોઈ અન્ય વ્યક્તિ તમારા વતી નકલ મેળવવાની હોય, તો તેનું નામ જણાવો (અથવા સ્કીપ કરવા 'skip' લખો):",
        "If another person will collect on your behalf, enter their name (or type 'skip'):",
    ),
]

DIGIT_MAP = str.maketrans("0123456789", "૦૧૨૩૪૫૬૭૮૯")

COMMON_TRANSLATIONS = {
    # Rajkot Talukas & Major Towns
    "rajkot": "રાજકોટ",
    "gondal": "ગોંડલ",
    "jetpur": "જેતપુર",
    "dhoraji": "ધોરાજી",
    "upleta": "ઉપલેટા",
    "jasdan": "જસદણ",
    "paddhari": "પડધરી",
    "padadhari": "પડધરી",
    "lodhika": "લોધિકા",
    "kotda sangani": "કોટડા સાંગાણી",
    "kotda-sangani": "કોટડા સાંગાણી",
    "kotda": "કોટડા",
    "sangani": "સાંગાણી",
    "jamkandorna": "જામકંડોરણા",
    "jamkandorana": "જામકંડોરણા",
    "vinchhiya": "વિંછીયા",
    "vinchiya": "વિંછીયા",

    # Rajkot Taluka Villages & Localities
    "vad vajdi": "વાજડી વડ",
    "vajdi vad": "વાજડી વડ",
    "vajdi (vad)": "વાજડી (વડ)",
    "vajdi virda": "વાજડી વીરડા",
    "vajdi (virda)": "વાજડી (વીરડા)",
    "vajdi gadh": "વાજડી ગઢ",
    "vajdi (gadh)": "વાજડી (ગઢ)",
    "vajdi": "વાજડી",
    "vad": "વડ",
    "shapar veraval": "શાપર વેરાવળ",
    "shapar": "શાપર",
    "veraval shapar": "શાપર વેરાવળ",
    "new jagnath": "ન્યુ જગનાથ",
    "jagnath": "જગનાથ",
    "pratik": "પ્રતીક",
    "mavdi": "મવડી",
    "raiya": "રૈયા",
    "nana mava": "નાના મવા",
    "mota mava": "મોટા મવા",
    "kotharia": "કોઠારીયા",
    "kothariya": "કોઠારીયા",
    "ghanteshwar": "ઘંટેશ્વર",
    "madhapar": "માધાપર",
    "bhaktinagar": "ભક્તિનગર",
    "kalawad road": "કાલાવડ રોડ",
    "university road": "યુનિવર્સિટી રોડ",
    "ring road": "રિંગ રોડ",
    "150 feet ring road": "૧૫૦ ફીટ રિંગ રોડ",
    "munjka": "મુંજકા",
    "para pipaliya": "પરા પીપળીયા",
    "kuvadva": "કુવાડવા",
    "kuvadava": "કુવાડવા",
    "bedi": "બેડી",
    "metoda": "મેટોડા",
    "sardhar": "સરધાર",
    "ribda": "રીબડા",
    "maliasan": "માલીયાસણ",
    "maliyasan": "માલીયાસણ",
    "navagam": "નવાગામ",
    "vavdi": "વાવડી",
    "anandpar": "આણંદપર",
    "hadmatiya": "હડમતીયા",
    "kalipat": "કાળીપાટ",
    "kankot": "કણકોટ",
    "khandheri": "ખંઢેરી",
    "kherdi": "ખેરડી",
    "lampasari": "લાંપાસર",
    "lapasari": "લાપાસરી",
    "mahika": "મહિકા",
    "manharpur": "મનહરપુર",
    "nakarawadi": "નાકરાવાડી",
    "gunda": "ગુંદા",
    "gavaridad": "ગવરીદડ",
    "dhamalpar": "ધમલપર",
    "amargadh": "અમરગઢ",
    "virpur": "વીરપુર",
    "bhayavadar": "ભાયાવદર",
    "shapur": "શાહપુર",
    "atkot": "આટકોટ",
    "bhadla": "ભડલા",
    "sanosara": "સણોસરા",
    "kharachiya": "ખારચીયા",
    "gadhka": "ગઢકા",
    "sokhada": "સોખડા",
    "ronki": "રોણકી",
    "targhadiya": "તરઘડીયા",
    "bedla": "બેડલા",
    "hirasar": "હીરાસર",
    "bhupgadh": "ભુપગઢ",
    "ratanpar": "રતનપર",
    "golida": "ગોલીડા",
    "khorana": "ખોરાણા",
    "chitravav": "ચિત્રાવાવ",
    "aniyara": "અણીયારા",
    "dhandhiya": "ધાંધીયા",
    "padasan": "પાડાસણ",
    "lothda": "લોઠડા",
    "hodthali": "હોડથલી",
    "jiyana": "જીયાણા",
    "dhandhani": "ધાંધણી",
    "mesvada": "મેસવડા",
    "lakhapar": "લાખાપર",
    "bhayasar": "ભાયાસર",

    # Lodhika Taluka Villages
    "abhepar": "અભેપર",
    "balsar": "બાલસર",
    "chandli": "ચાંદલી",
    "chapra": "છાપરા",
    "chibhda": "ચીભડા",
    "devgam": "દેવગામ",
    "devla": "દેવલા",
    "dholra": "ઢોલરા",
    "dhudiya domda": "ધુડીયા દોમડા",
    "haripar pal": "હરિપર પાળ",
    "haripar taravada": "હરિપર તારાવાડા",
    "haripar": "હરિપર",
    "jasvantpur": "જશવંતપુર",
    "jetkuba": "જેતકુબા",
    "kangasiyali": "કાંગશીયાળી",
    "khamba khirsara": "ખાંભાખીરસરા",
    "kotha pipaliya": "કોઠા પીપળીયા",
    "lakshmi intala": "લક્ષ્મી ઇંટાળા",
    "makhawad": "માખાવાડ",
    "motavada": "મોટાવાડા",
    "nonghanchora": "નંઘણચોરા",
    "nadhu pipaliya": "નાધુ પીપળીયા",
    "nagar pipliya": "નગર પીપલીયા",
    "pal": "પાળ",
    "pambhar intala": "પાંભર ઇંટાળા",
    "pardi": "પારડી",
    "pipaliya pal": "પીપળીયા પાળ",
    "pipardi": "પીપરડી",
    "rataiya": "રતૈયા",
    "ravki": "રાવકી",
    "sadak pipaliya": "સડક પિપળિયા",
    "sanganwa": "સાંગણવા",
    "taravada": "તારાવાડા",
    "und khijadiya": "ઉંડ ખીજડીયા",
    "vagudal": "વાગુદળ",
    "veerveri": "વીરવી",

    # Kotda Sangani Taluka Villages
    "hadmatala": "હડમતાળા",
    "ardoi": "અરડોઈ",
    "soliya": "સોળીયા",
    "naranka": "નારણકા",
    "rajpara": "રાજપરા",
    "bhadai": "ભાડાઈ",
    "develiya": "દેવળીયા",
    "bhadwa": "ભાડવા",
    "khokhari": "ખોખરી",
    "champabeda": "ચાંપાબેડા",
    "manekwada": "માણેકવાડા",
    "khareda": "ખરેડા",
    "ramod": "રામોદ",
    "shishak": "શીશક",
    "satapar": "સતાપર",
    "kalambhdi": "કાલંભડી",
    "sandhavaya": "સાંઢવાયા",
    "detdiya": "દેતડીયા",
    "bagdadiya": "બગદડીયા",
    "karmal pipaliya": "કરમાળ પીપળીયા",
    "nana mandwa": "નાના માંડવા",
    "vadipara": "વાદીપરા",
    "nawa rajpipla": "નવા રાજપીપળા",
    "juni mengani": "જુની મેંગણી",
    "navi mengani": "નવી મેંગણી",
    "mengani": "મેંગણી",
    "ambliyala": "આંબલીયાળા",
    "anida": "અનીડા",
    "thordi": "થોરડી",
    "rampara": "રામપરા",
    "piplana": "પીપલાણા",
    "padvala": "પડવલા",

    # Paddhari Taluka Villages
    "adbalaka": "અડબાલકા",
    "baghi": "બાઘી",
    "bodi dhodi": "બોડી ધોડી",
    "dahisarda": "દહીસરડા",
    "depaliya": "દેપાલીયા",
    "dhokliya": "ઢોકળીયા",
    "fatepar": "ફતેપર",
    "gadhada": "ગઢડા",
    "govindpar": "ગોવીંદપર",
    "hidad": "હીદડ",
    "ishvariya": "ઇશ્વરીયા",
    "jilriya": "જીલરીયા",
    "jivapar": "જીવાપર",
    "jodhpur chhala": "જોધપુર છાલા",
    "kerala": "કેરાળા",
    "khajurdi": "ખજુરડી",
    "khambhala": "ખંભાળા",
    "khamta": "ખામટા",
    "khodapiper": "ખોડાપીપર",
    "movi": "મોવી",
    "nyara": "ન્યારા",
    "radad": "રાદડ",
    "rangpar": "રંગપર",
    "rojiya": "રોજીયા",
    "rupavati": "રૂપાવટી",
    "sal pipaliya": "સાલ પીપળીયા",
    "sarapdad": "સરપદડ",
    "suvag": "સુવાગ",
    "targhadi": "તરધડી",
    "thoriyali": "થોરીયાળી",
    "ukurda": "ઉકરડા",
    "vanpari": "વણપરી",

    # Gondal Taluka Villages
    "ambardi": "અંબારડી",
    "analgadh": "અનલગઢ",
    "bandhiya": "બાંધીયા",
    "bandra": "બાંદરા",
    "bhandariya": "ભંડારીયા",
    "bharudi": "ભારુડી",
    "bhojpura": "ભોજપુરા",
    "biliyal": "બીલીયાળા",
    "biliyala": "બીલીયાળા",
    "charkhadi": "ચરખડી",
    "chordi": "ચોરડી",
    "dadwa": "દડવા",
    "derdi kumbhaji": "દેરડી કુંભાજી",
    "derdi": "દેરડી",
    "devchadi": "દેવચડી",
    "ghoghavadar": "ઘોઘાવદર",
    "gomta": "ગોમતા",
    "gundala": "ગુંદાળા",
    "gundasara": "ગુંદાસરા",
    "jamvali": "જામવળી",
    "kamadhya": "કમાઢિયા",
    "kantoliya": "કાંટોળીયા",
    "keshavala": "કેશવાળા",
    "khambhalida": "ખંભાલીડા",
    "kolithad": "કોલીથડ",
    "lilakha": "લીલાખા",
    "lunivav": "લુણીવાવ",
    "moviya": "મોવીયા",
    "pachiyavadar": "પાંચિયાવદર",
    "patidad": "પાટીદડ",
    "patikhilori": "પાટખીલોરી",
    "shivrajgadh": "શિવરાજગઢ",
    "shrinathgadh": "શ્રીનાથગઢ",
    "sultanpur": "સુલતાનપુર",
    "trakuda": "ત્રાકુડા",
    "vasavad": "વાસાવડ",
    "vekuria": "વેકરી",
    "vorakotda": "વોરાકોટડા",

    # Nearby Districts & Major Cities of Gujarat
    "morbi": "મોરબી",
    "jamnagar": "જામનગર",
    "junagadh": "જૂનાગઢ",
    "amreli": "અમરેલી",
    "bhavnagar": "ભાવનગર",
    "surendranagar": "સુરેન્દ્રનગર",
    "porbandar": "પોરબંદર",
    "botad": "બોટાદ",
    "devbhumi dwarka": "દેવભૂમિ દ્વારકા",
    "dwarka": "દ્વારકા",
    "gir somnath": "ગીર સોમનાથ",
    "somnath": "સોમનાથ",
    "veraval": "વેરાવળ",
    "kutch": "કચ્છ",
    "kachchh": "કચ્છ",
    "bhuj": "ભુજ",
    "gandhidham": "ગાંધીધામ",
    "ahmedabad": "અમદાવાદ",
    "amdavad": "અમદાવાદ",
    "gandhinagar": "ગાંધીનગર",
    "vadodara": "વડોદરા",
    "baroda": "વડોદરા",
    "surat": "સુરત",
    "anand": "આણંદ",
    "bharuch": "ભરૂચ",
    "mehsana": "મહેસાણા",
    "patan": "પાટણ",
    "valsad": "વલસાડ",
    "navsari": "નવસારી",
    "tapi": "તાપી",
    "dahod": "દાહોદ",
    "dang": "ડાંગ",
    "kheda": "ખેડા",
    "mahisagar": "મહીસાગર",
    "narmada": "નર્મદા",
    "panchmahal": "પંચમહાલ",
    "sabarkantha": "સાબરકાંઠા",
    "aravalli": "અરવલ્લી",
    "banaskantha": "બનાસકાંઠા",
    "chhota udepur": "છોટા ઉદેપુર",
    "chhota udaipur": "છોટા ઉદેપુર",
    "wankaner": "વાંકાનેર",
    "tankara": "ટંકારા",
    "halvad": "હળવદ",
    "dhrangadhra": "ધ્રાંગધ્રા",
    "limbdi": "લીંબડી",
    "chotila": "ચોટીલા",
    "mahuva": "મહવા",
    "kodinar": "કોડીનાર",
    "khambhalia": "ખંભાળિયા",
    "bhanvad": "ભાનવડ",
    "manavadar": "માણાવદર",
    "keshod": "કેશોદ",
    "mangrol": "માળિયા",
    "maliya": "માળિયા",
    "una": "ઉના",
    "kalawad": "કાલાવડ",
    "lathi": "લાઠી",
    "babra": "બાબરા",
    "bagasara": "બગસરા",
    "savarkundla": "સાવરકુંડલા",
    "dhari": "ધારી",
    "rajula": "રાજુલા",
    "jafrabad": "જાફરાબાદ",
    "palitana": "પાલીતાણા",
    "gariadhar": "ગારિયાધર",
    "sihor": "સિહોર",
    "talaja": "તળાજા",
    "vallabhipur": "વલ્લભીપુર",

    # Offices & Administrative Designations
    "mamlatdar shri": "મામલતદાર શ્રી",
    "daftardar shri": "દફતરદાર શ્રી",
    "district collector": "જિલ્લા કલેક્ટર",
    "deputy collector": "નાયબ કલેક્ટર",
    "prant officer": "પ્રાંત અધિકારી",
    "land record inspector": "જમીન દફતર નિરીક્ષક",
    "land record": "જમીન દફતર",
    "dlr": "ડી.એલ.આર.",
    "city survey superintendent": "સીટી સર્વે સુપ્રિન્ટેન્ડન્ટ",
    "city survey": "સીટી સર્વે",
    "surveyor shri": "સર્વેયર શ્રી",
    "talati cum mantri": "તલાટી કમ મંત્રી",
    "talati": "તલાટી",
    "circle officer": "સર્કલ ઓફિસર",
    "sub registrar": "સબ રજિસ્ટ્રાર",
    "resident additional collector": "નિવાસી અધિક કલેક્ટર",
    "mamlatdar office": "મામલતદાર કચેરી",
    "jan seva kendra": "જન સેવા કેન્દ્ર",
    "seva sadan": "સેવા સદન",
    "bahumali bhavan": "બહુમાળી ભવન",
    "collector office": "કલેક્ટર કચેરી",

    # Address Terms & Building Types
    "house no": "મકાન નં.",
    "house number": "મકાન નંબર",
    "flat no": "ફ્લેટ નં.",
    "flat number": "ફ્લેટ નંબર",
    "block no": "બ્લોક નં.",
    "block number": "બ્લોક નંબર",
    "plot no": "પ્લોટ નં.",
    "plot number": "પ્લોટ નંબર",
    "main road": "મેઇન રોડ",
    "bypass road": "બાયપાસ રોડ",
    "cross road": "ક્રોસ રોડ",
    "railway station": "રેલવે સ્ટેશન",
    "bus stand": "બસ સ્ટેન્ડ",
    "bus station": "બસ સ્ટેશન",
    "national highway": "નેશનલ હાઇવે",
    "highway": "હાઇવે",
    "colony": "કોલોની",
    "apartment": "એપાર્ટમેન્ટ",
    "flat": "ફ્લેટ",
    "house": "મકાન",
    "sector": "સેક્ટર",
    "bazar": "બજાર",
    "chowk": "ચોક",
    "station": "સ્ટેશન",
    "pincode": "પિનકોડ",
    "pin": "પિન",
    "road": "રોડ",
    "street": "શેરી",
    "plot": "પ્લોટ",
    "society": "સોસાયટી",
    "moje": "મોજે",

    # Survey & Land Numbers
    "survey no": "સર્વે નંબર",
    "survey number": "સર્વે નંબર",
    "city survey no": "સીટી સર્વે નંબર",
    "city survey number": "સીટી સર્વે નંબર",
    "khata no": "ખાતા નંબર",
    "khata number": "ખાતા નંબર",
    "tp no": "ટી.પી. નંબર",
    "tp scheme": "ટી.પી. સ્કીમ",
    "fp no": "એફ.પી. નંબર",
    "final plot": "ફાઇનલ પ્લોટ",
    "paiki": "પૈકી",
    "piki": "પૈકી",
    "sub division": "સબ ડિવિઝન",
    "re survey": "રી સર્વે",
    "re-survey": "રી સર્વે",

    # Document & Record Copies
    "tippan sheet": "ટીપ્પણ શીટ",
    "tippan": "ટીપ્પણ",
    "mapani sheet": "માપણી શીટ",
    "mapani": "માપણી",
    "sketch": "સ્કેચ",
    "sheet": "શીટ",
    "village form 7/12": "ગામ નમૂના નંબર ૭/૧૨",
    "village form 8a": "ગામ નમૂના નંબર ૮-અ",
    "village form 6": "ગામ નમૂના નંબર ૬",
    "village form": "ગામ નમૂનો",
    "hak patrak": "હક પત્રક",
    "ferfar nond": "ફેરફાર નોંધ",
    "niyamit mapani": "નિયમિત માપણી",
    "gunakar": "ગુણાકાર",
    "kami jasti patrak": "કમી જાસ્તી પત્રક",
    "khasra": "ખસરા",
    "promulgation entry": "પ્રમોલ્ગેશન નોંધ",
    "city survey map": "સીટી સર્વે નકશો",
    "dlr map": "ડી.એલ.આર. નકશો",
    "measurement sheet": "માપણી શીટ",
    "partition deed": "વહેંચણી લેખ",
    "sanad": "સનદ",
    "order copy": "હુકમ નકલ",
    "judgment copy": "ચુકાદા નકલ",
    "khedut khatu": "ખેડૂત ખાતું",
    "copies": "નકલો",
    "copy": "નકલ",
    "nakal": "નકલ",

    # English Numbers to Gujarati
    "one": "૧",
    "two": "૨",
    "three": "૩",
    "four": "૪",
    "five": "૫",
    "six": "૬",
    "seven": "૭",
    "eight": "૮",
    "nine": "૯",
    "ten": "૧૦",
    "nang": "નંગ",

    # Currency & Fee terms
    "rupees": "રૂપિયા",
    "rupee": "રૂપિયા",
    "rs": "રૂા.",
    "inr": "રૂા.",
    "deposit": "ડીપોઝીટ",
    "fee": "ફી",
    "fees": "ફી",

    # Surnames & Family Names
    "kheradiya": "ખેરાડીયા",
    "kheradiyaa": "ખેરાડીયા",
    "patel": "પટેલ",
    "shah": "શાહ",
    "joshi": "જોશી",
    "mehta": "મહેતા",
    "trivedi": "ત્રિવેદી",
    "parmar": "પરમાર",
    "rathod": "રાઠોડ",
    "jadeja": "જાડેજા",
    "chavda": "ચાવડા",
    "chavada": "ચાવડા",
    "vaghela": "વાઘેલા",
    "vaghelaa": "વાઘેલા",
    "gohil": "ગોહિલ",
    "zala": "ઝાળા",
    "jhala": "ઝાલા",
    "solanki": "સોલંકી",
    "makwana": "મકવાણા",
    "makawana": "મકવાણા",
    "kanzariya": "કાંજરીયા",
    "sarvaiya": "સરવૈયા",
    "bhatt": "ભટ્ટ",
    "dave": "દવે",
    "prajapati": "પ્રજાપતિ",
    "suthar": "સુથાર",
    "luhar": "લુહાર",
    "mistry": "મિસ્તરી",
    "mistri": "મિસ્તરી",
    "darji": "દરજી",
    "maru": "મારુ",
    "vadher": "વાઢેર",
    "kalsariya": "કાળસરીયા",
    "sorathiya": "સોરઠીયા",
    "barad": "બારડ",
    "chothani": "ચોથાણી",
    "domadiya": "ડોમડીયા",
    "pedhadiya": "પેઢડીયા",
    "dobariya": "ડોબરીયા",
    "vachhani": "વાછાણી",
    "gajera": "ગજેરા",
    "bhalodiya": "ભાલોડીયા",
    "detroja": "દેતરોજા",
    "radadiya": "રાડાડીયા",
    "vasoya": "વસોયા",
    "savaliya": "સાવલીયા",
    "hirpara": "હિરપરા",
    "kakadiya": "કાકડીયા",
    "dhaduk": "ધાડુક",
    "chunara": "ચૂનારા",
    "raiyani": "રાયયાણી",
    "tanti": "તાંતિ",
    "bhesaniya": "ભેસાણીયા",
    "virani": "વીરાણી",
    "vavadiya": "વાવડીયા",
    "mangroliya": "માંગરોળીયા",
    "pipaliya": "પીપળીયા",
    "chodavadiya": "ચોડવડીયા",
    "khunt": "ખૂંટ",
    "donga": "ડોંગા",
    "ghori": "ઘોરી",
    "ramani": "રામાણી",
    "faldu": "ફળદુ",
    "thummar": "ઠુમ્મર",
    "chovatia": "ચોવટીયા",
    "chovatiya": "ચોવટીયા",
    "bhuva": "ભુવા",
    "tarpara": "તરપરા",
    "baladha": "બળાધા",
    "vaghasiya": "વાઘાસીયા",
    "kasundra": "કાસુંદ્રા",
    "godhani": "ગોધાણી",
    "panchani": "પંચાણી",
    "kotadiya": "કોટાડીયા",
    "dudhat": "દૂધાત",
    "mavani": "માવાણી",
    "sutariya": "સુતરીયા",
    "lathiya": "લાઠીયા",
    "sanghani": "સાંઘાણી",
    "sojitra": "સોજીત્રા",
    "kikani": "કીકાણી",
    "der": "ડેર",
    "moradiya": "મોરાડીયા",
    "vekariya": "વેકરીયા",

    # First Names & Common Honorifics
    "gajrajsinh": "ગજરાજસિંહ",
    "gajraj": "ગજરાજ",
    "gajrajsinhji": "ગજરાજસિંહજી",
    "ramesh": "રમેશ",
    "rameshbhai": "રમેશભાઈ",
    "suresh": "સુરેશ",
    "sureshbhai": "સુરેશભાઈ",
    "dinesh": "દિનેશ",
    "dineshbhai": "દિનેશભાઈ",
    "rajesh": "રાજેશ",
    "rajeshbhai": "રાજેશભાઈ",
    "mahesh": "મહેશ",
    "maheshbhai": "મહેશભાઈ",
    "naresh": "નરેશ",
    "nareshbhai": "નરેશભાઈ",
    "vijay": "વિજય",
    "vijaybhai": "વિજયભાઈ",
    "sanjay": "સંજય",
    "sanjaybhai": "સંજયભાઈ",
    "jayesh": "જયેશ",
    "jayeshbhai": "જયેશભાઈ",
    "pankaj": "પંકજ",
    "pankajbhai": "પંકજભાઈ",
    "alpesh": "અલ્પેશ",
    "alpeshbhai": "અલ્પેશભાઈ",
    "bhavesh": "ભાવેશ",
    "bhaveshbhai": "ભાવેશભાઈ",
    "hitesh": "હિતેશ",
    "hiteshbhai": "હિતેશભાઈ",
    "jignesh": "જીજ્ઞેશ",
    "jigneshbhai": "જીજ્ઞેશભાઈ",
    "kamlesh": "કમલેશ",
    "kamleshbhai": "કમલેશભાઈ",
    "nilesh": "નિલેશ",
    "nileshbhai": "નિલેશભાઈ",
    "paresh": "પરેશ",
    "pareshbhai": "પરેશભાઈ",
    "shailesh": "શૈલેષ",
    "shaileshbhai": "શૈલેષભાઈ",
    "yogesh": "યોગેશ",
    "yogeshbhai": "યોગેશભાઈ",
    "harish": "હરીશ",
    "harishbhai": "હરીશભાઈ",
    "gautam": "ગૌતમ",
    "gautambhai": "ગૌતમભાઈ",
    "bharat": "ભરત",
    "bharatbhai": "ભરતભાઈ",
    "pravin": "પ્રવીણ",
    "pravinbhai": "પ્રવીણભાઈ",
    "ashok": "અશોક",
    "ashokbhai": "અશોકભાઈ",
    "mansukh": "મનસુખ",
    "mansukhbhai": "મનસુખભાઈ",
    "kanu": "કાનુ",
    "kanubhai": "કાનુભાઈ",
    "chaggan": "છગન",
    "chagganbhai": "છગનભાઈ",
    "chagan": "છગન",
    "chaganbhai": "છગનભાઈ",
    "mohan": "મોહન",
    "mohanbhai": "મોહનભાઈ",
    "jadav": "જાદવ",
    "jadavbhai": "જાદવભાઈ",
    "gopal": "ગોપાલ",
    "gopalbhai": "ગોપાલભાઈ",
    "gopaldas": "ગોપાલદાસ",
    "kisan": "કિશન",
    "kisanbhai": "કિશનભાઈ",
    "kishan": "કિશન",
    "kishanbhai": "કિશનભાઈ",
    "kiran": "કિરણ",
    "kiranbhai": "કિરણભાઈ",
    "chetan": "ચેતન",
    "chetanbhai": "ચેતનભાઈ",
    "ketan": "કેતન",
    "ketanbhai": "કેતનભાઈ",
    "nitin": "નિતિન",
    "nitinbhai": "નિતિનભાઈ",
    "mukul": "મુકુલ",
    "mukulbhai": "મુકુલભાઈ",
    "anand": "આણંદ",
    "anandbhai": "આણંદભાઈ",
    "tarun": "તરુણ",
    "tarunbhai": "તરુણભાઈ",
    "varun": "વરુણ",
    "varunbhai": "વરુણભાઈ",
    "arun": "અરુણ",
    "arunbhai": "અરુણભાઈ",
    "babulal": "બાબુલાલ",
    "chiman": "ચિમન",
    "chimanbhai": "ચિમનભાઈ",
    "dahyabhai": "ડહ્યાભાઈ",
    "magan": "મગન",
    "maganbhai": "મગનભાઈ",
    "chhotubhai": "છોટુભાઈ",
    "popat": "પોપટ",
    "popatbhai": "પોપટભાઈ",
    "karsan": "કરશન",
    "karsanbhai": "કરશનભાઈ",
    "narayan": "નારાયણ",
    "narayanbhai": "નારાયણભાઈ",
    "vrajlal": "વ્રજલાલ",
    "gordhan": "ગોરધન",
    "gordhanbhai": "ગોરધનભાઈ",
    "parsottam": "પરસોત્તમ",
    "parsottambhai": "પરસોત્તમભાઈ",
    "parshottam": "પર્ષોત્તમ",
    "purshottam": "પુરુષોત્તમ",
    "khoda": "ખોડા",
    "khodabhai": "ખોડાભાઈ",
    "naran": "નારણ",
    "naranbhai": "નારણભાઈ",
    "devraj": "દેવરાજ",
    "devrajbhai": "દેવરાજભાઈ",
    "dhanji": "ધનજી",
    "dhanjibhai": "ધનજીભાઈ",
    "mulji": "મૂળજી",
    "muljibhai": "મૂળજીભાઈ",
    "bhagvanji": "ભગવાનજી",
    "bhagvanjibhai": "ભગવાનજીભાઈ",
    "valji": "વાલજી",
    "valjibhai": "વાલજીભાઈ",
    "kanji": "કાનજી",
    "kanjibhai": "કાનજીભાઈ",
    "mavji": "માવજી",
    "mavjibhai": "માવજીભાઈ",
    "ramji": "રામજી",
    "ramjibhai": "રામજીભાઈ",
    "shamji": "શામજી",
    "shamjibhai": "શામજીભાઈ",
    "shavji": "શાવજી",
    "shavjibhai": "શાવજીભાઈ",
    "khemji": "ખેમજી",
    "khemjibhai": "ખેમજીભાઈ",
    "gokul": "ગોકુલ",
    "gokulbhai": "ગોકુલભાઈ",
    "geeta": "ગીતા",
    "geetaben": "ગીતાબેન",
    "gitaben": "ગીતાબેન",
    "sita": "સીતા",
    "sitaben": "સીતાબેન",
    "rita": "રીટા",
    "ritaben": "રીટાબેન",
    "nita": "નીતા",
    "nitaben": "નીતાબેન",
    "sunita": "સુનિતા",
    "sunitaben": "સુનિતાબેન",
    "anita": "અનિતા",
    "anitaben": "અનિતાબેન",
    "kavita": "કવિતા",
    "kavitaben": "કવિતાબેન",
    "savita": "સવિતા",
    "savitaben": "સવિતાબેન",
    "sharda": "શારદા",
    "shardaben": "શારદાબેન",
    "laxmi": "લક્ષ્મી",
    "laxmiben": "લક્ષ્મીબેન",
    "kashiben": "કાશીબેન",
    "shantaben": "શાંતાબેન",
    "leelaben": "લીલાબેન",
    "lilaben": "લીલાબેન",
    "pushpaben": "પુષ્પાબેન",
    "bhavnaben": "ભાવનાબેન",
    "bhavna": "ભાવના",
    "shilpaben": "શિલ્પાબેન",
    "shilpa": "શિલ્પા",
    "rekhaben": "રેખાબેન",
    "rekha": "રેખા",
    "naynaben": "નાયનાબેન",
    "nayana": "નયના",
    "nayanaben": "નયનાબેન",
    "kiranben": "કિરણબેન",
    "dakshaben": "દક્ષાબેન",
    "daksha": "દક્ષા",
    "hansaben": "હંસાબેન",
    "hansa": "હંસા",
    "kamlaben": "કમલાબેન",
    "kamla": "કમલા",
    "kokilaben": "કોકિલાબેન",
    "kokila": "કોકિલા",
    "manjulaben": "મંજુલાબેન",
    "manjula": "મંજુલા",

    # Generic Location & Prepositions
    "post": "પોસ્ટ",
    "near": "પાસે",
    "opp": "સામે",
    "opposite": "સામે",
    "behind": "પાછળ",
    "bhai": "ભાઈ",
    "ben": "બેન",
    "kumar": "કુમાર",
    "shri": "શ્રી",
    "shree": "શ્રી",
    "gram": "ગામ",
    "village": "ગામ",
    "taluka": "તાલુકો",
    "taluko": "તાલુકો",
    "district": "જીલ્લો",
    "jillo": "જીલ્લો",
    "jilla": "જીલ્લો",
    "city": "શહેર",
}

# Override dictionary for Google Translate mistranslations of place names and proper nouns
DICT_OVERRIDES = {
    "શું વાજડી": "વાજડી વડ",
    "વાજડી શું": "વાજડી વડ",
    "વડ વજડી": "વાજડી વડ",
    "વાળ વાજડી": "વાજડી વડ",
    "વાજડી વાળ": "વાજડી વડ",
    "વજડી વડ": "વાજડી વડ",
    "વજડી વિરદા": "વાજડી વીરડા",
    "ન્યૂ જાગનાથ": "ન્યુ જગનાથ",
    "ખેરડીયા": "ખેરાડીયા",
    "સર્વે નો": "સર્વે નંબર",
    "જાગનાથ": "જગનાથ",
    "હાડમાટલા": "હડમતાળા",
    "હડમતલા": "હડમતાળા",
    "અરડોઇ": "અરડોઈ",
    "મેંગની": "મેંગણી",
    "બેદી": "બેડી",
    "પાઈકી": "પૈકી",
    "ટીપ્પન": "ટીપ્પણ",
    "માપાણી": "માપણી",
    "એન્ડ": "અને",
}

INDEPENDENT_VOWELS = {
    "aai": "આઈ",
    "aau": "આઉ",
    "aae": "આએ",
    "aa": "આ",
    "ai": "ઐ",
    "au": "ઔ",
    "ii": "ઈ",
    "ee": "ઈ",
    "ea": "ઈ",
    "uu": "ઊ",
    "oo": "ઊ",
    "a": "અ",
    "i": "ઇ",
    "u": "ઉ",
    "e": "એ",
    "o": "ઓ",
}

VOWEL_SIGNS = {
    "aai": "ાઈ",
    "aau": "ાઉ",
    "aae": "ાએ",
    "aa": "ા",
    "ai": "ૈ",
    "au": "ૌ",
    "ii": "ી",
    "ee": "ી",
    "ea": "ી",
    "uu": "ૂ",
    "oo": "ૂ",
    "a": "",
    "i": "િ",
    "u": "ુ",
    "e": "ે",
    "o": "ો",
}

CONSONANTS = {
    "ksh": "ક્ષ",
    "chh": "છ",
    "sth": "સ્થ",
    "str": "સ્ત્ર",
    "sph": "સ્ફ",
    "sch": "શ્ચ",
    "rsh": "ર્ષ",
    "rth": "ર્થ",
    "rdh": "ર્ધ",
    "rkh": "ર્ખ",
    "rgh": "ર્ઘ",
    "rbh": "ર્ભ",
    "kh": "ખ",
    "gh": "ઘ",
    "ch": "ચ",
    "jh": "ઝ",
    "th": "થ",
    "dh": "ધ",
    "ph": "ફ",
    "bh": "ભ",
    "sh": "શ",
    "gn": "જ્ઞ",
    "tr": "ત્ર",
    "gy": "જ્ઞ",
    "ny": "ઞ",
    "ng": "ઙ",
    "kr": "ક્ર",
    "gr": "ગ્ર",
    "pr": "પ્ર",
    "br": "બ્ર",
    "dr": "દ્ર",
    "fr": "ફ્ર",
    "st": "સ્ત",
    "sp": "સ્પ",
    "sk": "સ્ક",
    "sl": "સ્લ",
    "sm": "સ્મ",
    "sn": "સ્ન",
    "sw": "સ્વ",
    "sv": "સ્વ",
    "nd": "ન્દ",
    "nt": "ન્ત",
    "nj": "ન્જ",
    "nk": "ન્ક",
    "mp": "મ્પ",
    "mb": "મ્બ",
    "rd": "ર્ડ",
    "rt": "ર્ટ",
    "rj": "ર્જ",
    "rk": "ર્ક",
    "rm": "ર્મ",
    "rn": "ર્ન",
    "rp": "ર્પ",
    "rs": "ર્સ",
    "ks": "ક્ષ",
    "ty": "ત્ય",
    "dy": "દ્ય",
    "ny": "ન્ય",
    "py": "પ્ય",
    "by": "બ્ય",
    "my": "મ્ય",
    "vy": "વ્ય",
    "k": "ક",
    "g": "ગ",
    "j": "જ",
    "t": "ત",
    "d": "દ",
    "n": "ન",
    "p": "પ",
    "b": "બ",
    "m": "મ",
    "y": "ય",
    "r": "ર",
    "l": "લ",
    "v": "વ",
    "w": "વ",
    "s": "સ",
    "h": "હ",
    "f": "ફ",
    "z": "ઝ",
    "q": "ક",
    "x": "ક્સ",
    "c": "ક",
}

VOWEL_KEYS = sorted(INDEPENDENT_VOWELS.keys(), key=len, reverse=True)
CONSONANT_KEYS = sorted(CONSONANTS.keys(), key=len, reverse=True)
_SORTED_TRANSLATION_KEYS = sorted(COMMON_TRANSLATIONS.keys(), key=len, reverse=True)

def _contains_gujarati(text: str) -> bool:
    return any("\u0A80" <= ch <= "\u0AFF" for ch in text)

def _to_gujarati_digits(text: str) -> str:
    return text.translate(DIGIT_MAP)

def _match_from(text: str, index: int, options: list[str]) -> str:
    for key in options:
        if text.startswith(key, index):
            return key
    return ""

def _transliterate_latin_word(word: str) -> str:
    lw = word.lower()
    if lw in COMMON_TRANSLATIONS:
        return COMMON_TRANSLATIONS[lw]

    suffix_rules = [
        ("sinhji", "સિંહજી"),
        ("singhji", "સિંહજી"),
        ("sinh", "સિંહ"),
        ("singh", "સિંહ"),
        ("bhai", "ભાઈ"),
        ("ben", "બેન"),
        ("kumar", "કુમાર"),
        ("prasad", "પ્રસાદ"),
        ("nagar", "નગર"),
        ("pur", "પુર"),
        ("pura", "પુરા"),
        ("wadi", "વાડી"),
        ("vadi", "વાડી"),
        ("gadh", "ગઢ"),
        ("raj", "રાજ"),
        ("nath", "નાથ"),
        ("pal", "પાલ"),
        ("ram", "રામ"),
        ("dhar", "ધાર"),
        ("diya", "ડીયા"),
        ("iya", "િયા"),
        ("ani", "ાણી"),
    ]

    for sfx_en, sfx_gu in suffix_rules:
        if lw.endswith(sfx_en) and len(lw) > len(sfx_en):
            base_part = lw[:-len(sfx_en)]
            if base_part in COMMON_TRANSLATIONS:
                return COMMON_TRANSLATIONS[base_part] + sfx_gu
            return _transliterate_latin_word(base_part) + sfx_gu

    out = []
    i = 0
    while i < len(lw):
        if not lw[i].isalpha():
            out.append(lw[i])
            i += 1
            continue

        cons = _match_from(lw, i, CONSONANT_KEYS)
        if cons:
            out.append(CONSONANTS[cons])
            i += len(cons)
            vow = _match_from(lw, i, VOWEL_KEYS)
            if vow:
                out.append(VOWEL_SIGNS[vow])
                i += len(vow)
            continue

        vow = _match_from(lw, i, VOWEL_KEYS)
        if vow:
            out.append(INDEPENDENT_VOWELS[vow])
            i += len(vow)
            continue

        out.append(lw[i])
        i += 1

    return "".join(out)

def transliterate_english_to_gujarati(text: str) -> str:
    if not text:
        return ""

    working_text = text

    for key in _SORTED_TRANSLATION_KEYS:
        pattern = re.compile(r"\b" + re.escape(key) + r"\b", re.IGNORECASE)
        if pattern.search(working_text):
            working_text = pattern.sub(COMMON_TRANSLATIONS[key], working_text)

    parts = []
    token = []

    def flush_token() -> None:
        if token:
            word_str = "".join(token)
            parts.append(_transliterate_latin_word(word_str))
            token.clear()

    for ch in working_text:
        if ch.isalpha():
            token.append(ch)
        else:
            flush_token()
            parts.append(ch)
    flush_token()

    return _to_gujarati_digits("".join(parts))

def transliterate_indic_input(text: str) -> str:
    """
    Phonetic Indic transliteration engine (No API Key Required).
    1. Pre-substitutes known Rajkot & Gujarat place names, talukas, and legal terms.
    2. Uses Indic phonetic transliteration for English words without language hallucination.
    3. Preserves all punctuation, slashes, numbers, and formatting.
    4. Post-corrects machine artifacts using DICT_OVERRIDES.
    5. Converts numbers to Gujarati numerals (0-9 -> ૦-૯).
    """
    if not text or not text.strip():
        return text

    working = text.strip()

    # 1. Pre-substitute known phrases and place names from dictionary
    for key in _SORTED_TRANSLATION_KEYS:
        pattern = re.compile(r"" + re.escape(key) + r"", re.IGNORECASE)
        if pattern.search(working):
            working = pattern.sub(COMMON_TRANSLATIONS[key], working)

    # If no English/Latin letters remain, return directly with Gujarati digits
    if not any(c.isalpha() and ord(c) < 128 for c in working):
        return _to_gujarati_digits(working)

    # 2. Extract remaining English words to transliterate with Indic Input Tools
    words = list(dict.fromkeys(re.findall(r"[a-zA-Z]+", working)))
    if words:
        try:
            nl = chr(10)
            query = nl.join(words)
            url = "https://inputtools.google.com/request?text=" + urllib.parse.quote(query) + "&itc=gu-t-i0-und&num=1&cp=0&cs=1&ie=utf-8&oe=utf-8"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            res = json.loads(urllib.request.urlopen(req, timeout=5).read().decode("utf-8"))
            if res[0] == "SUCCESS" and res[1]:
                trans_words = res[1][0][1][0].split(nl)
                mapping = dict(zip(words, trans_words))
                working = re.sub(r"[a-zA-Z]+", lambda m: mapping.get(m.group(0), m.group(0)), working)
        except Exception as e:
            print(f"Indic transliteration API fallback: {e}")
            working = transliterate_english_to_gujarati(working)

    for k, v in DICT_OVERRIDES.items():
        working = working.replace(k, v)

    return _to_gujarati_digits(working)

# Alias for backward compatibility
translate_with_google = transliterate_indic_input

def normalize_value_for_form(value: str) -> str:
    if not value:
        return value
    text = value.strip()
    if _contains_gujarati(text):
        return _to_gujarati_digits(text)
    return translate_with_google(text)

def normalize_form_updates(data: dict) -> dict:
    normalized = {}
    for key, value in data.items():
        if value is None:
            normalized[key] = value
        else:
            normalized[key] = normalize_value_for_form(str(value))
    return normalized

def build_bilingual_question(gujarati_text: str, english_text: str) -> str:
    return f"{gujarati_text}\n(English) {english_text}"

def get_next_question(form_data: dict) -> str | None:
    for field_name, gujarati_question, english_question in FIELD_QUESTIONS:
        val = form_data.get(field_name, "")
        if val is None or str(val).strip() == "":
            return build_bilingual_question(gujarati_question, english_question)
    return None

def process_chat_message(session_id: str, user_message: str) -> str:
    form_data = get_form_data(session_id)
    msg = user_message.strip()

    current_field = None
    for field_name, _, _ in FIELD_QUESTIONS:
        val = form_data.get(field_name, "")
        if val is None or str(val).strip() == "":
            current_field = field_name
            break

    confirm_prefix = ""

    if current_field:
        if msg.lower() in ["skip", "સ્કીપ", "નથી", "no", "-", "નથી રાખવું"]:
            update_form_data(session_id, {current_field: "-"})
            confirm_prefix = "⏭️ સ્કીપ કરેલ છે (Skipped)."
        else:
            if current_field == "date" and msg.lower() in ["today", "આજે", "આજની"]:
                today_str = datetime.date.today().strftime("%d-%m-%Y")
                normalized_val = _to_gujarati_digits(today_str)
                update_form_data(session_id, {current_field: normalized_val})
                confirm_prefix = f"✓ આજની તારીખ (Today): {normalized_val}"
            else:
                normalized_val = normalize_value_for_form(msg)
                update_form_data(session_id, {current_field: normalized_val})
                if _contains_gujarati(msg):
                    confirm_prefix = f"✓ નોંધાયેલ: {normalized_val}"
                else:
                    confirm_prefix = f"✓ Google Translation: \"{msg}\" ➔ \"{normalized_val}\""

    updated_form_data = get_form_data(session_id)
    next_question = get_next_question(updated_form_data)

    if next_question:
        if confirm_prefix:
            reply = f"{confirm_prefix}\n\n{next_question}"
        else:
            reply = next_question
    else:
        completion_msg = (
            "અભિનંદન! ફોર્મની બધી જ વિગતો ભરાઈ ગઈ છે. તમે ઉપર આપેલા બટનથી પીડીએફ ડાઉનલોડ કરી શકો છો.\n"
            "(English) Great! All form details are completed. You can now download the PDF using the button above."
        )
        if confirm_prefix:
            reply = f"{confirm_prefix}\n\n{completion_msg}"
        else:
            reply = completion_msg

    add_chat_message(session_id, "user", user_message)
    add_chat_message(session_id, "bot", reply)

    return reply
