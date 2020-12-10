import imaplib
import json
import os
import shutil
import tkinter
from tkinter import Frame, Listbox, StringVar, OptionMenu, Button, END, Toplevel, Label, Entry, messagebox

from src.GameFileController import PretenderFile, load_last_turn_file, list_pretender_files, \
    get_or_create_save_game_path, get_save_game_turn_file_name, get_save_game_file_name, start_dominions
from src.MailController import load_mail, read_mail, upload_turn, upload_pretender
from src.main import CURRENT_TURN, DOM_DATA_DIRECTORY, DOM_SAVE_GAME_SUBDIR, DOM_NEWLORDS_SUBDIR, SMTP_SERVER, \
    EMAIL_FILE


class ManagerFrame(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.activeGames = Listbox(self)

        # self.activeGames.bind('<Button-1>', self.getAvailableTurns)
        self.activeGames.bind('<Double-Button>', self.get_available_turns)

        self.activeGames.pack()

        self.fill_active_games()

        self.turns = [CURRENT_TURN]
        self.activeTurn = StringVar(self)
        self.activeTurn.set(self.turns[0])

        self.activeTurnMenu = OptionMenu(self, self.activeTurn, *self.turns)
        self.activeTurnMenu.pack()

        self.getTurnsButton = Button(self, command=self.get_turns, text="Get turns")
        self.joinGameButton = Button(self, command=self.join_new, text="Join new game")
        self.openGameButton = Button(self, command=self.open_game, text="Open game")

        self.getTurnsButton.pack()
        self.joinGameButton.pack()
        self.openGameButton.pack()

        self.pack()

        load_mail()

    def fill_active_games(self):
        self.activeGames.delete(0, END)
        lastTurns = load_last_turn_file()
        for gameName in lastTurns:
            self.activeGames.insert(END, gameName)

    def get_turns(self, *args, **kwargs):
        read_mail()
        self.fill_active_games()

    def join_new(self, *args, **kwargs):
        self.joinWindow = JoinWindow()

    def get_available_turns(self, *args, **kwargs):

        self.turns = []
        if len(self.activeGames.curselection()) > 0:
            selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])

            lastTurns = load_last_turn_file()

            for i in range(int(lastTurns[selectedGameName])):
                self.turns.append(i)
        self.turns.append(CURRENT_TURN)

        self.activeTurnMenu['menu'].delete(0, 'end')
        for turn in self.turns:
            self.activeTurnMenu['menu'].add_command(label=turn, command=tkinter._setit(self.activeTurn, turn))

        self.activeTurn.set(self.turns[-1])

    def open_game(self, *args, **kwargs):
        if len(self.activeGames.curselection()) > 0:
            if self.activeTurn.get() != CURRENT_TURN:
                turnNumber = self.activeTurn.get()
                selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])

                tempTurnpath = "{}_{}".format(selectedGameName, turnNumber)
                tempFolderPath = get_or_create_save_game_path(tempTurnpath)

                originalFolderPath = get_or_create_save_game_path(selectedGameName)

                tFile = get_save_game_turn_file_name(selectedGameName)
                hFile = get_save_game_file_name(selectedGameName)

                shutil.copy(os.path.join(originalFolderPath, "{}_{}".format(turnNumber, tFile)),
                            os.path.join(tempFolderPath, tFile))
                shutil.copy(os.path.join(originalFolderPath, "{}_{}".format(turnNumber, hFile)),
                            os.path.join(tempFolderPath, hFile))

                start_dominions(tempTurnpath)

                shutil.rmtree(tempFolderPath)
            else:
                selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])

                lastTurns = load_last_turn_file()
                lastTurnNumber = int(lastTurns[selectedGameName])

                start_dominions(selectedGameName)
                if ask_for_upload():
                    upload_turn(selectedGameName, lastTurnNumber)


class PretenderFrame(Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.availablePretenders = Listbox(self)
        self.availablePretenders.pack()

        self.fill_available_pretenders()

        self.pack()

    def fill_available_pretenders(self):
        self.pretenderFiles = []
        for pretenderFileName in list_pretender_files():
            self.pretenderFiles.append(PretenderFile())
            pretender = self.pretenderFiles[-1]
            if pretender.open(
                    os.path.join(DOM_DATA_DIRECTORY, DOM_SAVE_GAME_SUBDIR, DOM_NEWLORDS_SUBDIR, pretenderFileName)):
                pretenderDescription = "{}, {}, {}".format(pretender.get_era(), pretender.get_nation_name(),
                                                           pretender.get_name())
                self.availablePretenders.insert(END, pretenderDescription)

    def get_selected_pretender(self):
        if len(self.availablePretenders.curselection()) > 0:
            return self.pretenderFiles[self.availablePretenders.curselection()[0]]
        return None


class JoinWindow(Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Join Llama game")

        self.gameNameLbl = Label(self, text="Game name")
        self.gameNameLbl.pack()

        self.gameNameVar = StringVar(self)
        self.gameName = Entry(self, textvariable=self.gameNameVar)
        self.gameName.pack()

        self.pFrameLbl = Label(self, text="Pretender")
        self.pFrameLbl.pack()
        self.pFrame = PretenderFrame(self)

        self.joinGameButton = Button(self, command=self.join_new, text="Join new game")
        self.joinGameButton.pack()

    def join_new(self, *args, **kwargs):
        gName = self.gameNameVar.get()
        pretender = self.pFrame.get_selected_pretender()

        if len(gName) > 0 and pretender != None:
            upload_pretender(gName, pretender.get_file_name())
            self.destroy()
        else:
            messagebox.showwarning(title="Problem", message="Name or pretender selection invalid please reselect")


class EmailWindow(Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Add gmail account")

        self.msgLbl = Label(self,
                            text="Please enter your gmail information. You have to allow access for low security apps in gmail. It is adviced to use a secondary account just for this purpose.")
        self.msgLbl.pack()

        self.emailLbl = Label(self, text="Email address")
        self.emailLbl.pack()

        self.emailVar = StringVar(self)
        self.email = Entry(self, textvariable=self.emailVar)
        self.email.pack()

        self.emailPassLbl = Label(self, text="Email password")
        self.emailPassLbl.pack()

        self.emailPassVar = StringVar(self)
        self.emailPass = Entry(self, textvariable=self.emailPassVar)
        self.emailPass.pack()

        self.registerMailButton = Button(self, command=self.register_mail, text="registerMail")
        self.registerMailButton.pack()

    def register_mail(self, *args, **kwargs):
        global FROM_EMAIL
        global FROM_PWD
        email = self.emailVar.get()
        passwd = self.emailPassVar.get()

        if len(email) > 0 and len(passwd) > 0:
            try:
                mail = imaplib.IMAP4_SSL(SMTP_SERVER)
                mail.login(email, passwd)

                mail.select('inbox')

                # mail.quit()

                FROM_EMAIL = email
                FROM_PWD = passwd

                jsonData = {"email": FROM_EMAIL, "passwd": FROM_PWD}
                with open(EMAIL_FILE, 'w') as jsonFile:
                    json.dump(jsonData, jsonFile)

                self.destroy()

            except Exception as err:
                messagebox.showerror(title="Problem", message=str(err))
        else:
            messagebox.showerror(title="Problem", message="Please enter email and password")


def ask_for_upload():
    msgAnswer = messagebox.askyesno(title="Upload turnfile", message="Do you want to upload the turnfile now?")
    return msgAnswer
