import smtplib
import json

mail_cred = json.load(open("./mail_cred.json", "r", encoding="utf-8"))

gmail_user = mail_cred["adress"]
gmail_password = mail_cred["app-password"]

sent_from = gmail_user
to = ["mr.alexander.rusakevich@gmail.com"]
subject = 'It works!'
body = "Hello, World"

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

    print('Email sent!')
except:
    print('Something went wrong...')
