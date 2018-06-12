#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Script for conversion of Stardict tabfile (<header>\t<definition>
# per line) into the OPF file for MobiPocket Dictionary
#
# For usage of dictionary convert it by:
# (wine) mobigen.exe DICTIONARY.opf
# or now...
# kindlegen DICTIONARY.opf
#
# MobiPocket Reader at: www.mobipocket.com for platforms:
#   PalmOs, Windows Mobile, Symbian (Series 60, Series 80, 90, UIQ), Psion, Blackberry, Franklin, iLiad (by iRex), BenQ-Siemens, Pepper Pad..
#   http://www.mobipocket.com/en/DownloadSoft/DownloadManualInstall.asp
# mobigen.exe available at:
#   http://www.mobipocket.com/soft/prcgen/mobigen.zip
#
# Copyright (C) 2007 - Klokan Petr Přidal (www.klokan.cz)
# Copyright (C) 2015 - Alexander Peyser (github.com/apeyser)
# Copyright (C) 2018 - Steven Pan (github.com/stevenpan91)
#
# Version history:
# 0.1 (19.7.2007) Initial version
# 0.2 (2/2015) Rework removing encoding, runs on python3
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

# VERSION
#VERSION = "0.2"

import sys
import os
import argparse
from itertools import islice, count, groupby
from contextlib import contextmanager
import importlib
import io

# Stop with the encoding -- it's broken anyhow
# in the kindles and undefined.
def normalizeLetter(ch):
    try: ch = mapping[ch]
    except KeyError: pass
    return ch

def normalizeUnicode(text):
    """
    Reduce some characters to something else
    """
    return ''.join(normalizeLetter(c) for c in text)

# Args:
#  --verbose
#  --module: module to load and attempt to extract getdef, getkey & mapping
#  --source: source language code (en by default)
#  --target: target language code (en by default)
#  file: the tab delimited file to read

def parseargs():
    if len(sys.argv) < 1:
        print("tab2opf (Stardict->MobiPocket)")
        print("------------------------------")
        print("Version: %s" % VERSION)
        print("Copyright (C) 2007 - Klokan Petr Pridal")
        print()
        print("Usage: python tab2opf.py [-utf] DICTIONARY.tab")
        print()
        print("ERROR: You have to specify a .tab file")
        sys.exit(1)

    parser = argparse.ArgumentParser("tab2opf")
    parser.add_argument("-v", "--verbose", help="make verbose", 
                        action="store_true")
    parser.add_argument("-m", "--module", 
                        help="Import module for mapping, getkey, getdef")
    parser.add_argument("-s", "--source", default="en", help="Source language")
    parser.add_argument("-t", "--target", default="en", help="Target language")
    parser.add_argument("file", help="tab file to input")    
    return parser.parse_args()

def loadmember(mod, attr, dfault):
    if hasattr(mod, attr):
        print("Loading {} from {}".format(attr, mod.__name__))
        globals()[attr] = getattr(mod, attr)
    else: globals()[attr] = dfault

def importmod():
    global MODULE
    if MODULE is None: mod = None
    else:
        mod = importlib.import_module(MODULE)
        print("Loading methods from: {}".format(mod.__file__))

    loadmember(mod, 'getkey', lambda key: key)
    loadmember(mod, 'getdef', lambda dfn: dfn)
    loadmember(mod, 'mapping', {})

args = parseargs()
VERBOSE  = args.verbose
FILENAME = args.file
MODULE   = args.module
INLANG   = args.source
OUTLANG  = args.target
importmod()

# add a single [term, definition]
# to defs[key]
# r is a tab split line
def readkey(r, defs):
    try: term, defn =  r.split('\t',1)
    except ValueError:
        print("Bad line: '{}'".format(r))
        raise

    term = term.strip()
    defn = getdef(defn)
    defn = defn.replace("\\\\","\\").\
        replace(">", "\\>").\
        replace("<", "\\<").\
        replace("\\n","<br/>\n").\
        strip()

    nkey = normalizeUnicode(term)
    key = getkey(nkey)
    key = key.\
        replace('"', "'").\
        replace('<', '\\<').\
        replace('>', '\\>').\
        lower().strip()

    nkey = nkey.\
        replace('"', "'").\
        replace('<', '\\<').\
        replace('>', '\\>').\
        lower().strip()

    if key == '':
        raise Exception("Missing key {}".format(term))
    if defn == '':
        raise Exception("Missing definition {}".format(term))

    if VERBOSE: print(key, ":", term)

    ndef = [term, defn, key == nkey]
    if key in defs: defs[key].append(ndef)
    else:           defs[key] = [ndef]

