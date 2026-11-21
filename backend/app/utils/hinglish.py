import re
from typing import Dict

# Common conversational Hindi/Hinglish vocabulary dictionary
# Mapped to popular, natural creator spellings (as seen on YouTube Shorts, Reels, TikTok)
HINDI_TO_HINGLISH_DICT: Dict[str, str] = {
    # Pronouns & People
    "ये": "ye", "यह": "yeh", "वो": "wo", "वह": "woh",
    "हम": "hum", "आप": "aap", "तुम": "tum", "तू": "tu",
    "मेरा": "mera", "मेरी": "meri", "मेरे": "mere",
    "तेरा": "tera", "तेरी": "teri", "तेरे": "tere",
    "उसका": "uska", "उसकी": "uski", "उसके": "uske",
    "इसका": "iska", "इसकी": "iski", "इसके": "iske",
    "हमारा": "hamara", "हमारी": "hamari", "हमारे": "hamare",
    "आपका": "aapka", "आपकी": "aapki", "आपके": "aapke",
    "तुम्हारा": "tumhara", "तुम्हारी": "tumhari", "तुम्हारे": "tumhare",
    "भाई": "bhai", "यार": "yaar", "दोस्त": "dost", "दोस्तो": "dosto", "दोस्तों": "doston",
    "लोग": "log", "लोगों": "logon", "बंदे": "bande", "बंदा": "banda",
    "सब": "sab", "कोई": "koi", "कुछ": "kuch", "खुद": "khud", "किसी": "kisi",

    # Auxiliaries & State
    "है": "hai", "हैं": "hain", "हो": "ho", "हूँ": "hoon", "हूं": "hoon",
    "था": "tha", "थी": "thi", "थे": "the",
    "होगा": "hoga", "होगी": "hogi", "होंगे": "honge",
    "रहा": "raha", "रही": "rahi", "रहे": "rahe",
    "हुआ": "hua", "हुई": "hui", "हुए": "hue",

    # Common Verbs
    "कर": "kar", "करना": "karna", "करते": "karte", "करता": "karta", "करती": "karti",
    "करेंगे": "karenge", "करेगा": "karega", "करेगी": "karegi", "किया": "kiya",
    "गया": "gaya", "गयी": "gayi", "गए": "gaye", "जा": "jaa", "जाना": "jaana",
    "जाता": "jaata", "जाती": "jaati", "जाते": "jaate", "जायेंगे": "jayenge", "जाएंगे": "jayenge",
    "देख": "dekh", "देखा": "dekha", "देखते": "dekhte", "देखना": "dekhna", "दिखा": "dikha",
    "आ": "aa", "आया": "aaya", "आता": "aata", "आती": "aati", "आते": "aate", "आना": "aana",
    "बोल": "bol", "बोला": "bola", "बोलते": "bolte", "बोलना": "bolna",
    "बता": "bata", "बताया": "bataya", "बताते": "batate", "बताना": "batana",
    "सोच": "soch", "सोचा": "socha", "सोचते": "sochte", "सोचना": "sochna",
    "समझ": "samajh", "समझा": "samjha", "समझे": "samjhe", "समझना": "samajhna",
    "ले": "le", "लिया": "liya", "लेते": "lete", "लेना": "lena", "लेंगे": "lenge",
    "दे": "de", "दिया": "diya", "देते": "dete", "देना": "dena", "देंगे": "denge",
    "मिल": "mil", "मिला": "mila", "मिलता": "milta", "मिलते": "milte", "मिलना": "milna",
    "लग": "lag", "लगा": "laga", "लगता": "lagta", "लगते": "lagte", "लगना": "lagna",
    "निकल": "nikal", "निकला": "nikla", "निकलना": "nikalna", "निकाल": "nikal", "निकाला": "nikala", "निकालना": "nikalna",

    # Prepositions, Conjunctions & Particles
    "पर": "par", "पे": "pe", "से": "se", "को": "ko", "का": "ka", "के": "ke", "की": "ki",
    "और": "aur", "या": "ya", "भी": "bhi", "तो": "to", "तक": "tak", "में": "mein", "ने": "ne",
    "नही": "nahi", "नहीं": "nahi", "ना": "na", "मत": "mat",
    "अगर": "agar", "मगर": "magar", "लेकिन": "lekin", "क्योंकि": "kyunki", "इसलिए": "isliye",
    "ताकि": "taaki", "जैसे": "jaise", "वैसे": "waise", "ऐसे": "aise",

    # Questions & Wh-words
    "क्या": "kya", "क्यों": "kyun", "कहा": "kaha", "कहाँ": "kahan",
    "कब": "kab", "कैसे": "kaise", "कौन": "kaun", "कितना": "kitna", "कितने": "kitne", "कितनी": "kitni",
    "यहाँ": "yahan", "यहां": "yahan", "वहाँ": "wahan", "वहां": "wahan",
    "जब": "jab", "तब": "tab", "अब": "ab",

    # Adjectives, Modifiers & Common Words
    "बहुत": "bahut", "ज्यादा": "jyada", "कम": "kam", "थोड़ा": "thoda", "थोड़ी": "thodi",
    "काफी": "kaafi", "बाकी": "baaki", "अलग": "alag", "पूरा": "poora", "पूरी": "poori", "पूरे": "poore",
    "अच्छा": "achha", "अच्छी": "achhi", "अच्छे": "achhe",
    "बुरा": "bura", "बुरी": "buri", "बुरे": "bure",
    "बड़ा": "bada", "बड़ी": "badi", "बड़े": "bade",
    "छोटा": "chhota", "छोटी": "chhoti", "छोटे": "chhote",
    "सही": "sahi", "गलत": "galat", "सच": "sach", "झूठ": "jhooth",
    "ठीक": "theek", "पक्का": "pakka", "जरूर": "zaroor", "शायद": "shayad",
    "आज": "aaj", "कल": "kal", "बात": "baat", "काम": "kaam", "टाइम": "time",
    "पैसा": "paisa", "पैसे": "paise", "रुपए": "rupaye", "रुपया": "rupaya",
    "दिन": "din", "रात": "raat", "साल": "saal", "महीना": "mahina",
    "घर": "ghar", "रास्ता": "raasta", "जगह": "jagah", "दुनिया": "duniya",
    "आंधी": "aandhi", "तूफान": "toofan", "गाड़ी": "gaadi", "कार": "car",
    "टेढ़े": "tedhe", "सीधा": "seedha",

    # YouTube, Gaming & Pop Culture Terms
    "लेट्स": "let's", "गो": "go", "लेट्स गो": "let's go",
    "करैक्टर": "character", "कैरेक्टर": "character",
    "गेम": "game", "गेमप्ले": "gameplay", "प्ले": "play",
    "वीडियो": "video", "चैनल": "channel", "सब्सक्राइब": "subscribe",
    "लाइक": "like", "शेयर": "share", "कमेंट": "comment",
    "फॉलो": "follow", "सीक्रेट": "secret", "ट्रिक": "trick",
    "लेवल": "level", "मिशन": "mission", "पुलिस": "police"
}

