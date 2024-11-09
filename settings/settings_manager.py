import configparser
import os
import logging
import shutil
from cryptography.fernet import Fernet
from utils.helpers import encrypt_password, decrypt_password, log_exception
import re

DEFAULT_CONFIG = {
    'SMTP': {
        'email_address': 'your_email@example.com',
        'password': '',  
        'smtp_server': 'smtp.example.com',
        'smtp_port': '587'
    },
    'DATABASE': {
        'database_file': 'contacts.db'
    },
    'PATHS': {
        'templates_dir': 'templates',
        'attachments_dir': 'attachments'
    },
    'SPAM_PROTECTION': {
        'throttle_min': '15',
        'throttle_max': '22',
        'unsubscribe_link': 'http://yourwebsite.com/unsubscribe'
    },
    'GENERAL': {
        'business_id': 'Your Business ID Here',
        'log_file': 'email_sender.log'
    }
}

KEY_FILE = 'utils/secret.key'

class SettingsManager:
    def __init__(self, config_file='config.ini', backup_file='config_backup.ini'):
        self.config_file = config_file
        self.backup_file = backup_file
        self.config = configparser.ConfigParser()
        self.fernet = self.initialize_fernet()
        if not os.path.exists(self.config_file):
            self.create_default_config()
        self.load_config()
        self.validate_settings()

    def initialize_fernet(self):
        if not os.path.exists(KEY_FILE):
            key = Fernet.generate_key()
            with open(KEY_FILE, 'wb') as key_file:
                key_file.write(key)
        else:
            with open(KEY_FILE, 'rb') as key_file:
                key = key_file.read()
        return Fernet(key)

    def create_default_config(self):
        for section, settings in DEFAULT_CONFIG.items():
            self.config[section] = settings
        self.config['SMTP']['password'] = encrypt_password(DEFAULT_CONFIG['SMTP']['password'])
        self.save_config()

    def load_config(self):
        self.config.read(self.config_file)
        for section in self.config.sections():
            if 'password' in self.config[section]:
                encrypted = self.config[section]['password']
                decrypted = decrypt_password(encrypted)
                self.config[section]['password'] = decrypted if decrypted else ''

    def save_config(self):
        for section in self.config.sections():
            if 'password' in self.config[section]:
                plain = self.config[section]['password']
                encrypted = encrypt_password(plain)
                self.config[section]['password'] = encrypted
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        for section in self.config.sections():
            if 'password' in self.config[section]:
                encrypted = self.config[section]['password']
                decrypted = decrypt_password(encrypted)
                self.config[section]['password'] = decrypted if decrypted else ''

    @log_exception
    def backup_config(self):
        shutil.copyfile(self.config_file, self.backup_file)
        logging.info(f"Configuration backed up to {self.backup_file}.")

    @log_exception
    def restore_config(self):
        if os.path.exists(self.backup_file):
            shutil.copyfile(self.backup_file, self.config_file)
            self.load_config()
            logging.info(f"Configuration restored from {self.backup_file}.")
        else:
            logging.error("Backup file does not exist.")

    @log_exception
    def reset_to_defaults(self):
        self.config = configparser.ConfigParser()
        for section, settings in DEFAULT_CONFIG.items():
            self.config[section] = settings
        self.config['SMTP']['password'] = encrypt_password(DEFAULT_CONFIG['SMTP']['password'])
        self.save_config()
        self.load_config()
        logging.info("Configuration reset to default settings.")

    def get(self, section, option, default=None):
        env_var = f"{section.upper()}_{option.upper()}"
        if os.getenv(env_var):
            return os.getenv(env_var)
        return self.config.get(section, option, fallback=default)

    def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        if option == 'password':
            value = decrypt_password(encrypt_password(value))
        self.config.set(section, option, value)

    def validate_settings(self):
        email = self.get('SMTP', 'email_address')
        password = self.get('SMTP', 'password')
        smtp_server = self.get('SMTP', 'smtp_server')
        smtp_port = self.get('SMTP', 'smtp_port')
        unsubscribe_link = self.get('SPAM_PROTECTION', 'unsubscribe_link')
        if not re.match(r'^[A-Za-z0-9\._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            logging.error("Invalid SMTP email address.")
        if not smtp_server:
            logging.error("SMTP server is not set.")
        if not smtp_port.isdigit():
            logging.error("SMTP port must be a number.")
        if not re.match(r'^https?://', unsubscribe_link):
            logging.error("Invalid unsubscribe link URL.")

    @log_exception
    def export_settings(self, export_path):
        self.backup_config()
        shutil.copyfile(self.config_file, export_path)
        logging.info(f"Configuration exported to {export_path}.")

    @log_exception
    def import_settings(self, import_path):
        if os.path.exists(import_path):
            shutil.copyfile(import_path, self.config_file)
            self.load_config()
            self.validate_settings()
            logging.info(f"Configuration imported from {import_path}.")
        else:
            logging.error(f"Import file {import_path} does not exist.")
