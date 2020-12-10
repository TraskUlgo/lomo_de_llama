import email
import imaplib
import json
import os
import smtplib
from email.message import EmailMessage
from tkinter import messagebox

from src.GameFileController import load_last_turn_file, get_or_create_save_game_path, start_dominions, \
    save_last_turn_file, get_save_game_file_name, get_save_game_file_path, BACKUP_TURNS


#from src.View import EmailWindow, ask_for_upload


def load_mail():
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


def extract_from_subject(subjectText):
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


def read_mail():
    lastTurns = load_last_turn_file()

    mail = imaplib.IMAP4_SSL(SMTP_SERVER)
    mail.login(FROM_EMAIL, FROM_PWD)

    mail.select('inbox')

    responseType, returnData = mail.search(None, 'FROM', TURN_EMAIL, '(UNSEEN)')

    mailIDs = returnData[0].split()

    # print(len(mailIDs), "new emails received")

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

            needTurn, gameName, turnNumber = extract_from_subject(subject)

            if needTurn:
                if gameName in lastTurns:  # check if we look at old turnfiles
                    # if int(lastTurns[gameName]) >= int(turnNumber):
                    #	continue
                    # else:
                    lastTurns[gameName] = turnNumber
                else:  # if int(turnNumber) == 1: # this just started
                    lastTurns[gameName] = turnNumber

                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue

                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    attPath = os.path.join(get_or_create_save_game_path(gameName), filename)

                    fp = open(attPath, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()

                    if BACKUP_TURNS:
                        attPath = os.path.join(get_or_create_save_game_path(gameName),
                                               "{}_{}".format(turnNumber, filename))

                        fp = open(attPath, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()

                    newTurnFoundGamenames.append((gameName, turnNumber))

    mail.logout()

    if len(newTurnFoundGamenames) > 0:
        for gameName, turnNumber in newTurnFoundGamenames:
            messagebox.showinfo(title="New turn", message="New turn {} received for {}".format(turnNumber, gameName))
            start_dominions(gameName)
            if ask_for_upload():
                upload_turn(gameName, lastTurns[gameName])
    else:
        messagebox.showinfo(title="No new turns", message="No new turn received")
    # print("No new turn received")

    save_last_turn_file(lastTurns)


def upload_turn(gameName, turnNumber):
    try:
        msg = EmailMessage()
        msg['Subject'] = filter_chars(gameName)
        msg['From'] = FROM_EMAIL
        msg['To'] = TURN_EMAIL

        hFileName = get_save_game_file_name(gameName)

        hFilePath = get_save_game_file_path(gameName)

        with open(hFilePath, 'rb') as fp:
            hData = fp.read()
        msg.add_attachment(hData, maintype='application', subtype='octet-stream', filename=hFileName)

        mail = smtplib.SMTP_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, FROM_PWD)

        mail.send_message(msg)

        mail.quit()

        if BACKUP_TURNS:
            attPath = os.path.join(get_or_create_save_game_path(gameName), "{}_{}".format(turnNumber, hFileName))

            fp = open(attPath, 'wb')
            fp.write(hData)
            fp.close()

        messagebox.showinfo(title="Turn sent", message="Turn sent")
    except Exception as err:
        messagebox.showinfo(title="Error", message=str(err))


def upload_pretender(gameName, pretenderPath):
    try:
        msg = EmailMessage()
        msg['Subject'] = filter_chars(gameName)
        msg['From'] = FROM_EMAIL
        msg['To'] = JOIN_EMAIL

        fileName = os.path.basename(pretenderPath)

        with open(pretenderPath, 'rb') as fp:
            pData = fp.read()
        msg.add_attachment(pData, maintype='application', subtype='octet-stream', filename=fileName)

        mail = smtplib.SMTP_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, FROM_PWD)

        mail.send_message(msg)

        mail.quit()

        messagebox.showinfo(title="Pretender sent", message="Pretender sent")
    except Exception as err:
        messagebox.showinfo(title="Error", message=str(err))


def filter_chars(text):
    return text.strip("\t\n\r ")


EMAIL_FILE = "email.json"
FROM_EMAIL = ""
FROM_PWD = ""
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT = 993
FETCH_PROTOCOL = '(RFC822)'
LLAMA_EMAIL = "@llamaserver.net"
TURN_EMAIL = "turns" + LLAMA_EMAIL
JOIN_EMAIL = "pretenders" + LLAMA_EMAIL