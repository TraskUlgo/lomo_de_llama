import email
import imaplib
import json
import os
import smtplib
from email.message import EmailMessage
from tkinter import messagebox
import view
import gamefilecontroller as gfc

EMAIL_FILE = "email.json"
FROM_EMAIL = ""
FROM_PWD = ""
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT = 993
FETCH_PROTOCOL = '(RFC822)'
LLAMA_EMAIL = "@llamaserver.net"
TURN_EMAIL = "turns" + LLAMA_EMAIL
JOIN_EMAIL = "pretenders" + LLAMA_EMAIL


def load_mail():
    try:
        with open(EMAIL_FILE, 'r') as jsonFile:
            json_data = json.load(jsonFile)
            FROM_EMAIL = json_data["email"]
            FROM_PWD = json_data["passwd"]
    except IOError:
        view.EmailWindow()


def extract_from_subject(subject_text):
    if "Reminder: " in subject_text:
        return False, "", 0

    if ": Pretender received for " in subject_text:
        messagebox.showinfo(title="Pretender received", message=subject_text)
        return False, "", 0

    if "Problem - " in subject_text:
        messagebox.showwarning(title="Problem", message=subject_text)
        return False, "", 0

    if " started! First turn attached" in subject_text:
        game_name = subject_text.split(' ')[0]
        return True, game_name, 1

    if ": Rolled back to turn " in subject_text:
        game_name = subject_text.split(':')[0]
        turn_number = subject_text.split(' ')[-1]
    elif " " in subject_text.split(':')[0]:
        game_name = subject_text.split(':')[1].split()[0].split(',')[0]
        turn_number = subject_text.lower().split('turn')[2].split()[0]
    else:
        game_name = subject_text.split(':')[0]
        if 'started!' in subject_text:
            turn_number = '1'
        else:
            turn_number = subject_text.lower().split('turn')[1].split()[0]
    return True, game_name, turn_number


def read_mail():
    last_turns = gfc.load_last_turn_file()

    mail = imaplib.IMAP4_SSL(SMTP_SERVER)
    mail.login(FROM_EMAIL, FROM_PWD)

    mail.select('inbox')

    response_type, return_data = mail.search(None, 'FROM', TURN_EMAIL, '(UNSEEN)')

    mail_ids = return_data[0].split()

    # print(len(mailIDs), "new emails received")

    att_path = None
    game_name = None
    new_turn_found_game_names = []
    turn_number = -1

    if len(mail_ids) > 0:
        for mailID in mail_ids:
            response_type, mail_parts = mail.fetch(mailID, FETCH_PROTOCOL)

            msg = email.message_from_bytes(mail_parts[0][1])

            subject = email.header.decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()

            need_turn, game_name, turn_number = extract_from_subject(subject)

            if need_turn:
                if game_name in last_turns:  # check if we look at old turn files
                    # if int(lastTurns[gameName]) >= int(turnNumber):
                    # continue
                    # else:
                    last_turns[game_name] = turn_number
                else:  # if int(turnNumber) == 1: # this just started
                    last_turns[game_name] = turn_number

                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue

                    if part.get('Content-Disposition') is None:
                        continue

                    filename = part.get_filename()
                    att_path = os.path.join(gfc.get_or_create_save_game_path(game_name), filename)

                    fp = open(att_path, 'wb')
                    fp.write(part.get_payload(decode=True))
                    fp.close()

                    if gfc.BACKUP_TURNS:
                        att_path = os.path.join(gfc.get_or_create_save_game_path(game_name),
                                                "{}_{}".format(turn_number, filename))

                        fp = open(att_path, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()

                    new_turn_found_game_names.append((game_name, turn_number))

    mail.logout()

    if len(new_turn_found_game_names) > 0:
        for game_name, turn_number in new_turn_found_game_names:
            messagebox.showinfo(title="New turn", message="New turn {} received for {}".format(turn_number, game_name))
            gfc.start_dominions(game_name)
            if view.ask_for_upload():
                upload_turn(game_name, last_turns[game_name])
    else:
        messagebox.showinfo(title="No new turns", message="No new turn received")
    # print("No new turn received")

    gfc.save_last_turn_file(last_turns)


def upload_turn(game_name, turn_number):
    try:
        msg = EmailMessage()
        msg['Subject'] = filter_chars(game_name)
        msg['From'] = FROM_EMAIL
        msg['To'] = TURN_EMAIL

        h_file_name = gfc.get_save_game_file_name(game_name)

        h_file_path = gfc.get_save_game_file_path(game_name)

        with open(h_file_path, 'rb') as fp:
            h_data = fp.read()
        msg.add_attachment(h_data, maintype='application', subtype='octet-stream', filename=h_file_name)

        mail = smtplib.SMTP_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, FROM_PWD)

        mail.send_message(msg)

        mail.quit()

        if gfc.BACKUP_TURNS:
            att_path = os.path.join(gfc.get_or_create_save_game_path(game_name),
                                    "{}_{}".format(turn_number, h_file_name))

            fp = open(att_path, 'wb')
            fp.write(h_data)
            fp.close()

        messagebox.showinfo(title="Turn sent", message="Turn sent")
    except Exception as err:
        messagebox.showinfo(title="Error", message=str(err))


def upload_pretender(game_name, pretender_path):
    try:
        msg = EmailMessage()
        msg['Subject'] = filter_chars(game_name)
        msg['From'] = FROM_EMAIL
        msg['To'] = JOIN_EMAIL

        file_name = os.path.basename(pretender_path)

        with open(pretender_path, 'rb') as fp:
            p_data = fp.read()
        msg.add_attachment(p_data, maintype='application', subtype='octet-stream', filename=file_name)

        mail = smtplib.SMTP_SSL(SMTP_SERVER)
        mail.login(FROM_EMAIL, FROM_PWD)

        mail.send_message(msg)

        mail.quit()

        messagebox.showinfo(title="Pretender sent", message="Pretender sent")
    except Exception as err:
        messagebox.showinfo(title="Error", message=str(err))


def filter_chars(text):
    return text.strip("\t\n\r ")
