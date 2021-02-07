# PretenderFile
# Interpreter for dom5 newlords files
# Author: Rafael Stauffer rafael.stauffer@gmx.ch
# Version: 0.1

import csv
import json
import os

DOM_DATA_DIRECTORY = ""
DOM_EXE = ""
DOM_SAVE_GAME_SUBDIR = "savedgames"
DOM_NEWLORDS_SUBDIR = "newlords"
TURN_EXT = ".trn"
H_EXT = ".2h"
LAST_TURN_FILE = "lastturns.json"
BACKUP_TURNS = True
CURRENT_TURN = "current"


class PretenderFile():
    def __init__(self):
        self.fileName = ""
        self.rawData = ''
        self.nations = {}
        self.read_nations_lookup('../data/nations.csv')

    def read_nations_lookup(self, fileName):
        # nation csv file has following line structure: nationID,nationName,nationTitle,era
        self.nations = {}
        with open(fileName, 'r') as csvFile:
            csvReader = csv.reader(csvFile, delimiter=",")
            for row in csvReader:
                nationID = int(row[0].strip())
                self.nations[nationID] = (row[1].strip(), row[2].strip(), row[3].strip())

    def open(self, fileName):
        self.fileName = fileName
        self.rawData = ''
        with open(fileName, 'rb') as pretFile:
            self.rawData = pretFile.read()
        if len(self.rawData) < 10:
            return False
        return self.is_dominion_file()

    def get_nation(self):
        nationID = self.rawData[26]

        nationCode = nationID
        # print("{} {}, {}".format(self.nations[nationCode][2], self.nations[nationCode][0], self.nations[nationCode][1]))
        return self.nations[nationCode]

    def get_era(self):
        return self.get_nation()[2]

    def get_nation_name(self):
        return self.get_nation()[0]

    def get_file_name(self):
        return self.fileName

    def get_name(self):
        xorValue = 79  # b'\x4F'
        terminator = 79  # b'\x4F'
        startPos = 0 # relative in name subpart
        pretNameStr = ''
        readPos = 0
        
        ignores = [0, 255]

        name_subpart = self.rawData.split(b'\xFF\xFF\xFF\xFF')[4]

        lastRead = b'\x00'
        while lastRead != terminator:
            lastRead = name_subpart[startPos + readPos]
            readPos = readPos + 1
            
            if lastRead in ignores: # we are reading pre name junk, move start pos forward, reset readPos back
                startPos += 1
                readPos -= 1
                
        for b in bytes(name_subpart[startPos:startPos + readPos - 1]):
            pretNameStr = pretNameStr + chr(b ^ xorValue)        

        return pretNameStr

    def is_dominion_file(self):
        # print(self.rawData[3:6])
        return self.rawData[3:6] == b'DOM'


def load_last_turn_file():
    try:
        with open(LAST_TURN_FILE, 'r') as jsonFile:
            jsonData = json.load(jsonFile)
        return jsonData
    except IOError:
        return {}


def save_last_turn_file(jsonData):
    with open(LAST_TURN_FILE, 'w') as jsonFile:
        json.dump(jsonData, jsonFile)


def get_pretender_path():
    gameDir = os.path.join(DOM_DATA_DIRECTORY, DOM_SAVE_GAME_SUBDIR, DOM_NEWLORDS_SUBDIR)
    return gameDir


def list_pretender_files():
    gameDir = get_pretender_path()
    gameFiles = [f for f in os.listdir(gameDir) if os.path.isfile(os.path.join(gameDir, f))]
    return gameFiles


def get_or_create_save_game_path(gameName):
    gameDir = get_save_game_path(gameName)
    try:
        os.makedirs(gameDir)
    except OSError as e:
        # if e.errno != errno.EEXIST:
        #	raise
        pass
    return gameDir


def list_save_game_files(gameName):
    gameDir = get_save_game_path(gameName)
    gameFiles = [f for f in os.listdir(gameDir) if os.path.isfile(os.path.join(gameDir, f))]
    return gameFiles


def get_save_game_turn_file_name(gameName):
    for f in list_save_game_files(gameName):
        if TURN_EXT in f:
            if f.split('_')[0].isnumeric():  # ignore backup files
                pass
            else:
                return f
    return None


def get_save_game_file_name(gameName):
    for f in list_save_game_files(gameName):
        if H_EXT in f:
            if f.split('_')[0].isnumeric():  # ignore backup files
                pass
            else:
                return f
    return None


def get_save_game_file_path(gameName):
    hfileName = get_save_game_file_name(gameName)
    if hfileName != None:
        return os.path.join(get_save_game_path(gameName), get_save_game_file_name(gameName))
    return None


def start_dominions(gameName):
    os.system(DOM_EXE + " --nocredits " + gameName)


def get_save_game_path(gameName):
    gameDir = os.path.join(DOM_DATA_DIRECTORY, DOM_SAVE_GAME_SUBDIR, gameName)
    return gameDir

if __name__ == '__main__':
    import unittest
    
    class TestPretenderFileNoPasswordRus(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.pretender_file_obj = PretenderFile()
            cls.pretender_file_obj.open("../test/early_bogarus_0.2h")
        
        def test_era(self):
            self.assertEqual(self.pretender_file_obj.get_era(), "EA")
            
        def test_nation(self):
            self.assertEqual(self.pretender_file_obj.get_nation_name(), "Rus")         
        
        def test_name(self):
            self.assertEqual(self.pretender_file_obj.get_name(), "Gerhart")  
            
    class TestPretenderFileNoPasswordUlm(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.pretender_file_obj = PretenderFile()
            cls.pretender_file_obj.open("../test/mid_ulm_1.2h")
        
        def test_era(self):
            self.assertEqual(self.pretender_file_obj.get_era(), "MA")
            
        def test_nation(self):
            self.assertEqual(self.pretender_file_obj.get_nation_name(), "Ulm")         
        
        def test_name(self):
            self.assertEqual(self.pretender_file_obj.get_name(), "Rend")    
            
    class TestPretenderFilePasswordJomon(unittest.TestCase):
        @classmethod
        def setUpClass(cls):
            cls.pretender_file_obj = PretenderFile()
            cls.pretender_file_obj.open("../test/late_jomon_0.2h")
        
        def test_era(self):
            self.assertEqual(self.pretender_file_obj.get_era(), "LA")
            
        def test_nation(self):
            self.assertEqual(self.pretender_file_obj.get_nation_name(), "Jomon")         
        
        def test_name(self):
            self.assertEqual(self.pretender_file_obj.get_name(), "Seiichi")      
    
    unittest.main(verbosity=True)