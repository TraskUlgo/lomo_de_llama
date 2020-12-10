# LOMO DE LLAMA
# Automatic PBeM manager for Dominions 5 llamaserver.net
# Author: Rafael Stauffer rafael.stauffer@gmx.ch
# Version: 0.5.1

import os
from pathlib import Path
from sys import platform
from tkinter import *

from src.View import ManagerFrame

if platform == "linux":
    # linux
    DOM_DATA_DIRECTORY = str(Path.home()) + "/.dominions5/"
    DOM_EXE = str(Path.home()) + "/.local/share/Steam/steamapps/common/Dominions5/dom5.sh"
elif platform == "darwin":
    # OS X
    DOM_DATA_DIRECTORY = str(Path.home()) + "/.dominions5/"
    DOM_EXE = str(Path.home()) + "/.local/share/Steam/steamapps/common/Dominions5/dom5.sh"
elif platform == "win32":
    # Windows
    DOM_DATA_DIRECTORY = os.path.expandvars(r'%APPDATA%\\Dominions5\\')
    DOM_EXE = "\"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Dominions5\\Dominions5.exe\""

FROM_EMAIL = ""
FROM_PWD = ""
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT = 993

FETCH_PROTOCOL = '(RFC822)'

LLAMA_EMAIL = "@llamaserver.net"
TURN_EMAIL = "turns" + LLAMA_EMAIL
JOIN_EMAIL = "pretenders" + LLAMA_EMAIL

DOM_SAVE_GAME_SUBDIR = "savedgames"
DOM_NEWLORDS_SUBDIR = "newlords"

TURN_EXT = ".trn"
H_EXT = ".2h"

LAST_TURN_FILE = "lastturns.json"

EMAIL_FILE = "email.json"

BACKUP_TURNS = True
CURRENT_TURN = "current"


def filter_chars(text):
    return text.strip("\t\n\r ")


if __name__ == '__main__':
    root = Tk()
    pebmApp = ManagerFrame(root)
    root.wm_title("Dom5 PEBM")
    root.mainloop()
