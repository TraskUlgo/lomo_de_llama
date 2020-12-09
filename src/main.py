
# LOMO DE LLAMA
# Automatic PBeM manager for Dominions 5 llamaserver.net
# Author: Rafael Stauffer rafael.stauffer@gmx.ch
# Version: 0.5.1

import imaplib
import smtplib
import email
from email.message import EmailMessage
import os
from pathlib import Path
import json
from sys import platform

from pretender import PretenderFile

import tkinter
from tkinter import *
from tkinter import messagebox

import shutil

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


FROM_EMAIL  = ""
FROM_PWD    = ""
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT   = 993

FETCH_PROTOCOL = '(RFC822)'

LLAMA_EMAIL = "@llamaserver.net"
TURN_EMAIL = "turns" + LLAMA_EMAIL
JOIN_EMAIL = "pretenders" + LLAMA_EMAIL

DOM_SAVEGAME_SUBDIR = "savedgames"
DOM_NEWLORDS_SUBDIR = "newlords"

TURN_EXT = ".trn"
H_EXT = ".2h"

LASTTURN_FILE = "lastturns.json"

EMAIL_FILE = "email.json"

BACKUP_TURNS = True
CURRENT_TURN = "current"

def filterChars(text):
	return text.strip("\t\n\r ")

class EmailWindow(Toplevel):
	def __init__(self):
		super().__init__()	
		self.title("Add gmail account")
		
		self.msgLbl = Label(self, text="Please enter your gmail information. You have to allow access for low security apps in gmail. It is adviced to use a secondary account just for this purpose.")
		self.msgLbl.pack()
		
		self.emailLbl = Label(self, text="Email address")
		self.emailLbl.pack()
		
		self.emailVar = StringVar(self)
		self.email = Entry(self, textvariable = self.emailVar)
		self.email.pack()
		
		self.emailPassLbl = Label(self, text="Email password")
		self.emailPassLbl.pack()
		
		self.emailPassVar = StringVar(self)
		self.emailPass = Entry(self, textvariable = self.emailPassVar)
		self.emailPass.pack()
		
		self.registerMailButton = Button(self, command=self.registerMail, text="registerMail")
		self.registerMailButton.pack()
		
	def registerMail(self, *args, **kwargs):
		global FROM_EMAIL
		global FROM_PWD
		email = self.emailVar.get()
		passwd = self.emailPassVar.get()
		
		if len(email) > 0 and len(passwd) > 0:
			try:
				mail = imaplib.IMAP4_SSL(SMTP_SERVER)
				mail.login(email,passwd)
				
				mail.select('inbox')
				
				#mail.quit()
				
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

def loadMail():
	global FROM_EMAIL
	global FROM_PWD
	
	jsonData = {}
	try:
		with open(EMAIL_FILE, 'r') as jsonFile:
			jsonData = json.load(jsonFile)
			FROM_EMAIL = jsonData["email"]
			FROM_PWD = jsonData["passwd"]
	except IOError:
		ew = EmailWindow()
		

def loadLastturnFile():
	try:
		with open(LASTTURN_FILE, 'r') as jsonFile:
			jsonData = json.load(jsonFile)
		return jsonData
	except IOError:
		return {}
	
def saveLastturnFile(jsonData):
	with open(LASTTURN_FILE, 'w') as jsonFile:
		json.dump(jsonData, jsonFile)

def getPretenderPath():
	gameDir = os.path.join(DOM_DATA_DIRECTORY, DOM_SAVEGAME_SUBDIR, DOM_NEWLORDS_SUBDIR)
	return gameDir

def listPretenderFiles():
	gameDir = getPretenderPath()
	gameFiles = [f for f in os.listdir(gameDir) if os.path.isfile(os.path.join(gameDir, f))]
	return gameFiles

def getSavegamePath(gameName):
	gameDir = os.path.join(DOM_DATA_DIRECTORY, DOM_SAVEGAME_SUBDIR, gameName)
	return gameDir
	
def getOrCreateSavegamePath(gameName):
	gameDir = getSavegamePath(gameName)
	try:
		os.makedirs(gameDir)
	except OSError as e:
		#if e.errno != errno.EEXIST:
		#	raise
		pass
	return gameDir

