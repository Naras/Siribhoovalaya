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
    elif ch in [u'\u0964',u'\u0965']: return ch # extra devanagari chars .. danda/double danda
    else:
        return IndianUnicodeValue[targetScript][uni_to_hex(ch) - uni_to_hex(IndianUnicodeValue[detectLang(ch)][1])+1]
def transliterate_lines(source,scriptTarget='devanagari'):
    for i,e in enumerate(IndianLanguages):
        if scriptTarget == e: trg = i;
    target=''
    for s in source:
        t = ''
        for c in unicode(s,'utf-8'):
            # if ord(c) > 127: print 'transliterating:',c,uni_to_hex(c)
            t += transliterate(c,trg)
        target += t
    return target
IndianLanguages = ('devanagari','bengali','gurmukhi','gujarati','oriya','tamizh','telugu','kannada','malayalam')
IndianUnicodeValue = [['devanagari'],['bengali'],['gurmukhi'],['gujarati'],['oriya'],['tamizh'],['telugu'],['kannada'],['malayalam']]
for j in range(9):
    for i in xrange(0x0900,0x097F): #(0x0905,0x093A):
     IndianUnicodeValue[j].append(unichr(i+128*j))

sourceFile = open('source.txt')
source = sourceFile.readlines()
for s in source:    print s[:-1]
print transliterate_lines(source,'kannada')
