import sys
import re
inpaths = sys.argv[1:]
for inpath in inpaths:
    instr = open(inpath, 'r').read()
    outstr = re.sub(r'(\d) (\d)', r'\1,\2', instr)
    if outstr != instr:
        outf = open(inpath, 'w')
        outf.write(outstr)
        outf.close()
