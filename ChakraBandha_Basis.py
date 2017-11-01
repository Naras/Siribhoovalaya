#!/opt/local/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'naras_mg'
def detectLang(ch):
    start_end = {0:[0x0900,0x097F],1:[0x980, 0x9ff],2:[0xa00, 0xa7f], 3:[0xa80, 0xaff], \
             4:[0x0900,0x097F],5:[0xb00, 0xb7f],6:[0xb80, 0xbff],7:[0xc00, 0xc7f],8:[0xc80, 0xcff]}
    for k,v in start_end.items():
        ch_hex = uni_to_hex(ch)
        if ch_hex >= v[0] and ch_hex <= v[1]:
            return k
    return None
def uni_to_hex(u):
    return int(r"0x"+repr(u).translate(None,r"\xuu'"),0)
def transliterate(ch,targetScript):
    if ord(ch) < 128: return ch  # ascii
    # elif ch in [u'\u0964',u'\u0965']: return ch # extra devanagari chars .. danda/double danda
    else:
        lang = detectLang(ch)
        if lang == None: return ch
        else: return IndianUnicodeValue[targetScript][uni_to_hex(ch) - uni_to_hex(IndianUnicodeValue[lang][1])+1]
def transliterate_lines(source,scriptTarget='devanagari'):
    for i,e in enumerate(IndianLanguages):
        if scriptTarget == e: trg = i;
    target = ''
    for s in unicode(source,'utf-8'):
        # if ord(c) > 127: print 'transliterating:',c,uni_to_hex(c)
        target += transliterate(s,trg)
    return target
IndianLanguages = ('devanagari','bengali','gurmukhi','gujarati','oriya','tamizh','telugu','kannada','malayalam')
IndianUnicodeValue = [['devanagari'],['bengali'],['gurmukhi'],['gujarati'],['oriya'],['tamizh'],['telugu'],['kannada'],['malayalam']]
for j in range(9):
    for i in xrange(0x0900,0x097F): #(0x0905,0x093A):
     IndianUnicodeValue[j].append(unichr(i+128*j))

A = ['']
[A.append('') for x in range(65)]
A[1] = "अ"
A[2] = "आ"
A[3] = "आा"
A[4] = "इ"
A[5] = "ई"
A[6] = "ईी"
A[7] = "उ"
A[8] = "ऊ"
A[9] = "ऊू"
A[10] = "ॠ"
A[11] = "ॠृ"
A[12] = "ॠृा"
A[13] = "ळ"
A[14] = "ळु"
A[15] = "ळू"
A[16] = "ए"
A[17] = "एा"
A[18] = "एाा"
A[19] = "ऎ"
A[20] = "ऐॊ"
A[21] = "ऐॊॊ"
A[22] = "ओ"
A[23] = "ओो"
A[24] = "ओोो"
A[25] = "औ"
A[26] = "औौ"
A[27] = "औौौ"
A[28] = "क्"
A[29] = "ख्"
A[30] = "ग्"
A[31] = "घ्"
A[32] = "ङ्"
A[33] = "च्"
A[34] = "छ्"
A[35] = "ज्"
A[36] = "झ्"
A[37] = "ञ्"
A[38] = "ट्"
A[39] = "ठ्"
A[40] = "ड्"
A[41] = "ढ्"
A[42] = "ण्"
A[43] = "त्"
A[44] = "थ्"
A[45] = "द्"
A[46] = "ध्"
A[47] = "न्"
A[48] = "प्"
A[49] = "फ्"
A[50] = "ब्"
A[51] = "भ्"
A[52] = "म्"
A[53] = "य्"
A[54] = "र्"
A[55] = "ल्"
A[56] = "व्"
A[57] = "श्"
A[58] = "ष्"
A[59] = "स्"
A[60] = "ह्"
A[61] = "ं"
A[62] = "ः"
A[63] = "…"
A[64] = "::"

for i in range(1,64): A[i-1]=A[i]
del A[64]
print ' '.join(A)
xx=''
for x in A: xx += ' ' + transliterate_lines(x,'kannada')
print xx