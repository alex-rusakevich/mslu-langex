import smtplib
import json
import traceback
from email.message import EmailMessage
from langex.utils import ensure

MAX_EMAILS_PER_USER = 2
email_number_per_adress = {}

def inc_email_num(user_email: str):
    if user_email in email_number_per_adress.keys():
        email_number_per_adress[user_email] += 1
    else:
        email_number_per_adress[user_email] = 1

def can_send_more_emails_to(user_email: str, max_emails_per_user = 2):
    if max_emails_per_user <= 0:
        return False

    if user_email in email_number_per_adress.keys():
        if email_number_per_adress[user_email] >= max_emails_per_user:
            return False
    
    return True

mail_cred = {}

try:
    mail_cred = json.load(open("./mail_cred.json", "r", encoding="utf-8"))
except FileNotFoundError:
    with open("./mail_cred.json", "w", encoding="utf-8") as file:
        file.writelines("""{
    "adress": "",
    "app-password": ""
}""")
        file.close()
    raise FileNotFoundError

gmail_user = ensure(mail_cred["adress"])
gmail_password = ensure(mail_cred["app-password"])

server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.ehlo()
server.login(gmail_user, gmail_password)


def msg_gen(user_to, users_pair, match_perc):
    def join_langs(lang_list):
        if isinstance(lang_list, str):
            return lang_list

        lgs = []
        for l in lang_list:
            lgs.append(l.title())

        if len(lgs) == 0:
            return ""
        elif len(lgs) == 1:
            return lgs[0]
        else:
            return ", ".join(lgs[:-1]) + " and " + lgs[-1]

    langs = []

    for lang in users_pair.lng_knows:
        if lang in user_to.lng_want_to_know:
            langs.append(lang)

    for lang in user_to.lng_knows:
        if lang in users_pair.lng_want_to_know:
            langs.append(lang)

    langs = join_langs(list(set(langs)))

    mtch = ""
    match_perc = int(match_perc)
    if match_perc >= 90:
        mtch = "a perfect"
    elif match_perc >= 75:
        mtch = "a very good"
    elif match_perc >= 50:
        mtch = "a"

    return f"Hello, {user_to.name}! You have {mtch} match with {users_pair.name} ({users_pair.email}), \
who speaks {join_langs(users_pair.lng_knows)}. They use these social networks: {users_pair.social_networks.strip()}.\
\nHappy learning {langs} together!"


def close_msg_connection():
    server.close()


def send_msg(to, subject, msg_txt):
    if not can_send_more_emails_to(", ".join(to)):
        print(f"Can't send more emails to {to}")
        return False

    global server

    if isinstance(to, str):
        to = [to, ]

    msg = EmailMessage()
    msg.set_content(str(msg_txt))

    msg['Subject'] = str(subject)
    msg['From'] = str(gmail_user)
    msg['To'] = str(", ".join(to))

    try:
        server.send_message(msg)

        print(f'Email sent to {", ".join(to)}')
        inc_email_num(", ".join(to))

        return True
    except Exception as exception:
        print(
            f'Something went wrong while sending email to {", ".join(to)}: {traceback.format_exc()}')
        return False
