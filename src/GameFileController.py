# PretenderFile
# Interpreter for dom5 newlords files
# Author: Rafael Stauffer rafael.stauffer@gmx.ch
# Version: 0.1

import csv
import json
import os

from src.MailController import get_save_game_path
from src.main import LAST_TURN_FILE, DOM_DATA_DIRECTORY, DOM_SAVE_GAME_SUBDIR, DOM_NEWLORDS_SUBDIR, TURN_EXT, H_EXT, \
    DOM_EXE


class PretenderFile():
    def __init__(self):
        self.fileName = ""
        self.rawData = ''
        self.nations = {}
        self.read_nations_lookup('nations.csv')

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
        terminator = 79  # b'O' #b'\x78'
        startPos = 132
        pretNameStr = ''
        readPos = 0

        lastRead = b'\x00'
        while lastRead != terminator:
            lastRead = self.rawData[startPos + readPos]
            readPos = readPos + 1

        for b in bytes(self.rawData[startPos:startPos + readPos - 1]):
            pretNameStr = pretNameStr + chr(b ^ xorValue)

        # print(pretNameStr)
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