def listSavegameFiles(gameName):
	gameDir = getSavegamePath(gameName)
	gameFiles = [f for f in os.listdir(gameDir) if os.path.isfile(os.path.join(gameDir, f))]
	return gameFiles
	
def getSavegameTurnfileName(gameName):
	for f in listSavegameFiles(gameName):
		if TURN_EXT in f:
			if f.split('_')[0].isnumeric(): # ignore backup files
				pass
			else:
				return f
	return None
	
def getSavegameHfileName(gameName):
	for f in listSavegameFiles(gameName):
		if H_EXT in f:
			if f.split('_')[0].isnumeric(): # ignore backup files
				pass
			else:
				return f
	return None
	
def getSavegameHfilePath(gameName):
	hfileName = getSavegameHfileName(gameName)
	if hfileName != None:
		return os.path.join(getSavegamePath(gameName), getSavegameHfileName(gameName))
	return None

	
def startDominions(gameName):
	os.system(DOM_EXE + " --nocredits " + gameName)
	
def askForUpload():
	msgAnswer = messagebox.askyesno(title="Upload turnfile", message="Do you want to upload the turnfile now?")
	return msgAnswer

	#print()
	#answer = input("Upload turnfile now? [Y/n]: ").lower()
	#if answer == 'y' or answer == "":
	#	return True
	#else:
	#	return False

def extractFromSubject(subjectText):
	if "Reminder: " in subjectText:
		return (False, "", 0)
		
	if ": Pretender received for " in subjectText:
		messagebox.showinfo(title="Pretender received", message=subjectText)
		return (False, "", 0)
		
	if "Problem - " in subjectText:
		messagebox.showwarning(title="Problem", message=subjectText)
		return (False, "", 0)
		
	if " started! First turn attached" in subjectText:
		gameName = subjectText.split(' ')[0]
		return (True, gameName, 1)
		
	if ": Rolled back to turn " in subjectText:
		gameName = subjectText.split(':')[0]
		turnNumber = subjectText.split(' ')[-1]
	elif " " in subjectText.split(':')[0]:
		gameName = subjectText.split(':')[1].split()[0].split(',')[0]
		turnNumber = subjectText.lower().split('turn')[2].split()[0]
	else:
		gameName = subjectText.split(':')[0]
		if 'started!' in subjectText:
			turnNumber = '1'
		else:
			turnNumber = subjectText.lower().split('turn')[1].split()[0]
	return (True, gameName, turnNumber)

def readmail():

	lastTurns = loadLastturnFile()
	
	mail = imaplib.IMAP4_SSL(SMTP_SERVER)
	mail.login(FROM_EMAIL,FROM_PWD)
	
	mail.select('inbox')
	
	responseType, returnData = mail.search(None, 'FROM', TURN_EMAIL, '(UNSEEN)')
	
	mailIDs = returnData[0].split()
	
	#print(len(mailIDs), "new emails received")
	
	attPath = None
	gameName = None
	newTurnFoundGamenames = []
	turnNumber = -1
	
	if len(mailIDs) > 0:
		for mailID in mailIDs:
			responseType, mailParts = mail.fetch(mailID, FETCH_PROTOCOL)
			
			msg = email.message_from_bytes(mailParts[0][1])
			
			subject = email.header.decode_header(msg["Subject"])[0][0]
			if isinstance(subject, bytes):
				subject = subject.decode()
				
			needTurn, gameName, turnNumber = extractFromSubject(subject)
			
			if needTurn:
				if gameName in lastTurns: # check if we look at old turnfiles
					#if int(lastTurns[gameName]) >= int(turnNumber):
					#	continue
					#else:
					lastTurns[gameName] = turnNumber
				else: #if int(turnNumber) == 1: # this just started
					lastTurns[gameName] = turnNumber
					
				for part in msg.walk():
					if part.get_content_maintype() == 'multipart':
						continue
					
					if part.get('Content-Disposition') is None:
						continue
						
					filename = part.get_filename()
					attPath = os.path.join(getOrCreateSavegamePath(gameName), filename)
					
					fp = open(attPath, 'wb')
					fp.write(part.get_payload(decode=True))
					fp.close()
					
					if BACKUP_TURNS:
						attPath = os.path.join(getOrCreateSavegamePath(gameName), "{}_{}".format(turnNumber ,filename))
					
						fp = open(attPath, 'wb')
						fp.write(part.get_payload(decode=True))
						fp.close()
					
					newTurnFoundGamenames.append((gameName, turnNumber))
	
	mail.logout()
	
	if len(newTurnFoundGamenames) > 0:
		for gameName, turnNumber in newTurnFoundGamenames:
			messagebox.showinfo(title="New turn", message="New turn {} received for {}".format(turnNumber, gameName))
			startDominions(gameName)
			if askForUpload():
				uploadTurn(gameName, lastTurns[gameName])
	else:
		messagebox.showinfo(title="No new turns", message="No new turn received")
		#print("No new turn received")
		
	saveLastturnFile(lastTurns)
	
