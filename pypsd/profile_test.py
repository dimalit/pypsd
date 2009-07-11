import cProfile
from psdfile import PSDFile

def main():
    parseTest()
    #cProfile.run('parseTest()')
    
def parseTest():
    psd = PSDFile("./../samples/bcard back.psd")
    psd.parse()
    psd.save("./../samples/")
    
if __name__ == "__main__":
    main()