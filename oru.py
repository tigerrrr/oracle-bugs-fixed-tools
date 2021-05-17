#!/usr/bin/env python3
# coding=UTF-8

import sys
import getopt
import re

def PrintUsage():
##################
    print ( "Usage: \n" + sys.argv[0] + " -h | -l | -p <RU> file1 [ file2 ... ]" + """
    
Where:
      -h, --help            - print this usage
      -l, --list            - print all RU/RUR found in files
      -r <RU>, --ru <RU>    - print all patches for specified <RU> found in files
    
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

# global variables
gaPatches=[] # global list of patches for "-p" option
gaRU=[] # global list of RU for "-l" option 
bList=False
pRU=''

# parse 
try:
    opts, args = getopt.getopt(sys.argv[1:], 'hlr:', ['help', 'list','release-update='])

    for opt, arg in opts:
        if opt in ('-h','--help'):
            PrintUsage()
            sys.exit()
        elif opt in ('-l','--list'):
            bList = True
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

for file in args:
    with open(file,'r') as fp:
        sRU = ''
        sPatch = ''
        sDesc = ''
        aPatches=[]
        for line in fp:
            #print (line.rstrip()) 
            # table pattern
            if re.match('^            [+\|]',line):
                # if RU separator
                if re.match('^            [+\|][-]',line):
                    # this is final separator, then sRU and aPatches are ready
                    if sRU:
                        # add last patch from list, because RU separator hijack Patch separator 
                        if sPatch:
                            aPatches.append(FormatPatch(sPatch,sDesc.strip())) # add last element  
                            sPatch = ''
                            sDesc = ''

                        # if RU in this block patches one we we intertested in  
                        if re.match(pRU,sRU):
                            #print (sRU)
                            #print ('========================')
                            #print (*aPatches, sep='\n')
                            gaPatches.extend(aPatches) # add to global list

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
                    ##print ('>'+aLine[1].strip()+'<')
                    if not sRU and aLine[1].strip():
                        sRU = aLine[1].strip()
                        if bList and not sRU in gaRU:
                            gaRU.append(sRU) 
                        #print ('Found RU:'+sRU) 

                    # patch id is not separator
                    if not re.match('[-]',aLine[2].strip()):     
                        # TO DO  - what if Decsription contain "|"? 

                        #aDesc = aLine[3].rsplit('|\n') # get rid of last |\n

                        # print('>>'+aLine[2].strip())

                        if aLine[2].strip():
                            sPatch = aLine[2].strip()

                        # patch id is not a separator, then description is continuation of previous line   
                        sDesc = sDesc + aLine[3].rstrip('|\n').strip() + " "   
                    # patch id is a separator 
                    # (may not come here if RU separator, so we repeat the code at RU separator)
                    else:
                        aPatches.append(FormatPatch(sPatch,sDesc.strip()))
                        sPatch=''
                        sDesc=''
            # any other lines ()
            #else:
                #nil
# printing final results
if bList:
    gaRU.sort()
    print(*gaRU, sep='\n')

if pRU:
    print ('# ' + pRU)
    print ('========================')
    print (*gaPatches, sep='\n')
    print ('========================')
    print ('# total patches:  {}'.format(len(gaPatches)))

