
# -*- coding: utf-8 -*-
"""
Transliteration utility for Indian languages.
Ported from original Python 2.7 code (Transliterate.py and ChakraBandha_Basis.py).
"""

# Mapping of grid numbers (1-64) to Devanagari Aksharas
# Based on ChakraBandha_Basis.py
# 0-indexed for convenience (index 1 corresponds to grid value 1)
AKSHARA_MAP = [''] * 65
AKSHARA_MAP[1] = "अ"
AKSHARA_MAP[2] = "आ"
AKSHARA_MAP[3] = "आा"
AKSHARA_MAP[4] = "इ"
AKSHARA_MAP[5] = "ई"
AKSHARA_MAP[6] = "ईी"
AKSHARA_MAP[7] = "उ"
AKSHARA_MAP[8] = "ऊ"
AKSHARA_MAP[9] = "ऊू"
AKSHARA_MAP[10] = "ॠ"
AKSHARA_MAP[11] = "ॠृ"
AKSHARA_MAP[12] = "ॠृा"
AKSHARA_MAP[13] = "ळ"
AKSHARA_MAP[14] = "ळु"
AKSHARA_MAP[15] = "ळू"
AKSHARA_MAP[16] = "ए"
AKSHARA_MAP[17] = "एा"
AKSHARA_MAP[18] = "एाा"
AKSHARA_MAP[19] = "ऎ"
AKSHARA_MAP[20] = "ऐॊ"
AKSHARA_MAP[21] = "ऐॊॊ"
AKSHARA_MAP[22] = "ओ"
AKSHARA_MAP[23] = "ओो"
AKSHARA_MAP[24] = "ओोो"
AKSHARA_MAP[25] = "औ"
AKSHARA_MAP[26] = "औौ"
AKSHARA_MAP[27] = "औौौ"
AKSHARA_MAP[28] = "क्"
AKSHARA_MAP[29] = "ख्"
AKSHARA_MAP[30] = "ग्"
AKSHARA_MAP[31] = "घ्"
AKSHARA_MAP[32] = "ङ्"
AKSHARA_MAP[33] = "च्"
AKSHARA_MAP[34] = "छ्"
AKSHARA_MAP[35] = "ज्"
AKSHARA_MAP[36] = "झ्"
AKSHARA_MAP[37] = "ञ्"
AKSHARA_MAP[38] = "ट्"
AKSHARA_MAP[39] = "ठ्"
AKSHARA_MAP[40] = "ड्"
AKSHARA_MAP[41] = "ढ्"
AKSHARA_MAP[42] = "ण्"
AKSHARA_MAP[43] = "त्"
AKSHARA_MAP[44] = "थ्"
AKSHARA_MAP[45] = "द्"
AKSHARA_MAP[46] = "ध्"
AKSHARA_MAP[47] = "न्"
AKSHARA_MAP[48] = "प्"
AKSHARA_MAP[49] = "फ्"
AKSHARA_MAP[50] = "ब्"
AKSHARA_MAP[51] = "भ्"
AKSHARA_MAP[52] = "म्"
AKSHARA_MAP[53] = "य्"
AKSHARA_MAP[54] = "र्"
AKSHARA_MAP[55] = "ल्"
AKSHARA_MAP[56] = "व्"
AKSHARA_MAP[57] = "श्"
AKSHARA_MAP[58] = "ष्"
AKSHARA_MAP[59] = "स्"
AKSHARA_MAP[60] = "ह्"
AKSHARA_MAP[61] = "ं"
AKSHARA_MAP[62] = "ः"
AKSHARA_MAP[63] = "…"
AKSHARA_MAP[64] = "::"

INDIAN_LANGUAGES = ['devanagari', 'bengali', 'gurmukhi', 'gujarati', 'oriya', 'tamizh', 'telugu', 'kannada', 'malayalam']
INDIAN_UNICODE_START = {
    'devanagari': 0x0900,
    'bengali': 0x0980,
    'gurmukhi': 0x0A00,
    'gujarati': 0x0A80,
    'oriya': 0x0B00,
    'tamizh': 0x0B80,
    'telugu': 0x0C00,
    'kannada': 0x0C80,
    'malayalam': 0x0D00
}

def detect_lang_index(ch):
    """
    Detects the language index of a character based on its unicode value.
    Returns index in INDIAN_LANGUAGES list or None.
    """
    val = ord(ch)
    # Simple range checks based on standard offsets (128 bytes per block mostly)
    # Devanagari starts at 0x900
    if 0x0900 <= val <= 0x0D7F:
        offset = (val - 0x0900) // 128
        if 0 <= offset < len(INDIAN_LANGUAGES):
             # Verify strict bounds if needed, but blocks are generally 128 wide
             return offset
    return None

def transliterate_char(ch, target_lang='kannada'):
    """
    Transliterates a single character to the target language.
    """
    if ord(ch) < 128:
        return ch
        
    src_lang_idx = detect_lang_index(ch)
    if src_lang_idx is None:
        return ch
        
    target_lang_idx = INDIAN_LANGUAGES.index(target_lang)
    
    # Calculate offset within the script block
    # Devanagari base is 0x0900 + 0 * 128
    src_base = 0x0900 + (src_lang_idx * 128)
    target_base = 0x0900 + (target_lang_idx * 128)
    
    offset = ord(ch) - src_base
    
    # Handle specific language quirks if necessary, but standard mapping usually works
    # for direct offset mapping in Indian languages for core characters.
    
    return chr(target_base + offset)

def transliterate_text(text, target_lang='kannada'):
    """
    Transliterates a string to the target language.
    """
    return ''.join(transliterate_char(c, target_lang) for c in text)

def get_kannada_for_number(num):
    """
    Returns the Kannada Akshara for a given grid number (1-64).
    """
    if 1 <= num <= 64:
        devanagari = AKSHARA_MAP[num]
        return transliterate_text(devanagari, 'kannada')
    return ""
