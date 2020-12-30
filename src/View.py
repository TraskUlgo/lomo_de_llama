import imaplib
import json
import os
import shutil
import tkinter as tk
import MailController as mc
import GameFileController as gfc
from tkinter import messagebox


class ManagerFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.activeGames = tk.Listbox(self)

        # self.activeGames.bind('<Button-1>', self.getAvailableTurns)
        self.activeGames.bind('<Double-Button>', self.get_available_turns)

        self.activeGames.pack()

        self.fill_active_games()

        self.turns = [gfc.CURRENT_TURN]
        self.activeTurn = tk.StringVar(self)
        self.activeTurn.set(self.turns[0])

        self.activeTurnMenu = tk.OptionMenu(self, self.activeTurn, *self.turns)
        self.activeTurnMenu.pack()

        self.getTurnsButton = tk.Button(self, command=self.get_turns, text="Get turns")
        self.joinGameButton = tk.Button(self, command=self.join_new, text="Join new game")
        self.openGameButton = tk.Button(self, command=self.open_game, text="Open game")

        self.getTurnsButton.pack()
        self.joinGameButton.pack()
        self.openGameButton.pack()

        self.pack()

        mc.load_mail()

    def fill_active_games(self):
        self.activeGames.delete(0, tk.END)
        last_turns = gfc.load_last_turn_file()
        for gameName in last_turns:
            self.activeGames.insert(tk.END, gameName)

    def get_turns(self):
        mc.read_mail()
        self.fill_active_games()

    def join_new(self):
        self.joinWindow = JoinWindow()

    def get_available_turns(self):

        self.turns = []
        if len(self.activeGames.curselection()) > 0:
            selected_game_name = self.activeGames.get(self.activeGames.curselection()[0])

            last_turns = gfc.load_last_turn_file()

            for i in range(int(last_turns[selected_game_name])):
                self.turns.append(i)
        self.turns.append(gfc.CURRENT_TURN)

        self.activeTurnMenu['menu'].delete(0, 'end')
        for turn in self.turns:
            self.activeTurnMenu['menu'].add_command(label=turn, command=tk._setit(self.activeTurn, turn))

        self.activeTurn.set(self.turns[-1])

    def open_game(self):
        if len(self.activeGames.curselection()) > 0:
            if self.activeTurn.get() != gfc.CURRENT_TURN:
                turnNumber = self.activeTurn.get()
                selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])

                tempTurnpath = "{}_{}".format(selectedGameName, turnNumber)
                tempFolderPath = gfc.get_or_create_save_game_path(tempTurnpath)

                originalFolderPath = gfc.get_or_create_save_game_path(selectedGameName)

                tFile = gfc.get_save_game_turn_file_name(selectedGameName)
                hFile = gfc.get_save_game_file_name(selectedGameName)

                shutil.copy(os.path.join(originalFolderPath, "{}_{}".format(turnNumber, tFile)),
                            os.path.join(tempFolderPath, tFile))
                shutil.copy(os.path.join(originalFolderPath, "{}_{}".format(turnNumber, hFile)),
                            os.path.join(tempFolderPath, hFile))

                gfc.start_dominions(tempTurnpath)

                shutil.rmtree(tempFolderPath)
            else:
                selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])

                lastTurns = gfc.load_last_turn_file()
                lastTurnNumber = int(lastTurns[selectedGameName])

                gfc.start_dominions(selectedGameName)
                if ask_for_upload():
                    mc.upload_turn(selectedGameName, lastTurnNumber)


class PretenderFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)

        self.availablePretenders = tk.Listbox(self)
        self.availablePretenders.pack()

        self.fill_available_pretenders()

        self.pack()

    def fill_available_pretenders(self):
        self.pretenderFiles = []
        for pretenderFileName in gfc.list_pretender_files():
            self.pretenderFiles.append(gfc.PretenderFile())
            pretender = self.pretenderFiles[-1]
            if pretender.open(
                    os.path.join(gfc.DOM_DATA_DIRECTORY, gfc.DOM_SAVE_GAME_SUBDIR, gfc.DOM_NEWLORDS_SUBDIR, pretenderFileName)):
                pretenderDescription = "{}, {}, {}".format(pretender.get_era(), pretender.get_nation_name(),
                                                           pretender.get_name())
                self.availablePretenders.insert(tk.END, pretenderDescription)

    def get_selected_pretender(self):
        if len(self.availablePretenders.curselection()) > 0:
            return self.pretenderFiles[self.availablePretenders.curselection()[0]]
        return None


class JoinWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Join Llama game")

        self.gameNameLbl = tk.Label(self, text="Game name")
        self.gameNameLbl.pack()

        self.gameNameVar = tk.StringVar(self)
        self.gameName = tk.Entry(self, textvariable=self.gameNameVar)
        self.gameName.pack()

        self.pFrameLbl = tk.Label(self, text="Pretender")
        self.pFrameLbl.pack()
        self.pFrame = PretenderFrame(self)

        self.joinGameButton = tk.Button(self, command=self.join_new, text="Join new game")
        self.joinGameButton.pack()

    def join_new(self):
        gName = self.gameNameVar.get()
        pretender = self.pFrame.get_selected_pretender()

        if len(gName) > 0 and pretender != None:
            mc.upload_pretender(gName, pretender.get_file_name())
            self.destroy()
        else:
            tk.messagebox.showwarning(title="Problem", message="Name or pretender selection invalid please reselect")


class EmailWindow(tk.Toplevel):
    def __init__(self):
        super().__init__()
        self.title("Add gmail account")

        self.msgLbl = tk.Label(self,
                               text="Please enter your gmail information. You have to allow access for low security apps in gmail. It is adviced to use a secondary account just for this purpose.")
        self.msgLbl.pack()

        self.emailLbl = tk.Label(self, text="Email address")
        self.emailLbl.pack()

        self.emailVar = tk.StringVar(self)
        self.email = tk.Entry(self, textvariable=self.emailVar)
        self.email.pack()

        self.emailPassLbl = tk.Label(self, text="Email password")
        self.emailPassLbl.pack()

        self.emailPassVar = tk.StringVar(self)
        self.emailPass = tk.Entry(self, textvariable=self.emailPassVar)
        self.emailPass.pack()

        self.registerMailButton = tk.Button(self, command=self.register_mail, text="registerMail")
        self.registerMailButton.pack()

    def register_mail(self):
        email = self.emailVar.get()
        passwd = self.emailPassVar.get()

        if len(email) > 0 and len(passwd) > 0:
            try:
                mail = imaplib.IMAP4_SSL(mc.SMTP_SERVER)
                mail.login(email, passwd)

                mail.select('inbox')

                FROM_EMAIL = email
                FROM_PWD = passwd

                jsonData = {"email": FROM_EMAIL, "passwd": FROM_PWD}
                with open(mc.EMAIL_FILE, 'w') as jsonFile:
                    json.dump(jsonData, jsonFile)

                self.destroy()

            except Exception as err:
                tk.messagebox.showerror(title="Problem", message=str(err))
        else:
            tk.messagebox.showerror(title="Problem", message="Please enter email and password")


def ask_for_upload():
    msgAnswer = tk.messagebox.askyesno(title="Upload turnfile", message="Do you want to upload the turnfile now?")
    return msgAnswer


def run():
    window = tk.Tk()
    window.title("lomo de llama")
    window.geometry("500x500")
    ManagerFrame(window)
    window.mainloop()
