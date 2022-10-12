import smtplib
import json


mail_cred = json.load(open("./mail_cred.json", "r", encoding="utf-8"))

gmail_user = mail_cred["adress"]
gmail_password = mail_cred["app-password"]


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
    if match_perc > 90:
        mtch = "a perfect"
    elif match_perc > (100/3)*2:
        mtch = "an awesome"
    elif match_perc > 50:
        mtch = "a very good"
    else:
        mtch = "a"

    return f"Hello, {user_to.name}! You have {mtch} match with {users_pair.name} ({users_pair.email}), \
who speaks {join_langs(users_pair.lng_knows)}. They use these social networks: {users_pair.social_networks.strip()}.\n\
    Happy learning {langs} together!"


def send_msg(to, subject, msg):
    if isinstance(to, str):
        to = [to, ]

    sent_from = gmail_user
    body = msg

    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sent_from, ", ".join(to), subject, body)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print(f'Email sent to {", ".join(to)}')
    except:
        print(f'Something went wrong while sending email to {", ".join(to)}')
