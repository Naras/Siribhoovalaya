#!/opt/local/bin/python2.7
# -*- coding: utf-8 -*-
__author__ = 'naras_mg'
import re

for file in ['playground_straight.csv','playground_5x5.csv' ]:
# for file in ['playground_5x5.csv' ]:
    print '\n--------------------\nprocessing: ', file
    ckrFile = open(file)
    ckr = ckrFile.readlines()
    state = 0  # will denote where in the encoding instructions file we are reading lines
    bandha = []
    chakra = []
    for lin in ckr:
        if lin == ",,,,,,\n": continue # blank like line, just skip processing
        line = lin[:-1].split(',')
        # print line
        if re.search('^Text to Coded',line[0]) :
            state = 1
        elif re.search('^Is it possible to Code Entire Text',line[0]):
            state = 4
        elif re.search('^Text Matrix',line[0]):
            state = 4
        elif re.search('^Describe Your Coding Matrix ',line[0]):
            state = 2
        elif re.search('^Valaya',line[0]):
            state = 3
        else: pass # state from prev. read line continues
        # print state
        if state == 1: plainText = line[1] # plain text is here
        elif state == 2:  # coding matrix is here
           for i in range(5): bandha.append(line[2 + i])
        elif state == 3: # valaya (chakra here)
            for i in range(5): chakra.append(line[2 + i])

    bandha = [int(c) for c in bandha if c!='']
    chakra = [int(c) for c in chakra if c!='']

    print 'plain text: ', plainText
    print 'bandha: ', bandha
    print 'chakra: ', chakra

    cipherText = [chr(ord('a') + i - 1) for i in chakra]
    print 'cipher: ', ' '.join(cipherText)
    decrypted = (chr(ord('a') + chakra[i - 1] - 1) for i in bandha)
    print 'decrypted:',' '.join(decrypted)

    try:
        cipherText = [chr(i) for i in chakra]
        print 'cipher: ', ' '.join(cipherText)
        # sortedBandha = sorted(bandha)
        # for item in sortedBandha: print item, bandha.index(item)
        decrypted = (chr(chakra[bandha.index(item)]) for item in sorted(bandha))
        print 'decrypted:', ' '.join(decrypted)
    except:
        pass
