"""
Simplified Sandhi conversion functions for integration
Extracted from Sandhi_Convt.py to avoid dependency issues
"""

def Sandhi(inword: str) -> str:
    """
    Convert from separate consonants/vowels to combined normal form
    Handles halanth (्) + vowel combinations and applies proper vowel matra rules
    """
    if not inword:
        return ""
    halanth = chr(0x094d)  # Devanagari halanth sign
    vowels_indep = {'अ':'', 'आ':'ा', 'इ':'ि', 'ई':'ी', 'उ':'ु', 'ऊ':'ू', 'ऋ':'ृ', 'ॠ':'ॄ', 'ए':'े', 'ऐ':'ै', 'ओ':'ो', '�':'ौ', '\u0960': '\u0962', '\u0961': '\u0963'}
    outword = []
    i = 0
    while i < len(inword):
        ch = inword[i]
        if ch == halanth and i < len(inword) - 1:
            next_ch = inword[i + 1]
            if next_ch in vowels_indep:
                matra = vowels_indep[next_ch]
                if matra: outword.append(matra)
                i += 2
                continue
        elif 0x0915 <= ord(ch) <= 0x0939: # Consonants
            if i < len(inword) - 1:
                next_ch = inword[i + 1]
                if next_ch in vowels_indep:
                    matra = vowels_indep[next_ch]
                    outword.append(ch)
                    if matra: outword.append(matra)
                    i += 2
                    continue
        outword.append(ch)
        i += 1
    return "".join(outword)

def visandhi(inword: str) -> str:
    """
    Convert from combined normal form to separate consonants/vowels
    Adds halanth (्) between consonants and converts matras back to independent vowels
    """
    if not inword:
        return ""
    halanth = chr(0x094d)  # Devanagari halanth sign
    matra_to_indep = {'ा':'आ', 'ि':'इ', 'ी':'ई', 'ु':'उ', 'ू':'ऊ', 'ृ':'ऋ', 'ॄ':'ॠ', 'े':'ए', 'ै':'ऐ', 'ो':'ओ', 'ौ':'औ', '\u0962':'\u0960', '\u0963':'\u0961'}
    outword = []
    i = 0
    while i < len(inword):
        ch = inword[i]
        if 0x0915 <= ord(ch) <= 0x0939: # Consonants
            outword.append(ch)
            if i < len(inword) - 1:
                next_ch = inword[i + 1]
                if next_ch not in matra_to_indep and next_ch != halanth:
                    outword.append(halanth)
                    outword.append('अ')
            else:
                outword.append(halanth)
                outword.append('अ')
        elif ch in matra_to_indep:
            outword.append(halanth)
            outword.append(matra_to_indep[ch])
        else:
            outword.append(ch)
        i += 1
    return "".join(outword)

# Test functions
if __name__ == '__main__':
    # Test cases
    test_cases = [
        "ಸ್ಓಮ್",  # Separate consonant+vowel form
        "ಸೋಮ",   # Combined form
        "ಕ್ಷ್",  # Double halanth
    ]
    
    print("=== Sandhi/Visandhi Test ===")
    for test in test_cases:
        sandhi_result = Sandhi(test)
        visandhi_result = visandhi(test)
        print(f"Original: '{test}'")
        print(f"  Sandhi: '{sandhi_result}'")
        print(f"  Visandhi: '{visandhi_result}'")
        print()