def uploadTurn(gameName, turnNumber):
	try:
		msg = EmailMessage()
		msg['Subject'] = filterChars(gameName)
		msg['From'] = FROM_EMAIL
		msg['To'] = TURN_EMAIL
		
		hFileName = getSavegameHfileName(gameName)
		
		hFilePath = getSavegameHfilePath(gameName)
		
		with open(hFilePath, 'rb') as fp:
			hData = fp.read()
		msg.add_attachment(hData, maintype='application', subtype='octet-stream', filename=hFileName)
		
		mail = smtplib.SMTP_SSL(SMTP_SERVER)
		mail.login(FROM_EMAIL,FROM_PWD)
		
		mail.send_message(msg)
		
		mail.quit()
		
		if BACKUP_TURNS:
			attPath = os.path.join(getOrCreateSavegamePath(gameName), "{}_{}".format(turnNumber ,hFileName))

			fp = open(attPath, 'wb')
			fp.write(hData)
			fp.close()
		
		messagebox.showinfo(title="Turn sent", message="Turn sent")
	except Exception as err:
		messagebox.showinfo(title="Error", message=str(err))
	
def uploadPretender(gameName, pretenderPath):
	try:
		msg = EmailMessage()
		msg['Subject'] = filterChars(gameName)
		msg['From'] = FROM_EMAIL
		msg['To'] = JOIN_EMAIL
		
		fileName = os.path.basename(pretenderPath)
		
		with open(pretenderPath, 'rb') as fp:
			pData = fp.read()
		msg.add_attachment(pData, maintype='application', subtype='octet-stream', filename=fileName)
		
		mail = smtplib.SMTP_SSL(SMTP_SERVER)
		mail.login(FROM_EMAIL,FROM_PWD)
		
		mail.send_message(msg)
		
		mail.quit()
	
		messagebox.showinfo(title="Pretender sent", message="Pretender sent")
	except Exception as err:
		messagebox.showinfo(title="Error", message=str(err))
		
	
class JoinWindow(Toplevel):
	def __init__(self):
		super().__init__()	
		self.title("Join Llama game")
		
		self.gameNameLbl = Label(self, text="Game name")
		self.gameNameLbl.pack()
		
		self.gameNameVar = StringVar(self)
		self.gameName = Entry(self, textvariable = self.gameNameVar)
		self.gameName.pack()
		
		self.pFrameLbl = Label(self, text="Pretender")
		self.pFrameLbl.pack()
		self.pFrame = PretenderFrame(self)
		
		self.joinGameButton = Button(self, command=self.joinNew, text="Join new game")
		self.joinGameButton.pack()
		
	def joinNew(self, *args, **kwargs):
		gName = self.gameNameVar.get()
		pretender = self.pFrame.getSelectedPretender()
		
		if len(gName) > 0 and pretender != None:
			uploadPretender(gName, pretender.getFilename())
			self.destroy()
		else:
			messagebox.showwarning(title="Problem", message="Name or pretender selection invalid please reselect")