# Skip empty lines and lines that only have a comment
def inclline(s):
    s = s.lstrip()
    return len(s) != 0 and s[0] != '#'

# Iterate over FILENAME, reading lines of
# term {tab} definition
# skips empty lines and commented out lines
#
def readkeys():
    if VERBOSE: print("Reading {}".format(FILENAME))
    #with open(FILENAME,'r', encoding='utf-8') as fr:
    with io.open(FILENAME,'r', encoding='utf-8') as fr:
        defns = {}
        for r in filter(inclline, fr):
            readkey(r, defns)
        return defns

# Write to key file {name}{n}.html
# put the body inside the context manager
# The onclick here gives a kindlegen warning
# but appears to be necessary to actually
# have a lookup dictionary
@contextmanager
def writekeyfile(name, i):
    fname = "{}{}.html".format(name, i)
    if VERBOSE: print("Key file: {}".format(fname))
    #with open(fname, 'w') as to:
    with io.open(fname, 'w',encoding="utf-8") as to:
        to.write("""<?xml version="1.0" encoding="utf-8"?>
<html xmlns:idx="www.mobipocket.com" xmlns:mbp="www.mobipocket.com" xmlns:xlink="http://www.w3.org/1999/xlink">
  <body>
    <mbp:pagebreak/>
    <mbp:frameset>
      <mbp:slave-frame display="bottom" device="all" breadth="auto" leftmargin="0" rightmargin="0" bottommargin="0" topmargin="0">
        <div align="center" bgcolor="yellow"/>
        <a onclick="index_search()">Dictionary Search</a>
        </div>
      </mbp:slave-frame>
      <mbp:pagebreak/>
""")
        try: yield to
        finally:
            to.write("""
    </mbp:frameset>
  </body>
</html>
        """)

# Order definitions by keys, then by whether the key
# matches the original term, then by length of term
# then alphabetically
def keyf(defn):
    term = defn[0]
    if defn[2]: l = 0
    else: l = len(term)
    return l, term

#find Mongolian vowel that counts for vowel harmony
def isMNVowelHarmonyVowel(letter):
    ignorelettercase=letter.lower()
    retval=False
    #vowels=['а','е','ё','и','й','о','ө','у','ү','э'] #all
    vowels=['а','о','ө','э'] #just count these
    for c in vowels:
        if(letter==c):
            retval=True

    return retval

#find Mongolian vowel
def isMNVowel(letter):
    ignorelettercase=letter.lower()
    retval=False
    vowels=['а','е','ё','и','й','о','ө','у','ү','э','я','ё'] #all
    #vowels=['а','о','ө','э'] #just count these
    for c in vowels:
        if(letter==c):
            retval=True

    return retval

#capitalize
def capitalize(word):
    if(len(word)>0):
        #print(word[0])
        firstterm=word[0]
        ucaseletters=['А','Б','В','Г','Д','Е','Ё','Ж','З',\
                    'И','Й','К','Л','М','Н','О','Ө','П',\
                    'Р','С','Т','У','Ү','Ф','Х','Ц','Ч',\
                    'Ш','Щ','Ъ','Ы','Ь','Э','Ю','Я']
        lcaseletters=['а','б','в','г','д','е','ё','ж','з',\
                    'и','й','к','л','м','н','о','ө','п',\
                    'р','с','т','у','ү','ф','х','ц','ч',\
                    'ш','щ','ъ','ы','ь','э','ю','я']

        try:
            letterindex=lcaseletters.index(firstterm)
            #print(ucaseletters[letterindex]+word[1:])
            return ucaseletters[letterindex]+word[1:]
        except ValueError:
            return word
    
    return word

