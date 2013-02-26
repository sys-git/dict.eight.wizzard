"""
Decipher the email to find the 'key', the rest should be obvious...
"""

from Crypto.Cipher import AES
from optparse import OptionParser
import base64
import os
import sys
import tempfile
#import this

PADDING = '@'
BLOCK_SIZE = 32
KEY_SIZE = 32
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
encodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
decodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
newKey = lambda k: AES.new(k.zfill(KEY_SIZE)[:KEY_SIZE])
encode = lambda key, data: encodeAES(newKey(key), data)
decode = lambda key, data: decodeAES(newKey(key), data)

def work(args):
    parser = OptionParser()
    parser.add_option("-e", "--encode", dest="encode",
                  help="encode a file path", metavar="ENCODE", default=None)
    parser.add_option("-d", "--decode", dest="decode",
                  help="decode a file path", metavar="DECODE", default=None)
    parser.add_option("-o", "--output", dest="output",
                  help="output path for encode/decode (mandatory)", metavar="OUTPUT", default="result.file")
    parser.add_option("-k", "--key", dest="key",
                  help="secret key (mandatory)", metavar="KEY", default="")
    parser.add_option("-v", "--verify", dest="verify", action="store_true",
                  help="verify round-trip using random data", metavar="VERIFY")
    (options, _args) = parser.parse_args(args)
    if options.encode != None:
        open(os.path.realpath(options.output), "wb").write(encode(options.key, open(os.path.realpath(options.encode), "rb").read()))
        print "\nEncoded '%(E)s' to '%(O)s'." % {"E":options.encode, "O":os.path.realpath(options.output)}
        return options
    elif options.decode != None:
        open(os.path.realpath(options.output), "wb").write(decode(options.key, open(os.path.realpath(options.decode), "rb").read()))
        print "\nDecoded '%(D)s' to '%(O)s'." % {"D":options.decode, "O":os.path.realpath(options.output)}
        return options
    elif options.verify != None:
        (fd, name) = tempfile.mkstemp()
        os.close(fd)
        eResult = "hello.world!"
        open(name, "wb").write(encode(options.key, eResult))
        result = decode(options.key, open(name, "rb").read())
        assert result == eResult, "encode/decode round-trip failed!"
        print "\nSimple round-trip verified!"
        return options
    else:
        parser.print_help()

if __name__ == '__main__':
    work(sys.argv[1:])

