__author__ = 'naras_mg'

IndianUnicodeValue = [['devanagari'],['bengali'],['gurmukhi'],['gujarati'],['oriya'],['tamizh'],['telugu'],['kannada'],['malayalam']]
for j in range(9):
    for i in xrange(0x0900,0x097F): #:(0x0905,0x093A)
     IndianUnicodeValue[j].append(unichr(i+128*j))
for j in range(9):print ' '.join(IndianUnicodeValue[j])