def makeinflection(word,capitalizeYN=True, negativeYN=False,reflexiveYN=False,instrumentalYN=False,whichIsMarkerYN=False):
    #vowelharmony=getvowelharmonyletter(word)
    vowelharmony=getvowelharmonyletter(word)[0]
    retval="<idx:infl><idx:iform value=\""+word+"\"/></idx:infl>"
    if(capitalizeYN):
        retval=retval+"<idx:infl><idx:iform value=\""+capitalize(word)+"\"/></idx:infl>"
    if(negativeYN):
        retval=retval+"<idx:infl><idx:iform value=\""+word+"гүй\"/></idx:infl>"
        if(capitalizeYN):
            retval=retval+"<idx:infl><idx:iform value=\""+capitalize(word)+"гүй\"/></idx:infl>"
    if(reflexiveYN):
        retval=retval+"<idx:infl><idx:iform value=\""+word+vowelharmony+vowelharmony+"\"/></idx:infl>"
        if(capitalizeYN):
            retval=retval+"<idx:infl><idx:iform value=\""+capitalize(word)+vowelharmony+vowelharmony+"\"/></idx:infl>"
    if(instrumentalYN):
        retval=retval+"<idx:infl><idx:iform value=\""+word+vowelharmony+vowelharmony+"р\"/></idx:infl>"
        if(capitalizeYN):
            retval=retval+"<idx:infl><idx:iform value=\""+capitalize(word)+vowelharmony+vowelharmony+"р\"/></idx:infl>"
        if(reflexiveYN):
            retval=retval+"<idx:infl><idx:iform value=\""+word+vowelharmony+vowelharmony+"р"+vowelharmony+vowelharmony+"\"/></idx:infl>"
            if(capitalizeYN):
                retval=retval+"<idx:infl><idx:iform value=\""+capitalize(word)+vowelharmony+vowelharmony+"р"+vowelharmony+vowelharmony+"\"/></idx:infl>"
    if(whichIsMarkerYN):
        retval=retval+makeinflection(word+"х",reflexiveYN=True)
        #retval=retval+"<idx:infl><idx:iform value=\""+word+"х\"/></idx:infl>"
        #if(capitalizeYN):
            #retval=retval+"<idx:infl><idx:iform value=\""+capitalize(word)+"х\"/></idx:infl>"        
    return retval

def getvowelharmonyletter(word):
    retval=['э','э','ү'] #0: individual VH, 1: primary VH, 2: secondary VH
    #retval='э'#feminine vowels and words with only neutral vowels will have э for vowel harmony
    notfound=True
    index=len(word)-1
    #print(word)
    if(len(word)>1):
        while(notfound):
            if(isMNVowel(word[index])):
                if(word[index]=='а' or word[index]=='у' or word[index]=='о' or word[index]=='я' or word[index]=='ё'): #if a masculine vowel is found, switch to 'a'
                    #retval='а'
                    retval=['а','а','у']

            if(isMNVowelHarmonyVowel(word[index])):
                notfound=False
                #retval=word[index]
                retval[0]=word[index]
            index-=1
            if(index<0):
                notfound=False
            #print(index)
    
    return retval



