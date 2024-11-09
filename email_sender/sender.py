# email_sender/sender.py

import smtplib
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate
from string import Template
from random import randint
from time import sleep
from utils.helpers import validate_email, read_template, sanitize_html, validate_url, format_phone_number, calculate_age, generate_unique_id, log_exception
from settings.settings_manager import SettingsManager
from database.db_manager import DBManager

class EmailSender:
    def __init__(self):
        self.settings = SettingsManager()
        self.db_manager = DBManager(self.settings.get('DATABASE', 'database_file'))
        self.my_address = self.settings.get('SMTP', 'email_address')
        self.password = self.settings.get('SMTP', 'password')
        self.smtp_server = self.settings.get('SMTP', 'smtp_server')
        self.smtp_port = int(self.settings.get('SMTP', 'smtp_port'))
        self.templates_dir = self.settings.get('PATHS', 'templates_dir')
        self.attachments_dir = self.settings.get('PATHS', 'attachments_dir')
        self.throttle_min = int(self.settings.get('SPAM_PROTECTION', 'throttle_min'))
        self.throttle_max = int(self.settings.get('SPAM_PROTECTION', 'throttle_max'))
        self.unsubscribe_link = self.settings.get('SPAM_PROTECTION', 'unsubscribe_link')
        self.business_id = self.settings.get('GENERAL', 'business_id')
    
    @log_exception
    def send_emails(self, contacts, template_name, status_callback=None, progress_callback=None):
        template_path = os.path.join(self.templates_dir, template_name)
        message_template = read_template(template_path)
        if not message_template:
            logging.error("Selected message template is empty or missing.")
            return False
        try:
            with smtplib.SMTP(host=self.smtp_server, port=self.smtp_port) as server:
                server.starttls()
                server.login(self.my_address, self.password)
                sent_count = 0
                total_contacts = len(contacts)
                for contact in contacts:
                    name, email, group, subject, phone, birthdate = contact
                    if not validate_email(email):
                        logging.warning(f"Invalid email skipped: {email}")
                        continue
                    msg = MIMEMultipart('alternative')
                    msg['From'] = self.my_address
                    msg['To'] = email
                    msg['Date'] = formatdate(localtime=True)
                    msg['Subject'] = subject
                    msg['X-Mailer'] = 'Python SMTP Email Sender'
                    msg['List-Unsubscribe'] = f'<{self.unsubscribe_link}>'
                    age = calculate_age(birthdate) if birthdate else 'N/A'
                    formatted_phone = format_phone_number(phone) if phone else 'N/A'
                    message = message_template.safe_substitute(
                        NAME=name,
                        UNSUBSCRIBE_LINK=self.unsubscribe_link,
                        BUSINESS_ID=self.business_id,
                        PHONE=formatted_phone,
                        AGE=age
                    )
                    sanitized_message = sanitize_html(message)
                    plain_message = Template(sanitized_message).safe_substitute().replace('<br>', '\n').replace('</p>', '').replace('<p>', '')
                    part1 = MIMEText(plain_message, 'plain')
                    part2 = MIMEText(sanitized_message, 'html')
                    msg.attach(part1)
                    msg.attach(part2)
                    if os.path.isdir(self.attachments_dir):
                        for filename in os.listdir(self.attachments_dir):
                            filepath = os.path.join(self.attachments_dir, filename)
                            with open(filepath, 'rb') as attachment:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(attachment.read())
                                encoders.encode_base64(part)
                                part.add_header('Content-Disposition', f'attachment; filename= {filename}')
                                msg.attach(part)
                    try:
                        server.send_message(msg)
                        logging.info(f"Email sent to {name} <{email}>.")
                        sent_count += 1
                        if status_callback:
                            status_callback(sent_count, total_contacts)
                        if progress_callback:
                            progress_callback(sent_count, total_contacts)
                    except Exception as e:
                        logging.error(f"Failed to send email to {email}: {e}")
                    sleep_time = randint(self.throttle_min, self.throttle_max)
                    sleep(sleep_time)
                logging.info("All emails have been sent.")
                return True
        except Exception as e:
            logging.error(f"SMTP connection failed: {e}")
            return False

    @log_exception
    def schedule_emails(self, contacts, template_name, schedule_time, status_callback=None, progress_callback=None):
        delay = (schedule_time - datetime.now()).total_seconds()
        if delay < 0:
            delay = 0
        threading.Thread(target=self.send_emails_thread, args=(contacts, template_name, delay, status_callback, progress_callback), daemon=True).start()
    
    def send_emails_thread(self, contacts, template_name, delay, status_callback, progress_callback):
        sleep(delay)
        self.send_emails(contacts, template_name, status_callback, progress_callback)
    
    def close(self):
        self.db_manager.close()
