import re
import os
import logging
from string import Template
from datetime import datetime
import json
import hashlib
import base64
import random
import string
from functools import wraps
from cryptography.fernet import Fernet
from urllib.parse import urlparse

KEY_FILE = 'utils/secret.key'

def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as key_file:
            key_file.write(key)
    else:
        with open(KEY_FILE, 'rb') as key_file:
            key = key_file.read()
    return key

def get_fernet():
    key = load_key()
    return Fernet(key)

def validate_email(email):
    pattern = r'^[A-Za-z0-9\._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None

def read_template(filename):
    if not os.path.exists(filename):
        logging.error(f"Template file {filename} does not exist.")
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as template_file:
            template_file_content = template_file.read()
        return Template(template_file_content)
    except Exception as e:
        logging.error(f"Error reading template {filename}: {e}")
        return None

def validate_phone_number(phone):
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone) is not None

def parse_datetime(date_str, format_str='%Y-%m-%d %H:%M'):
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError:
        logging.error(f"Date string '{date_str}' does not match format '{format_str}'.")
        return None

def get_current_timestamp(format_str='%Y-%m-%d %H:%M:%S'):
    return datetime.now().strftime(format_str)

def format_datetime(dt_obj, format_str='%Y-%m-%d %H:%M:%S'):
    return dt_obj.strftime(format_str)

def generate_random_string(length=10):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def sanitize_html(html_content):
    clean = re.sub(r'<script.*?>.*?</script>', '', html_content, flags=re.DOTALL)
    clean = re.sub(r'<.*?on\w+=".*?".*?>', '', clean)
    clean = re.sub(r'<!--.*?-->', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<[^>]+>', '', clean)
    return clean

def load_json(file_path):
    if not os.path.exists(file_path):
        logging.error(f"JSON file {file_path} does not exist.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {file_path}: {e}")
        return None
    except Exception as e:
        logging.error(f"Error loading JSON file {file_path}: {e}")
        return None

def save_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)
        logging.info(f"Data successfully saved to {file_path}.")
        return True
    except Exception as e:
        logging.error(f"Error saving JSON to {file_path}: {e}")
        return False

def encrypt_password(password):
    f = get_fernet()
    encrypted = f.encrypt(password.encode())
    return encrypted.decode()

def decrypt_password(encrypted_password):
    f = get_fernet()
    try:
        decrypted = f.decrypt(encrypted_password.encode())
        return decrypted.decode()
    except Exception as e:
        logging.error(f"Error decrypting password: {e}")
        return None

def hash_string(input_str, algorithm='sha256'):
    hash_func = hashlib.new(algorithm)
    hash_func.update(input_str.encode())
    return hash_func.hexdigest()

def create_directories(path_list):
    for path in path_list:
        try:
            os.makedirs(path, exist_ok=True)
            logging.info(f"Directory '{path}' is ready.")
        except Exception as e:
            logging.error(f"Error creating directory '{path}': {e}")

def log_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception(f"Exception in {func.__name__}: {e}")
            raise
    return wrapper

def validate_url(url):
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])

def generate_unique_id(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def remove_duplicates(items):
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique

def format_phone_number(phone):
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 10:
        return f"+1{digits}"
    return f"+{digits}"

def extract_placeholders(template_str):
    return re.findall(r'\$\{(\w+)\}', template_str)

def safe_get(d, key, default=None):
    return d.get(key, default)

def calculate_age(birthdate_str, format_str='%Y-%m-%d'):
    birthdate = parse_datetime(birthdate_str, format_str)
    if birthdate:
        today = datetime.today()
        return today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    return None

def generate_password(length=12, include_special=True):
    characters = string.ascii_letters + string.digits
    if include_special:
        characters += string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))