class MongolianWord:
    term=""
    chain=""
    vowelharmonies=[]
    vowelharmony=""
    PVH=""
    SVH=""
    def __init__(self,word):
        self.term=word
        #chain="<idx:orth value=\""+key+"\">"
        self.chain=""
        self.vowelharmonies=getvowelharmonyletter(word)
        self.vowelharmony=self.vowelharmonies[0]
        self.PVH=self.vowelharmonies[1]
        self.SVH=self.vowelharmonies[2]

    def buildIt(self,combo,modifier="None",capitalizeYN=True, negativeYN=False,reflexiveYN=False,instrumentalYN=False,whichIsMarkerYN=False): #absorbed as in the vowel before "х" is absorbed
        modifiedTerm=self.getModifiedTerm(modifier)
        self.chain=self.chain+makeinflection(modifiedTerm+combo,capitalizeYN=capitalizeYN, negativeYN=negativeYN,reflexiveYN=reflexiveYN,instrumentalYN=instrumentalYN,whichIsMarkerYN=whichIsMarkerYN)

    def buildItVerb(self,combo,modifier="RemoveLast",capitalizeYN=True, negativeYN=False,reflexiveYN=False,instrumentalYN=False,whichIsMarkerYN=False): #absorbed as in the vowel before "х" is absorbed
        modifiedTerm=self.getModifiedTerm(modifier)
        self.chain=self.chain+makeinflection(modifiedTerm+combo,capitalizeYN=capitalizeYN, negativeYN=negativeYN,reflexiveYN=reflexiveYN,instrumentalYN=instrumentalYN,whichIsMarkerYN=whichIsMarkerYN)

    def conjugateIt(self,combo="",modifier="None",completionMod=False):
        modifiedTerm=self.getModifiedTerm(modifier)
        self.chain=self.chain+self.conjugateverb(modifiedTerm+combo,completionMod)

    def makeGenAcc(self,combo="ий",modifier="None",dropGenEnd=False): #make genitive accusative
        #modifiedTerm=self.getModifiedTerm(modifier)

        #gen
        if(dropGenEnd):
            self.buildIt(combo,modifier,whichIsMarkerYN=True)
        else:
            self.buildIt(combo+"н",modifier,whichIsMarkerYN=True)
    
        #acc
        self.buildIt(combo+"г",modifier)

    def makeDat(self,combo="д",modifier="None"):
        self.buildIt(combo,modifier,reflexiveYN=True,instrumentalYN=True)
        self.buildIt(combo+"л"+self.vowelharmony+self.vowelharmony,modifier)

    def makeVerbSuffixes(self,combo="",modifier="RemoveLast"):
        #past
        if(self.vowelharmony=="ө"):
            self.buildIt(combo+"сэн",modifier,negativeYN=True,reflexiveYN=True)
        else: 
            self.buildIt(combo+"с"+self.vowelharmony+"н",modifier,negativeYN=True,reflexiveYN=True)

        #future
        self.buildIt(combo+"н"+self.vowelharmony,modifier)

        self.buildIt(combo+"ж",modifier)

        #narrative past
        self.buildIt(combo+"жээ",modifier)
        self.buildIt("чээ",modifier)

        self.buildIt("ч",modifier)

        #perpetual
        self.buildItVerb(combo+"д"+self.vowelharmony+"г",modifier,negativeYN=True)

        #conditional converb (if __, when __)
        mTermLastLet=self.getModifiedTerm(modifier)[-1]
        if(mTermLastLet=="л" or mTermLastLet=="в"):
            self.buildItVerb(combo+"б"+self.vowelharmony+"л",modifier)
        else:
            self.buildItVerb(combo+"в"+self.vowelharmony+"л",modifier)

        #no idea what this is
        self.buildItVerb(combo+"т"+self.vowelharmony+"л",modifier)

        #intent
        self.buildItVerb(combo+"м"+self.vowelharmony+self.vowelharmony+"р",modifier) 

        #recent past
        self.buildItVerb(combo+"л"+self.vowelharmony+self.vowelharmony,modifier)

        #as soon as
        self.buildItVerb(combo+"м"+self.vowelharmony+"гц",modifier)

        #action of the main clause has been happening since the action of the sub clause
        self.buildItVerb(combo+"с"+self.vowelharmony+self.vowelharmony+"р",modifier,negativeYN=True)

    def getModifiedTerm(self,modifier="None"):
        modifiedTerm=self.term #default to none
        
        if(modifier=="Absorbed"):
            modifiedTerm=self.term[:-2]
        elif(modifier=="RemoveLast"):
            modifiedTerm=self.term[:-1]
        elif(modifier=="Switch"): #switch
            modifiedTerm=self.term[:-3]+self.term[-2]+self.term[-3]
        elif(modifier=="RemoveLastVowel"):
            modifiedTerm=self.term[:-2]+self.term[-1]

        return modifiedTerm


    def conjugateverb(self,originalWord=term,completionMod=False):
        term=originalWord
        #vowelharmony=getvowelharmonyletter(term)
        vowelharmony=getvowelharmonyletter(term)[0]

        #imperative
        impCount=0
        stop=False
        for c in reversed(term[:-1]): #go through term without x at end of verb
            if(stop==False and (c=="а" or c=="у" or c=="о" or c=="ү" or c=="ө")):
                impCount+=1
                if (len(term)>impCount+2 and term[-(impCount+2)]=="г"): #+2 because skip x and skip letter just added
                    impCount+=1
            else:
                stop=True

        #build imperative
        self.buildItVerb("")

        if(len(term)>impCount+1):
            #buildsourceword=buildsourceword+makeinflection(term[:(-1*(1+impCount))])
            self.chain=self.chain+makeinflection(term[:(-1*(1+impCount))])

        #unsure what this is
        self.buildItVerb("г"+vowelharmony+vowelharmony+"д")

        #when/while ____
        self.buildItVerb("х"+vowelharmony+"д")
        self.makeDat("хд",modifier="RemoveLast")

        #modified verbs for progressive tense
        self.buildItVerb("ж")
        
        #modified verbs for recent past
        self.buildItVerb("в")

        #modified verbs for modal converb
        self.buildItVerb("н")
        
        #still dative case?
        self.makeDat("нд",modifier="RemoveLast")
        
        #modified verbs for action verbs
        self.buildItVerb("л",negativeYN=True)
        self.makeDat("лт",modifier="RemoveLast")

        self.buildItVerb(vowelharmony+"гүй")

        
        if(len(term)>2):
            
            if(term[-3:]=="чих" and completionMod):
                if(completionMod):

                    self.makeVerbSuffixes(modifier="None")

                    #
                    #buildsourceword=buildsourceword+makeinflection(term+vowelharmony+vowelharmony+"д",negativeYN=True,reflexiveYN=True)
                    self.buildItVerb(vowelharmony+vowelharmony+"д",modifier="None",negativeYN=True,reflexiveYN=True)


            else:
                if((isMNVowelHarmonyVowel(term[-2]) and not isMNVowel(term[-3]) and term[-3]!="г")  or term[-3:]=="чих"): #filter out double vowels
                    

                    if(term[-3]=="ш" or term[-3]=="ж" or term[-3]=="н" or term[-3]=="з" or (term[-3]=="л" and term[-2]=="а")):
                        self.makeVerbSuffixes()
                    elif(len(term)>=5 and ( (term[-3]=="л" or term[-3]=="р") and not isMNVowel(term[-4]) ) ):
                        self.makeVerbSuffixes(modifier="Switch")
                    else:
                        self.makeVerbSuffixes(modifier="Absorbed")

                    if(isMNVowelHarmonyVowel(term[-2]) and not isMNVowel(term[-2])):
                        #action happens before main action
                        self.buildItVerb(vowelharmony+"д")
                    else: #term[-3:]=="чих"
                        self.buildItVerb(vowelharmony+vowelharmony+"д",modifier="Absorbed")
                else:

                
                    if(term[-2]=="и"):


                        if(term[-3]=="н" or term[-3]=="ш" or term[-3]=="ж"):
                            self.makeVerbSuffixes()
                        else:
                            self.makeVerbSuffixes("ь")


                        #action happens before main action
                        #buildsourceword=buildsourceword+makeinflection(term[:-1]+vowelharmony+"д")
                        self.buildItVerb(vowelharmony+"д")

                        if(term[-3]=="г" or term[-3]=="в" or term[-3]=="р"):
                            #take care of exceptions to ч rule
                            #buildsourceword=buildsourceword+makeinflection(term[:-2]+"ч")
                            self.buildItVerb("ч",modifier="Absorbed")
                    else:


                        self.makeVerbSuffixes()


                        #action happens before main action
                        #buildsourceword=buildsourceword+makeinflection(term[:-1]+vowelharmony+"д")
                        self.buildItVerb(vowelharmony+"д")
                    

        
        if(len(term)>2):
            if(vowelharmony=="ө"):
                self.buildItVerb(vowelharmony+vowelharmony+"рэй",modifier="Absorbed")
            else:
                self.buildItVerb(vowelharmony+vowelharmony+"р"+vowelharmony+"й",modifier="Absorbed")
            
            #imperative
            #buildsourceword=buildsourceword+makeinflection(term[:-2]+\
                        #vowelharmony+vowelharmony+"р"+vowelharmony+"й")

        buildsourceword=self.chain

        #complete action
        #buildsourceword=buildsourceword+makeinflection(term[:-1]+"чих",negativeYN=True)

        #unsure of this
        buildsourceword=buildsourceword+makeinflection(term[:-1]+vowelharmony+"ч")

        
        

        #Let's ___
        if(isMNVowel(term[-2])):
            if(term[-2]=="а" or term[-2]=="у" or term[-2]=="я"):
                buildsourceword=buildsourceword+makeinflection(term[:-2]+"ъя")
                buildsourceword=buildsourceword+makeinflection(term[:-1]+"ъя")
            elif(term[-2]=="э" or term[-2]=="и" or term[-2]=="ө" or term[-2]=="ү"):
                buildsourceword=buildsourceword+makeinflection(term[:-2]+"ье")
                buildsourceword=buildsourceword+makeinflection(term[:-1]+"ье")
            else:
                buildsourceword=buildsourceword+makeinflection(term[:-2]+"ъё")
                buildsourceword=buildsourceword+makeinflection(term[:-1]+"ъё")

        return buildsourceword