# Devanagari character mappings
DEVA_CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'ड़': 'r', 'ढ़': 'rh', 'फ़': 'f'
}

DEVA_VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'an', 'अः': 'ah'
}

DEVA_MATRAS = {
    'ा': 'a',    # in colloquial hinglish, aa at middle/end is usually written as 'a' (e.g. nikalna, alag)
    'ि': 'i',
    'ी': 'i',    # in hinglish, ee is often written as 'i' (e.g. sahi, baaki)
    'ु': 'u',
    'ू': 'oo',
    'ृ': 'ri',
    'े': 'e',
    'ै': 'ai',
    'ो': 'o',
    'ौ': 'au',
    'ॉ': 'o',
    'ं': 'n',
    'ँ': 'n',
    'ः': 'h'
}

VIRAMA = '्'
NUKTA = '़'

def is_hindi(text: str) -> bool:
    """Check if the text contains Devanagari characters."""
    if not text:
        return False
    return bool(re.search(r"[\u0900-\u097F]", text))

def _transliterate_hindi_word(word: str) -> str:
    """Transliterate a single Devanagari word to natural Hinglish."""
    # Strip any attached punctuation
    match = re.match(r"^([^\w\u0900-\u097F]*)([\u0900-\u097F\w]+)([^\w\u0900-\u097F]*)$", word)
    if not match:
        return word

    prefix, core, suffix = match.groups()

    # 1. Check dictionary first
    if core in HINDI_TO_HINGLISH_DICT:
        return f"{prefix}{HINDI_TO_HINGLISH_DICT[core]}{suffix}"

    # 2. Rule-based transliteration
    n = len(core)
    res = []
    i = 0
    while i < n:
        c = core[i]

        # Check consonant + nukta (e.g. क + ़ = क़)
        if i + 1 < n and core[i + 1] == NUKTA:
            combined = c + NUKTA
            if combined in DEVA_CONSONANTS:
                c = combined
                i += 1

        if c in DEVA_CONSONANTS:
            base = DEVA_CONSONANTS[c]
            if i + 1 < n:
                nxt = core[i + 1]
                if nxt == VIRAMA:
                    res.append(base)
                    i += 2
                    continue
                elif nxt in DEVA_MATRAS:
                    # Specific friendly adjustments
                    matra_val = DEVA_MATRAS[nxt]
                    if nxt == 'ा':
                        # At end of word, 'a' (e.g. karana -> karna)
                        matra_val = 'a'
                    res.append(base + matra_val)
                    i += 2
                    continue
                else:
                    # Inherent vowel rule:
                    # Omit 'a' at end of word (schwa deletion: 'कम' -> 'kam', not 'kama')
                    if i + 1 == n:
                        res.append(base)
                    else:
                        res.append(base + 'a')
                    i += 1
                    continue
            else:
                res.append(base)
                i += 1
                continue
        elif c in DEVA_VOWELS:
            res.append(DEVA_VOWELS[c])
            i += 1
        elif c in DEVA_MATRAS:
            res.append(DEVA_MATRAS[c])
            i += 1
        elif c == VIRAMA:
            i += 1
        else:
            res.append(c)
            i += 1

    transliterated = "".join(res)
    return f"{prefix}{transliterated}{suffix}"

