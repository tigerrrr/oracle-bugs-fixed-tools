#!/usr/bin/env python3
# coding=UTF-8

import sys
import getopt
import re
from collections import defaultdict

def PrintUsage():
##################
    print ( "Usage: \n" + sys.argv[0] + " -h | [-e] {-l | [-r <RU>] } file1 [ file2 ... ]" + """
    
Where:
      -h, --help            - print this usage
      -e, --extended        - print extended information in format: <RU> | <PATH>
      -l, --list            - print all RU/RUR found in files and number of patches if -e option
      -r <RU>, --ru <RU>    - print only patches for specified <RU> found in files
    
    file# should be created by elinks using "File"->"Save formatted document" command  

Example for getting Oracle 19c's List of Fixed Bugs    
    elinks https://support.oracle.com/epmos/faces/DocContentDisplay?id=2523220.1
    
    """)

def FormatPatch(p,d):
    # if patch# contains non-number then insert a space between patch number and 
    # example 29807964E => 29807964 E
    if not re.match('[0-9]',p[-1]):
        np=p[:-1]+' '+p[-1]
    else:
        np=p     
    return np+'\t'+d


def replace_pseudograph(text):
    replacement_dict = {
        '┌': '+',  '─': '-', '┬': '-',  '┐': '+',
        '├': '|',            '┼': '+',  '┤': '|',
        '│': '|',
        '└': '+',            '┴': '-',  '┘': '+'
    }

    for pseudograph_char, ascii_char in replacement_dict.items():
        text = text.replace(pseudograph_char, ascii_char)

    return text


# global variables
bList=False
bExtended=False
pRU=''
gdRuPatches=defaultdict(list) # global dictionary of {"RU":[patches]}

# so far the longest possible RU version will contain 28 characters, but we give +1 just in case :
# 12.2.0.1.DBOCT2019RUR:200414
# 18.9.1.0.DBJAN2020RUR:200414
# 18.10.1.0.DBRUR:200714        
# 19.5.2.0.DBJAN2020RUR:200414
# 19.10.1.0.0.DBRUR:210420
# 123456789012345678901234567890 formatting ruller 
iRuLen = 29

# parse command line 
try:
    opts, args = getopt.getopt(sys.argv[1:], 'hler:', ['help', 'list','extended','release-update='])

    for opt, arg in opts:
        if opt in ('-h','--help'):
            PrintUsage()
            sys.exit()
        elif opt in ('-l','--list'):
            bList = True
        elif opt in ('-e','--extended'):
            bExtended = True    
        elif opt in ('-r','--release-update'):
            pRU=arg

except getopt.GetoptError as err:
    print(err)
    PrintUsage()
    sys.exit(2)

if len(args)==0:
    print("Please specify at least one file")
    PrintUsage()
    sys.exit(2)

example = '''
            +-------------------------------------------------------------------------------------------------------------------------------------------+
            | 19.11.0.0.DBRU:210420 | 31341746  | gdfb ORA-600 [kdlx_read-2] while modifying table partition lob parameters                             |
            |-----------------------+-----------+-------------------------------------------------------------------------------------------------------|
            |                       |           | ORA-600 [kdlimemCtor]/[kokl_kaf:invalid locator                                                       |
            | 19.10.0.0.DBRU:210119 | 29477015* | version]/[kdlxdup_rcictor_sz]/[kdld3_der:size]/[kdlferror597: unknown status] or ORA-22922 on IOT     |
            |                       |           | With LOB Column. This bug is alerted in Note 2584581.1                                                |
            |-----------------------+-----------+-------------------------------------------------------------------------------------------------------|
            |                       |           | ORA-600 [kdlimemCtor]/[kokl_kaf:invalid locator                                                       |
            | 19.9.0.0.DBRU:201020  | 29477015* | version]/[kdlxdup_rcictor_sz]/[kdld3_der:size]/[kdlferror597: unknown status] or ORA-22922 on IOT     |
            |                       |           | With LOB Column. This bug is alerted in Note 2584581.1                                                |
            |-----------------------+-----------+-------------------------------------------------------------------------------------------------------|
            |                       | 24596874  | Redact TSDP: multiple ORA-600[kghfrh:ds] on running star workload                                     |
            | 19.8.0.0.DBRU:200714  |-----------+-------------------------------------------------------------------------------------------------------|
            |                       | 30623138  | High row cache mutex wait on looking up dc_users                                                      |
            |-----------------------+-----------+-------------------------------------------------------------------------------------------------------|
            | 19.7.0.0.DBRU:200414  | 29794174  | Securefile: ORA-600: internal error code, arguments: [1:kdlwgather_cont]                              |
            +-------------------------------------------------------------------------------------------------------------------------------------------+
'''

