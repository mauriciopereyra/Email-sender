from django.conf import settings
import sys, os, django, time
from website.models import Contact, Email_sent, Template
import requests
import json
import time
import csv
import schedule
from random import randint
import codecs
from emailverify import EmailListVerifyOne
from configparser import ConfigParser

sys.path.append('..')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_django_project.settings")
django.setup()
dir_path = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser()
config.read('config.ini')
domain = config['mailgun']['domain']
domain2 = config['mailgun']['domain2']
api = config['mailgun']['api']

def send_email(to, subject, text):
    return requests.post(
        domain,
        auth=("api", api),
        data={"from": config['email']['from'],
            "to": [to],
            "subject": subject,
            "html": text,
            # "text": text,
            }).content



def get_status_last_email():

    return json.loads(requests.get(
        domain2,
        auth=("api", api),
        params={
                "ascending"   : "no",
                "limit"       :  1,
                "pretty"      : "yes"}).content)['items'][0]['event']



def send_email_and_check_status(to, subject, text):
    print(send_email(to, subject, text))
    time.sleep(60)
    return get_status_last_email()



def send_daily_emails(number,sleep_minutes):
    global emails_to_send
    emails_to_send *= 1.08
    number = int(emails_to_send)
    if number > 100:
        number = 100
    print("Will send",number,"emails")
    standby_time = randint(0,5*60) # Waiting 0-5 minutes before start sending emails
    print("Waiting",int(standby_time/60),"minutes before starting")

    django.db.close_old_connections() # To avoid errors with MySQL connection

    contacts = list(Contact.objects.filter(status='active'))#.filter(verified="ok"))
    contacts.sort(key=lambda x:Email_sent.objects.filter(to=x).count())
    contacts = contacts[:number]
    sent = 0 # Keep track of sent emails

    for index, contact in enumerate(contacts):
        django.db.close_old_connections() # To avoid errors with MySQL connection
        print('Checking {}'.format(contact.email))
        E = EmailListVerifyOne(config['mailgun']['key'], contact.email)
        result = E.control()
        contact.verified = result
        contact.save()

        if not contact.verified == 'ok':
            print(contact.email,"failed verification")
            contact.status = 'failed'
            contact.save()
            continue
        else:
            sent += 1
        
        print('Sending email to {}'.format(contact.email))

        this_email = Email_sent.objects.create(fr=config['mailgun']['fr'],to=contact,subject=Template.objects.all()[0].subject,content=Template.objects.all()[0].content.replace(r'{{email}}',contact.email),status='pending')

        this_email.status = send_email_and_check_status(this_email.to, this_email.subject, this_email.content)

        print('Email status is {}'.format(this_email.status))

        if this_email.status == 'failed':
            contact.status = 'failed'
            contact.save()

        this_email.save()

        print('{}/{}/{}'.format(sent,index+1,number))

        if sleep_minutes == 'auto':
            ### If auto, distribute all emails in 8 hs (Or more hours, if many emails)
            waiting = int(60*60*8/number)
        else:
            waiting = 60*sleep_minutes
        
        # Modify intervals randomly, decreasing or increasing up to 3.5 minutes
        waiting = abs(waiting+randint(-210,210)-60)
        # Waiting time must be at least 7 minutes
        if waiting/60 < 7: waiting += 60*6
        print("Waiting",int((waiting+60)/60),"minutes")
        time.sleep(waiting)



def import_emails_db():

    with open(r'static/others/emails_fb.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader, None)
        for row in csv_reader:
            print(row[0])
            verified_cell = ''
            if len(row) >= 8:
                verified_cell = row[7]
            try: row[0].encode('latin1')
            except:
                print('Error with string')
                continue

            obj, created = Contact.objects.get_or_create(
                email=row[0],
                source = 'source',
                # defaults={'verified': verified_cell}, # I was using this when VerifyEmails API was not implemented yet.
            )

            if not created:
                print('Email is already in the database')


def start(number,sleep_minutes,start_time=None):

    if start_time:
        print('Running daily at',start_time)
        while True:
            schedule.every().day.at(start_time).do(send_daily_emails,number,sleep_minutes)

            print('Standby')

            while True:
                schedule.run_pending()

    else:
        send_daily_emails(number,sleep_minutes)




def remove_all_contacts():
    contacts = Contact.objects.all().delete()



def send_test_email(email, html):
    print(send_email(email, "Subject", html.replace(r'{{email}}',email)))




############### Getting arguments from shell

if len(sys.argv) > 1:
    if sys.argv[1] == 'remove_contacts':
        remove_all_contacts()

    elif sys.argv[1] == 'import_db':
        import_emails_db()

    elif sys.argv[1] == 'send_test':
        f = codecs.open("templates/email_template.html", 'r')
        html = f.read()
        send_test_email(sys.argv[2],html)

    elif sys.argv[1] == 'start':
        emails_to_send = int(sys.argv[2])

        if len(sys.argv) < 5:
            print('''
                Starting now
                Sending {} emails
                Waiting {} minutes between emails'''.format(sys.argv[2],sys.argv[3]))
            start(number=sys.argv[2],sleep_minutes=sys.argv[3])
        else:
            print('''
                Starting at {}
                Sending {} emails
                Waiting {} minutes between emails'''.format(sys.argv[4],sys.argv[2],sys.argv[3]))
            start(number=sys.argv[2],sleep_minutes=sys.argv[3],start_time=sys.argv[4])

    elif sys.argv[1] == 'verified':
        contacts = list(Contact.objects.filter(status='active').filter(verified="ok"))
        print(len(contacts),"active and verified contacts")

else:
    print('''Please specify an option:
        remove_contacts
        import_db
        send_test address
        start number sleep_minutes|auto [hh:mm]
        verified''')


###############


