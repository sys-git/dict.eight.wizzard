
from dict.bin.FileCodec import decode
import os
import sys
import traceback

__dirname,__filename = os.path.split(sys.argv[0])
if __name__ == "__main__":
    __options__DEFAULT_OPTIONS_FILENAME = os.path.realpath(os.path.join(__dirname,'../options/options.bin'))
else:
    print __dirname
    __options__DEFAULT_OPTIONS_FILENAME = os.path.realpath(os.path.join(__dirname,'options/options.bin'))

""" Local variables: """
__options__IMPORT_FAILED = True


def __options__loadOptions(key, data):
    #    Decrypt the data:
    open("options.txt", "wb").write(decode(key, data))
    data = open("options.txt", "rb").read()
    os.remove("options.txt")
    currentVars = globals()
    dataLines = data.strip().splitlines()
    newLines = []
    """ Strip out the blank lines and lines beginning <#>. """
    for aLine in dataLines:
        if len(aLine.strip())>0:
            if aLine.strip()[0] == '#':
                continue
            newLines.append(aLine.strip())
    """ Now remove the <[> and <]> chars at the start and end of the lines. """
    currentParam = None
    myDir = {}
    for aLine in newLines:
        pre,match,post = aLine.strip().partition('[')
        if len(match)==0 and len(post)==0:
            # Found value.
            if currentParam:
                # Assign it to our global dictionary.
                currentVars[currentParam] = pre.strip()
                myDir[currentParam] = pre.strip()
            else:
                # Throw away the param as JUNK !
                pass
        else:
            # Found a parameter.
            pre,match,post = post.partition(']')
            if len(pre)>0:
                currentParam = pre
    return

""" Now load and parse the options from the user's options file and present these as global options. """
try:
    #print 'trying to open file: ', __options__DEFAULT_OPTIONS_FILENAME
    __options__fp = open(__options__DEFAULT_OPTIONS_FILENAME,'r')
    data = __options__fp.read()
    if data:
        __options__IMPORT_FAILED = False
        __options__loadOptions("hello.world", data)
    else:
        __options__IMPORT_FAILED = True
except Exception, _e:
    print 'error applying options:'
    print traceback.print_exc()
    sys.exit('error applying options')

if __name__ == "__main__":
    print 'Options> Defaults applied !'
    if __options__IMPORT_FAILED == False:
        print 'Options> User preferences applied !'
    else:
        print 'Options> ERROR - User preferences NOT applied !'
    