for file in args:
    with open(file,'r') as fp:
        sRU = ''
        sPatchID = ''
        sDesc = ''
        aPatches=[]
        for line in fp:
            ###print ('['+line.rstrip()+']') 
            line = replace_pseudograph (line)
            # table pattern
            if re.match('^[ ]+[+\|]',line):
                # if RU separator
                if re.match('^[ ]+[+\|][-]',line):
                    # this is final separator, then sRU and aPatches are ready
                    if sRU:
                        # add last patch from list, because RU separator hijack Patch separator 
                        if sPatchID:
                            sPatch = FormatPatch(sPatchID,sDesc.strip())
                            if sPatch not in aPatches:
                                aPatches.append(str(sPatch)) # add last element  
                            sPatchID = ''
                            sDesc = ''

                        # if RU in this block matches the one we are interested in  
                        if not pRU or (pRU and re.match(pRU,sRU)):
                            gdRuPatches[sRU].extend(aPatches) # add patches to global list

                        sRU = ''
                        aPatches=[]
                # not a separator
                else:
                    aLine = line.split('|',3)
                    #print (aLine[1].strip() + '#' + aLine[2].strip() + '#' + aLine[3].strip())
                    # [0] ignorable prefix
                    # [1] RU or empty
                    # [2] patch or separator or empty
                    # [3] patch description or empty if patch contain separator 
                    ###print ('>'+aLine[1].strip()+'<')
                    if not sRU and aLine[1].strip():
                        sRU = aLine[1].strip()
                        if bList and not sRU in gdRuPatches:
                            # print ('[['+sRU+']]')
                            gdRuPatches[sRU] = [] 

                    # patch id is not separator
                    if not re.match('[-]',aLine[2].strip()):     
                        # TO DO  - what if Decsription contain "|"? 

                        #aDesc = aLine[3].rsplit('|\n') # get rid of last |\n

                        # print('>>'+aLine[2].strip())

                        if aLine[2].strip():
                            sPatchID = aLine[2].strip()

                        # patch id is not a separator, then description is continuation of previous line   
                        sDesc = sDesc + aLine[3].rstrip('|\n').strip() + " "   
                    # patch id is a separator 
                    # (may not come here if RU separator, so we repeat the code at RU separator)
                    else:
                        sPatch = FormatPatch(sPatchID,sDesc.strip())
                        if sPatch not in aPatches:
                            aPatches.append(str(sPatch))   
                        sPatchID=''
                        sDesc=''
            # any other lines ()
            #else:
                #nil
# printing final results
if bList:
    for key in sorted(gdRuPatches):
        if bExtended:
            print(f'{key:{iRuLen}}'+'|{:4}'.format(len(gdRuPatches[key])))
        else:
            print(key)
    #print (*sorted(gdRuPatches),sep='\n')
else:
    for key in gdRuPatches:
        for patch in gdRuPatches[key]:
            if bExtended :
                print( f'{key:{iRuLen}}',end='|')
            print (patch)

        #print ('# ' + key)
        #print ('========================')
        #print (*gdRuPatches[key], sep='\n')
        #print ('========================')
        #print ('# total patches:  {}'.format(len(gdRuPatches[key])))    
