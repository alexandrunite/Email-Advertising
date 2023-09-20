import smtplib

from string import Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from random import randint
from time import sleep

sleep(randint(15-22))

MY_ADDRESS = 'oferte@arli.ro'
PASSWORD = 'decembrie2020'

def get_contacts(mycontacts):
    
    
    emails = []
    with open('mycontacts.txt', mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            emails.append(a_contact.split()[0])
    return emails

def read_template(message):
    
    with open('tempmess.docx', 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def main():
    emails = get_contacts('mycontacts.txt') # read contacts
    message_template = read_template('tempmess.docx')

    # set up the SMTP server
    s = smtplib.SMTP(host='mail.arli.ro', port=993)
    s.starttls()
    s.login(MY_ADDRESS, PASSWORD)

    # For each contact, send the email:
    for email in zip(emails):
        msg = MIMEMultipart()       # create a message

        # Prints out the message body for our sake
        print(message)

        # setup the parameters of the message
        msg['From']=MY_ADDRESS
        msg['To']=email
        msg['Subject']='ARLICO – SUPER OFERTĂ!'
        
        # add in the message body
        msg.attach(MIMEText(message, 'plain'))
        filename = 'oferta.pdf'
        
        # send the message via the server set up earlier.
        s.send_message(msg)
        del msg

        sleep(randint(15-22))
    # Terminate the SMTP session and close the connection
    s.quit()
    
if __name__ == '__main__':
    main()