def to_hinglish(text: str) -> str:
    """
    Convert Hindi (Devanagari) text into natural, readable Hinglish (Roman script).
    If the text is already English/Latin, it returns the text unmodified!
    """
    if not text or not is_hindi(text):
        return text

    # Replace Devanagari full stop (danda) with standard period
    result = text.replace("।", ".")

    # Handle multi-word dictionary phrases first
    for phrase, replacement in [
        ("लेट्स गो", "let's go"),
        ("करैक्टर है", "character hai"),
        ("बहुत ज्यादा", "bahut jyada"),
        ("ठीक है", "theek hai"),
        ("कोई बात नहीं", "koi baat nahi"),
        ("सब्सक्राइब करो", "subscribe karo"),
        ("लाइक करो", "like karo")
    ]:
        if phrase in result:
            result = result.replace(phrase, replacement)

    # Word-by-word transliteration
    tokens = result.split()
    converted_tokens = []
    for token in tokens:
        if is_hindi(token):
            converted_tokens.append(_transliterate_hindi_word(token))
        else:
            converted_tokens.append(token)

    output = " ".join(converted_tokens)
    # Clean up double spaces or formatting
    output = re.sub(r"\s+", " ", output).strip()

    # Capitalize the first letter if original had a word
    if output and output[0].islower():
        output = output[0].upper() + output[1:]

    return output
