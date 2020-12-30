# PretenderFile
# Interpreter for dom5 newlords files
# Author: Rafael Stauffer rafael.stauffer@gmx.ch
# Version: 0.1

import csv
import json
import os
from pathlib import Path
from sys import platform

DOM_DATA_DIRECTORY = ""
DOM_EXE = ""

DOM_SAVE_GAME_SUBDIR = "savedgames"
DOM_NEWLORDS_SUBDIR = "newlords"
TURN_EXT = ".trn"
H_EXT = ".2h"
LAST_TURN_FILE = "../data/lastturns.json"
BACKUP_TURNS = True
CURRENT_TURN = "current"


class PretenderFile:
    def __init__(self):
        self.fileName = ""
        self.rawData = ''
        self.nations = {}
        self.read_nations_lookup('../data/nations.csv')

    def read_nations_lookup(self, file_name):
        # nation csv file has following line structure: nationID,nationName,nationTitle,era
        self.nations = {}
        with open(file_name, 'r') as csvFile:
            csv_reader = csv.reader(csvFile, delimiter=",")
            for row in csv_reader:
                nation_id = int(row[0].strip())
                self.nations[nation_id] = (row[1].strip(), row[2].strip(), row[3].strip())

    def open(self, file_name):
        self.fileName = file_name
        self.rawData = ''
        with open(file_name, 'rb') as pretFile:
            self.rawData = pretFile.read()
        if len(self.rawData) < 10:
            return False
        return self.is_dominion_file()

    def get_nation(self):
        nation_id = self.rawData[26]

        nation_code = nation_id
        # print("{} {}, {}".format(self.nations[nationCode][2],
        # self.nations[nationCode][0], self.nations[nationCode][1]))
        return self.nations[nation_code]

    def get_era(self):
        return self.get_nation()[2]

    def get_nation_name(self):
        return self.get_nation()[0]

    def get_file_name(self):
        return self.fileName

    def get_name(self):
        xor_value = 79  # b'\x4F'
        terminator = 79  # b'O' #b'\x78'
        start_pos = 132
        pret_name_str = ''
        read_pos = 0

        last_read = b'\x00'
        while last_read != terminator:
            last_read = self.rawData[start_pos + read_pos]
            read_pos = read_pos + 1

        for b in bytes(self.rawData[start_pos:start_pos + read_pos - 1]):
            pret_name_str = pret_name_str + chr(b ^ xor_value)

        # print(pretNameStr)
        return pret_name_str

    def is_dominion_file(self):
        # print(self.rawData[3:6])
        return self.rawData[3:6] == b'DOM'


def load_last_turn_file():
    try:
        with open(LAST_TURN_FILE, 'r') as jsonFile:
            json_data = json.load(jsonFile)
        return json_data
    except IOError:
        return {}


def save_last_turn_file(json_data):
    with open(LAST_TURN_FILE, 'w') as jsonFile:
        json.dump(json_data, jsonFile)


def get_pretender_path():
    game_dir = os.path.join(DOM_DATA_DIRECTORY, DOM_SAVE_GAME_SUBDIR, DOM_NEWLORDS_SUBDIR)
    return game_dir


def list_pretender_files():
    game_dir = get_pretender_path()
    game_files = [f for f in os.listdir(game_dir) if os.path.isfile(os.path.join(game_dir, f))]
    return game_files


def get_or_create_save_game_path(game_name):
    game_dir = get_save_game_path(game_name)
    try:
        os.makedirs(game_dir)
    except OSError as e:
        # if e.errno != errno.EEXIST:
        # raise
        pass
    return game_dir


def list_save_game_files(game_name):
    game_dir = get_save_game_path(game_name)
    game_files = [f for f in os.listdir(game_dir) if os.path.isfile(os.path.join(game_dir, f))]
    return game_files


def get_save_game_turn_file_name(game_name):
    for f in list_save_game_files(game_name):
        if TURN_EXT in f:
            if f.split('_')[0].isnumeric():  # ignore backup files
                pass
            else:
                return f
    return None


def get_save_game_file_name(game_name):
    for f in list_save_game_files(game_name):
        if H_EXT in f:
            if f.split('_')[0].isnumeric():  # ignore backup files
                pass
            else:
                return f
    return None


def get_save_game_file_path(game_name):
    h_file_name = get_save_game_file_name(game_name)
    if h_file_name is not None:
        return os.path.join(get_save_game_path(game_name), get_save_game_file_name(game_name))
    return None


def start_dominions(game_name):
    os.system(DOM_EXE + " --nocredits " + game_name)


def get_save_game_path(game_name):
    game_dir = os.path.join(DOM_DATA_DIRECTORY, DOM_SAVE_GAME_SUBDIR, game_name)
    return game_dir


