# -*- coding:utf-8 -*-
import smtplib
import threading
from email.mime.text import MIMEText

import time

import logging

from datetime import datetime

from sqlalchemy import text

from database.storage import get_session
from env import is_pi
from users.users import Users

# lower and we send mails every x days!
minimum_balance = -5
remind_mail_every_x_hours = 24 * 7

with open('mail_pw', 'r') as pw:
    mail_pw = pw.read().replace('\n', '')

def send_notification_newthread(to_address, subject, message):
    send_thread = threading.Thread(
        target=send_notification,
        args=(to_address, subject, message)
    )
    send_thread.daemon = True
    send_thread.start()

def send_notification(to_address, subject, message):
    msg = MIMEText(message,_charset='utf-8')

    fromMail = "flipdot-noti@vega.uberspace.de"

    msg['Subject'] = subject
    msg['From'] = fromMail
    msg['To'] = to_address

    s = smtplib.SMTP()
    s.connect(host='vega.uberspace.de', port=587)
    s.ehlo()
    s.starttls()
    s.login(user=fromMail, password=mail_pw)
    s.sendmail(fromMail, [to_address], msg.as_string())
    s.quit()

def send_drink(user, drink, balance):
    try:
        user_email = user['email']

        if user_email and user['meta']['drink_notification'] == 'instant':
            mail_msg = "Du hast das folgende Getränk getrunken {drink_name}" \
                       "\n\nVerbleibendes Guthaben: EUR {balance}\n\n" \
                       "Maileinstellungen: http://ldapapp.fd/" \
                .format(drink_name=drink['name'], balance=balance)
            send_notification_newthread(user_email,
                                        "[fd-noti] Getränk getrunken", mail_msg)
    except Exception as e:
        logging.error(e)
        pass

def send_lowbalances():
    if not is_pi():
        return
    for user in Users.get_all():
        try:
            user_email = user['email']
            if not user_email:
                continue
            send_lowbalance(user, user_email)
        except Exception as e:
            logging.error(e)
            continue

def send_lowbalance(user, email):
    now = time.time()

    balance = Users.get_balance(user['id'])
    if balance >= minimum_balance:
        # set time to okay
        user["last_emailed"] = time.time()
        Users.save(user)
        return
    diff = now - user['last_emailed']
    last_emailed_hours = diff / 60 / 60
    last_emailed_days = last_emailed_hours / 24
    if last_emailed_hours > remind_mail_every_x_hours:
        print user['name'], "balance last emailed", last_emailed_days, "days (", \
            last_emailed_hours, "hours) ago. Mailing now."
        mail_msg = "Du hast seit mehr als {limit_days} Stunden ein " \
                   "Guthaben unter EUR {limit}!\n\n" \
                   "Dein Guthaben betraegt: EUR {balance}\n\n" \
                   "Zum aufladen geh (im Space-Netz) auf http://drinks-touch.fd/" \
                   "\n\nMaileinstellungen: http://ldapapp.fd/" \
            .format(limit_days=remind_mail_every_x_hours / 24,
                    limit=minimum_balance, balance=balance)
        send_notification(email, "[fd-noti] Negatives Guthaben",
                          mail_msg)
        user["last_emailed"] = time.time()
        Users.save(user)

def send_summaries():
    session = get_session()
    if not is_pi():
        #u = Users.get_all('cfstras')[0]
        #send_summary(session, u, u['email'])
        return
    for user in Users.get_all():
        try:
            user_email = user['email']
            if not user_email:
                continue
            send_summary(session, user, user_email)
        except Exception as e:
            logging.error(e)
            continue

frequencies = {
    "daily": 60 * 60 * 24,
    "weekly": 60 * 60 * 24 * 7,
}

def send_summary(session, user, email):
    now = time.time()
    frequency_str = user['meta']['drink_notification']
    if frequency_str not in frequencies.keys():
        return
    freq_secs = frequencies[frequency_str]
    last_emailed = user['meta']['last_drink_notification']
    last_emailed_str = datetime.fromtimestamp(last_emailed).isoformat()
    diff = now - last_emailed
    last_emailed_hours = diff / 60 / 60
    last_emailed_days = last_emailed_hours / 24
    if diff > freq_secs:
        print user['name'], "summary last emailed", last_emailed_days, "days (", \
            last_emailed_hours, "hours) ago. Mailing now."
        mail_msg = "Hier ist deine Getränkeübersicht seit {since}:\n" \
                   "Dein aktuelles Guthaben beträgt EUR {balance}.\n" \
            .format(since=last_emailed_str, balance=Users.get_balance(user['id']))
        sql = text("""
SELECT
    se.barcode,
    se.timestamp,
    d.name,
    d.size
FROM scanevent se
    LEFT OUTER JOIN drink d ON d.ean = se.barcode
WHERE user_id = :userid
    AND se.timestamp > NOW() - INTERVAL '%d seconds'
ORDER BY se.timestamp
        """ % (freq_secs))
        rows = session.connection().execute(sql, userid=user['id']).fetchall()
        if len(rows) == 0:
            print "got no rows. skipping."
            return
        mail_msg += "    #      datum                     drink  groesse\n"
        for i, event in enumerate(rows):
            date = event['timestamp'].strftime("%F %T Z")
            name = event['name']
            size = event['size']
            mail_msg += "  % 3d % 20s % 15s % 5s l\n" % (
                i, date, str(name), str(size) if size else "?"
            )
        mail_msg += "\nBesuchen Sie uns bald wieder!\n\n" \
                    "Maileinstellungen: http://ldapapp.fd/"
        print "got %d rows. mailing." % (len(rows))
        send_notification(email, "[fd-noti] Getränkeübersicht für %s" % user['name'],
                          mail_msg)
        user['meta']["last_drink_notification"] = time.time()
        Users.save(user)
