import unittest
import os.path
import re
from StringIO import StringIO

class PSParserEndOfFileException(Exception):
    pass

class PSParserBadSyntax(Exception):
    def __init__(self, line):
        self.line = line
    def __str__(self):
        return repr(self.line)

class PSParser(object):
    def __init__(self, stream=None, source=None):
        if not stream and not source:
            raise BaseException("Stream or source should be defined")
        if not stream:
            stream = StringIO(source)
        self.stream = stream
        
        stream.seek(0,2)
        self.size = stream.tell()
        stream.seek(0)
        self.curr_line = 0
    
    def getNextLine(self):
        if self.stream.tell() < self.size:
            line = ""
            while line == "":
                line = self.stream.readline().strip()
                self.curr_line += 1
            return line
        else:
            raise PSParserEndOfFileException()
    
    def getArrayValue(self, line):
        array = []
        while not line.startswith("]"):
            if line == "":
                line = self.getNextLine()
                continue
            value, line = self.getValue(line)
            array.append(value)
        return array, line[1:].strip()
    
    def getDictKey(self, line):
        if not line.startswith("/") and line != "/":
            raise PSParserBadSyntax()
        empty, key, rest_line = re.compile(r'^/(\S+)\s?').split(line)
        return key, rest_line.strip()
            
    def getDictValue(self, line):
        dic = {}
        while not line.startswith(">>"):
            if line == "":
                line = self.getNextLine()
                continue
            key, line = self.getDictKey(line)
            value, line = self.getValue(line)
            dic[key] = value
        return dic, line[2:].strip() 
    
    def getTextValue(self, line):
        text=""
        excape = False
        while not line.startswith(")") or excape:
            if line == "":
                line = "\n"+self.getNextLine()
            excape = False
            if line[0] == "\\":
                if not excape:
                    excape = True
                else:
                    excape = False
            if line.startswith("\xfe\xff"):
                line = line[2:]
            text += line[0]
            line = line[1:]
        return text, line[1:].strip()
    
    def getValue(self, line):
        line = line.strip()
        if line == "":
            line = self.getNextLine()
        
        num_re = re.compile("^((?:-)?(?:\d+)?(?:\.\d+)?)")
        bool_re = re.compile("^((?:true)|(?:false))")
        
        num_groups = num_re.match(line).groups()
        if num_groups[0] != "":
            empty, value, rest_line = num_re.split(line)
            if "." in value:
                value = float(value)
            else:
                value = int(value)
            return value, rest_line.strip()
        
        if bool_re.match(line):
            empty, value, rest_line = bool_re.split(line)
            return value == 'true', rest_line.strip()
        
        if line.startswith("["):
            return self.getArrayValue(line[1:].strip())
        
        if line.startswith("<<"):
            return self.getDictValue(line[2:].strip())
        
        if line.startswith("("):
            return self.getTextValue(line[1:].strip())
    
    def parse(self):
        obj = None
        try:
            obj = self.getValue("")[0]
        except PSParserEndOfFileException:
            pass
        except Exception:
            print "Exception in line %d" % self.curr_line
        
        return obj

class _PSParserTest(unittest.TestCase):
    def setUp(self):
        self.file_stream = open('../samples/ps_example.txt', r'rb')
        self.array_test = """[-10.12 -10 20.12 [.19 -.20] 30 20]"""
        self.empty_array_test = """[-10.12 -10 20.12 [] 30 20]"""
        self.boolan_test = """[true false true]"""
        self.dict_with_empty_array = """<</Lines
                    <<
                        /WritingDirection 0
                        /Children [ ]
                    >>>>"""
        self.dict_test = """<</Key1 10 /Key2 20 /Key3 [10 20 30] /Key4 <</Key5 40>> /Key6 <</Key7 50>>>>"""
        self.text_test = """<</Key1 10 /Key2 20 /Key3 30  /Text (00Line 1
Line 2
Line 3
)>>>
"""
    
    def test_full_parse(self):
        #ps = PSParser(stream=self.file_stream)
        #obj = ps.parse()s
        pass
    
    def test_boolean_parse(self):
        ps = PSParser(source=self.boolan_test)
        obj = ps.parse()
        assert obj == [True, False, True]

    def test_array_parse(self):
        ps = PSParser(source=self.array_test)
        obj = ps.parse()
        assert obj == [-10.12, -10, 20.12, [0.19, -0.20], 30, 20]
        ps = PSParser(source=self.empty_array_test)
        obj = ps.parse()
        assert obj == [-10.12, -10, 20.12, [], 30, 20]
        
    def test_dict_parse(self):
        ps = PSParser(source=self.dict_test)
        obj = ps.parse()
        assert obj == {"Key1":10, "Key2":20, "Key3":[10, 20, 30], "Key4":{"Key5": 40}, "Key6": {"Key7":50}}
        ps = PSParser(source=self.dict_with_empty_array)
        obj = ps.parse()
        assert obj == {"Lines":{"WritingDirection":0, "Children":[]}}    
    
    def test_text_parse(self):
        ps = PSParser(source=self.text_test)
        obj = ps.parse()
        assert obj == {"Key1":10.0, "Key2":20.0, "Key3":30.0, "Text":'00Line 1\nLine 2\nLine 3\n'}
        

if __name__ == "__main__":
    unittest.main()