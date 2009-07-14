import cProfile
import pstats
from psdfile import PSDFile
import os
import psyco
from time import clock


def main():
    def doTest(filename, methodname):
        print "%s:" % methodname
        inf = os.path.abspath('../samples/%s' % filename)
        cProfile.run('%s()' % methodname, inf)
        p = pstats.Stats(inf)
        p.strip_dirs()
        p.sort_stats('cumulative').print_stats(10)
    
    #parseTest()
    doTest('bcard_back_profile_4.inf', 'parseTest')

def parseTest():
    a = clock()
    #psyco.full()
    psd = PSDFile("../samples/text_test.psd")
    #g = psyco.proxy(psd.parse)
    psd.parse()
    b = clock()
    print b-a
    psd.save("../samples/")
    
if __name__ == "__main__":
    main()