class PretenderFrame(Frame):
	def __init__(self, master=None):
		super().__init__(master)
		
		self.availablePretenders = Listbox(self)
		self.availablePretenders.pack()
		
		self.fillAvailablePretenders()
		
		self.pack()
			
	def fillAvailablePretenders(self):
		self.pretenderFiles = []
		for pretenderFileName in listPretenderFiles():
			self.pretenderFiles.append(PretenderFile())
			pretender = self.pretenderFiles[-1]
			if pretender.open(os.path.join(DOM_DATA_DIRECTORY, DOM_SAVEGAME_SUBDIR, DOM_NEWLORDS_SUBDIR, pretenderFileName)):
				pretenderDescription = "{}, {}, {}".format(pretender.getEra(), pretender.getNationName(), pretender.getName())
				self.availablePretenders.insert(END, pretenderDescription)
				
	def getSelectedPretender(self):
		if len(self.availablePretenders.curselection()) > 0:
			return self.pretenderFiles[self.availablePretenders.curselection()[0]]
		return None

class ManagerFrame(Frame):
	def __init__(self, master=None):
		super().__init__(master)
		
		self.activeGames = Listbox(self)
		
		#self.activeGames.bind('<Button-1>', self.getAvailableTurns) 
		self.activeGames.bind('<Double-Button>', self.getAvailableTurns)
		
		self.activeGames.pack()
		
		self.fillActiveGames()
		
		self.turns = [CURRENT_TURN]
		self.activeTurn = StringVar(self)
		self.activeTurn.set(self.turns[0])
		
		self.activeTurnMenu = OptionMenu(self, self.activeTurn, *self.turns)
		self.activeTurnMenu.pack()
		
		self.getTurnsButton = Button(self, command=self.getTurns, text="Get turns")
		self.joinGameButton = Button(self, command=self.joinNew, text="Join new game")
		self.openGameButton = Button(self, command=self.openGame, text="Open game")
		
		self.getTurnsButton.pack()
		self.joinGameButton.pack()
		self.openGameButton.pack()
		
		self.pack()
		
		loadMail()
			
	def fillActiveGames(self):
		self.activeGames.delete(0,END)
		lastTurns = loadLastturnFile()
		for gameName in lastTurns:
			self.activeGames.insert(END, gameName)
		
	def getTurns(self, *args, **kwargs):
		readmail()
		self.fillActiveGames()
		
	def joinNew(self, *args, **kwargs):
		self.joinWindow = JoinWindow()
		
	def getAvailableTurns(self, *args, **kwargs):
		
		self.turns = []
		if len(self.activeGames.curselection()) > 0:
			selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])
			
			lastTurns = loadLastturnFile()
			
			
			for i in range(int(lastTurns[selectedGameName])):
				self.turns.append(i)
		self.turns.append(CURRENT_TURN)
		
		self.activeTurnMenu['menu'].delete(0, 'end')
		for turn in self.turns:
			self.activeTurnMenu['menu'].add_command(label=turn, command=tkinter._setit(self.activeTurn, turn))
		
		self.activeTurn.set(self.turns[-1])
			
			
	def openGame(self, *args, **kwargs):
		if len(self.activeGames.curselection()) > 0:
			if self.activeTurn.get() != CURRENT_TURN:
				turnNumber = self.activeTurn.get()
				selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])
				
				tempTurnpath = "{}_{}".format(selectedGameName, turnNumber)
				tempFolderPath = getOrCreateSavegamePath(tempTurnpath)
				
				originalFolderPath = getOrCreateSavegamePath(selectedGameName)
				
				tFile = getSavegameTurnfileName(selectedGameName)
				hFile = getSavegameHfileName(selectedGameName)
				
				shutil.copy(os.path.join(originalFolderPath, "{}_{}".format(turnNumber, tFile)), os.path.join(tempFolderPath, tFile))
				shutil.copy(os.path.join(originalFolderPath, "{}_{}".format(turnNumber, hFile)), os.path.join(tempFolderPath, hFile))
				
				startDominions(tempTurnpath)
				
				shutil.rmtree(tempFolderPath)
			else:
				selectedGameName = self.activeGames.get(self.activeGames.curselection()[0])
				
				lastTurns = loadLastturnFile()
				lastTurnNumber = int(lastTurns[selectedGameName])
				
				startDominions(selectedGameName)
				if askForUpload():
					uploadTurn(selectedGameName, lastTurnNumber)
		
if __name__ == '__main__':
	root = Tk()
	pebmApp = ManagerFrame(root)
	root.wm_title("Dom5 PEBM")
	root.mainloop()
