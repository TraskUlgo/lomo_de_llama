# LOMO DE LLAMA
# Automatic PBeM manager for Dominions 5 llamaserver.net
# Author: Rafael Stauffer rafael.stauffer@gmx.ch
# Version: 0.5.1

import os
from pathlib import Path
from sys import platform

import View

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


def main():
    View.run()


if __name__ == '__main__':
    main()