# Write into to the key, definition pairs
# key -> [[term, defn, key==term]]
def writekey(to, key, defn):
    terms = iter(sorted(defn, key=keyf))
    for term, g in groupby(terms, key=lambda d: d[0]):
        mg = MongolianWord(term)
        lastletter=term[-1]
        mg.chain="<idx:orth value=\""+key+"\">"
        #vowelharmony=""
        #vowelharmony=getvowelharmonyletter(term)
        vowelharmonyletters=getvowelharmonyletter(term)
        vowelharmony=vowelharmonyletters[0]
        PVH=vowelharmonyletters[1] #as in а or э
        SVH=vowelharmonyletters[2] #as in у or ү
        #print(vowelharmony+PVH+SVH)

        #negation and capitalize
        mg.buildIt("",capitalizeYN=True,negativeYN=True,reflexiveYN=True,instrumentalYN=True)

        #if consonant
        if(not isMNVowel(lastletter) and len(term)>1):

			#possibly converb? Causes conflicts, commented out
            #buildsourceword=buildsourceword+makeinflection(term+vowelharmony+"н")
            if(len(term)>3):
                mg.buildIt(vowelharmony+"н")

            #ablative case (from <term>)
            
            if(lastletter=="х" or lastletter=="т" or lastletter=="в" or lastletter=="с"):
                mg.buildIt("н"+vowelharmony+vowelharmony+"с",reflexiveYN=True)
            else:
                mg.buildIt(vowelharmony+vowelharmony+"с",reflexiveYN=True)

            #instrumental case
            #mg.buildIt(vowelharmony+vowelharmony+"р",negativeYN=True)

            #genitive case + accusitive case
            if(lastletter=="ж" or lastletter=="ч" or lastletter=="г" or lastletter=="ш" or lastletter=="ь" or lastletter=="к"):   
                
                #gen
                if(lastletter=="г"):
                    mg.buildIt("гийн",modifier="Absorbed",whichIsMarkerYN=True)
                else:
                    mg.makeGenAcc()
                
            elif(lastletter=="н"):
                mg.makeGenAcc(dropGenEnd=True)
                mg.makeGenAcc("ы",dropGenEnd=True)
                #gen
                mg.buildIt("гийн",whichIsMarkerYN=True)

            else:
                
                if(lastletter=="р" and term[-2]=="а" and not isMNVowel(term[:-3])):
                    mg.makeGenAcc(modifier="RemoveLastVowel")
                    mg.makeGenAcc("ы",modifier="RemoveLastVowel")
                else:
                    mg.makeGenAcc()
                    mg.makeGenAcc("ы")

            

            #dative case
            if(lastletter=="г" or lastletter=="в" or lastletter=="с" or lastletter=="р" or lastletter=="к"):
                mg.makeDat("т")
            elif(lastletter=="д" or lastletter=="т" or lastletter=="з" or lastletter=="ц"):
                mg.makeDat(vowelharmony+"д")
            elif(lastletter=="ж" or lastletter=="ч" or lastletter=="ш"):
                mg.makeDat("ид")
            else:
                mg.makeDat()

			#exceptions for dative case
            if(lastletter=="л" or lastletter=="н"):
                mg.makeDat("т")


            #verbs
            if(lastletter=="х"):
                mg.conjugateIt()

                #complete action
                if(len(term)>3 and term[-3:]!="чих"):
                    mg.buildItVerb("чих",modifier="Absorbed",negativeYN=True)
                    mg.buildItVerb("чих"+vowelharmony+vowelharmony+"д",modifier="None",negativeYN=True,reflexiveYN=True)
                    mg.makeVerbSuffixes("чих",modifier="Absorbed")
                    #buildsourceword=buildsourceword+conjugateverb(term[:-2]+"чих",buildsourceword,completionMod=True)

                #passive voice
                if(len(term)>2 and term[-5:]!="уулах" and term[-5:]!="үүлэх"):
                    #уулах or үүлэх                    
                    mg.buildIt(SVH+SVH+"л"+PVH+"х",modifier="Absorbed",negativeYN=True)
                    mg.conjugateIt(SVH+SVH+"л"+PVH+"х",modifier="Absorbed")


                #no good description on what this is except that it's inherited from Classical Mongolian
                if(term[-4:]!="лдах" and term[-4:]!="лдэх"):
                    #лдах or лдэх
                    mg.buildIt("лд"+PVH+"х",modifier="RemoveLast",negativeYN=True)
                    mg.makeVerbSuffixes("лд"+PVH+"х")
                    #mg.conjugateIt("лд"+PVH+"х",modifier="RemoveLast")
                    #mg.buildIt("лд"+PVH+"н",modifier="RemoveLast")
                    #buildsourceword=buildsourceword+conjugateverb(term[:-1]+"лдах",buildsourceword)
            else:
                #plurals for non verbs ууд or үүд
                if(lastletter=='н'):
                    mg.buildIt("г"+SVH+SVH+"д",modifier="RemoveLast",reflexiveYN=True,instrumentalYN=True)
                else:
                    mg.buildIt("г"+SVH+SVH+"д",reflexiveYN=True,instrumentalYN=True)
               

            
        #ends in vowel
        else:

			#possibly converb?
            mg.buildIt("н")

            mg.buildIt("ч")

			#ablative case (from <term>)
            mg.buildIt("н"+vowelharmony+vowelharmony+"с",reflexiveYN=True)
            mg.buildIt(vowelharmony+"с",reflexiveYN=True)
            
            #instrumental case
            mg.buildIt("г"+vowelharmony+vowelharmony+"р")
            mg.buildIt(vowelharmony+"р")

            #accusative case
            mg.buildIt("г")
            mg.buildIt("г"+vowelharmony+vowelharmony) # with reflexive
            
            #dative case
            mg.makeDat()
            mg.makeDat("т")
            
            #figure out what this is later
            mg.buildIt("д"+vowelharmony+vowelharmony)

            #genitive case
            if(lastletter=="й"):
                mg.buildIt("н",whichIsMarkerYN=True)
            #long vowel
            elif(len(term)>1 and term[-2]==lastletter):            
                mg.buildIt("ны")
                mg.buildIt("ний")

            #single vowel at end
            if(len(term)>1 and not isMNVowel(term[-2])):

                mg.buildIt("ны")
                mg.buildIt("ын",whichIsMarkerYN=True)
                mg.buildIt("ийн",whichIsMarkerYN=True)
            #plurals
            mg.buildIt("н"+SVH+SVH+"д",reflexiveYN=True,instrumentalYN=True)

        #dimunitives (like shortened names)
        mg.buildIt("х"+vowelharmony+"н")
        
        #reflexive + other
        if(lastletter=="р" and not isMNVowel(term[:-3])):
            mg.buildIt(vowelharmony+vowelharmony,modifier="RemoveLastVowel")
        else:
            mg.buildIt(vowelharmony+vowelharmony)

		#add suffix -тай
        if(vowelharmony=="ө"):
            mg.buildIt("тэй")
        else:
            mg.buildIt("т"+vowelharmony+"й")

        #unsure what this is (I think it's dative plus reflexive, taken care of above)
        #buildsourceword=buildsourceword+makeinflection(term+"д"+vowelharmony+vowelharmony)

        #end        
        mg.chain=mg.chain+"</idx:orth>"
        to.write(
"""
      <idx:entry name="word" scriptable="yes">
        <h2>
"""
          +mg.chain+
          term+"<br/>"+
          #<idx:orth value="{key}">{term}</idx:orth>
"""
        </h2>
""".format(term=term, key=key))

        to.write('; '.join(ndefn for _, ndefn, _ in g))
        to.write(
"""
      </idx:entry>
"""
)

    if VERBOSE: print(key)

# Write all the keys, where defns is a map of
# key --> [[term, defn, key==term]...]
# and name is the basename
# The files are split so that there are no more than
# 10,000 keys written to each file (why?? I dunno)
#
# Returns the number of files.
def writekeys(defns, name):
    keyit = iter(sorted(defns))
    for j in count():
        with writekeyfile(name, j) as to:
            keys = list(islice(keyit, 10000))
            if len(keys) == 0: break
            for key in keys:
                writekey(to, key, defns[key])
    return j+1

# After writing keys, the opf that references all the key files
# is constructed.
# openopf wraps the contents of writeopf
#
@contextmanager
def openopf(ndicts, name):
    fname = "%s.opf" % name
    if VERBOSE: print("Opf: {}".format(fname))
    #with open(fname, 'w') as to:
    with io.open(fname, 'w',encoding="utf-8") as to:
        to.write("""<?xml version="1.0"?><!DOCTYPE package SYSTEM "oeb1.ent">

<!-- the command line instruction 'prcgen dictionary.opf' will produce the dictionary.prc file in the same folder-->
<!-- the command line instruction 'mobigen dictionary.opf' will produce the dictionary.mobi file in the same folder-->

<package unique-identifier="uid" xmlns:dc="Dublin Core">

<metadata>
	<dc-metadata>
		<dc:Identifier id="uid">{name}</dc:Identifier>
		<!-- Title of the document -->
		<dc:Title><h2>{name}</h2></dc:Title>
		<dc:Language>EN</dc:Language>
	</dc-metadata>
	<x-metadata>
	        <output encoding="utf-8" flatten-dynamic-dir="yes"/>
		<DictionaryInLanguage>{source}</DictionaryInLanguage>
		<DictionaryOutLanguage>{target}</DictionaryOutLanguage>
	</x-metadata>
</metadata>

<!-- list of all the files needed to produce the .prc file -->
<manifest>
""".format(name=name, source=INLANG, target=OUTLANG))

        yield to

        to.write("""
<tours/>
<guide> <reference type="search" title="Dictionary Search" onclick= "index_search()"/> </guide>
</package>
"""
)

# Write the opf that describes all the key files
def writeopf(ndicts, name):
    with openopf(ndicts, name) as to:
        for i in range(ndicts):
            to.write(
"""     <item id="dictionary{ndict}" href="{name}{ndict}.html" media-type="text/x-oeb1-document"/>
""".format(ndict=i, name=name))

        to.write("""
</manifest>
<!-- list of the html files in the correct order  -->
<spine>
"""
)
        for i in range(ndicts):
            to.write("""
	<itemref idref="dictionary{ndict}"/>
""".format(ndict=i))

        to.write("""
</spine>
""")

######################################################
# main
######################################################

print("Reading keys")
defns = readkeys()
name = os.path.splitext(os.path.basename(FILENAME))[0]
print("Writing keys")
ndicts = writekeys(defns, name)
print("Writing opf")
writeopf(ndicts, name)
