# 📧 Email Advertising Application

Welcome to the **Email Advertising Application**! This Python-based application is designed to make sending promotional emails easy, customizable, and automated. With this tool, you can manage contacts, create templates, and schedule email campaigns for targeted groups — all from a user-friendly interface.

## 🚀 Features

- **Contact Management**: Add, edit, import, and export contacts, complete with group support.
- **Customizable Templates**: Design HTML email templates with placeholders for personalized content.
- **Scheduled Email Sending**: Schedule email campaigns in advance to optimize reach and engagement.
- **Spam Protection**: Throttle email sending to avoid triggering spam filters.
- **Settings Management**: Manage SMTP settings, business details, and more, directly within the app.
- **Encryption**: Secure email credentials with built-in encryption.

## 📂 Project Structure

Here's an overview of the project structure:


email_advertising/
├── main.py                   # Main entry point for the application
├── gui/
│   └── app.py                # Graphical User Interface module
├── email_sender/
│   └── sender.py             # Email sending functionality
├── database/
│   └── db_manager.py         # Database management for contacts
├── settings/
│   └── settings_manager.py   # Settings management and configuration
├── utils/
│   └── helpers.py            # Helper functions (encryption, validation, etc.)
├── templates/                # Folder for storing email templates
├── attachments/              # Folder for storing attachments
├── config.ini                # Configuration file
└── requirements.txt          # Project dependencies


## 📋 Prerequisites

To run this application, you’ll need:

- **Python 3.8+** (ensure Python is added to your system PATH)
- **Pip** for installing dependencies

## ⚙️ Setup Instructions

### 1. Clone the Repository


git clone https://github.com/yourusername/email-advertising.git
cd email-advertising


### 2. Install Dependencies

Install the required Python libraries with:


pip install -r requirements.txt


### 3. Configure Settings

Update the `config.ini` file with your SMTP credentials and other settings:

ini
[SMTP]
email_address = your_email@example.com
password = your_encrypted_password_here
smtp_server = smtp.example.com
smtp_port = 587

[DATABASE]
database_file = contacts.db

[PATHS]
templates_dir = templates
attachments_dir = attachments

[SPAM_PROTECTION]
throttle_min = 15
throttle_max = 22
unsubscribe_link = http://yourwebsite.com/unsubscribe

[GENERAL]
business_id = Your Business ID Here
log_file = email_sender.log


### 4. Encrypt Your SMTP Password

Use the `encrypt_password` function in `utils/helpers.py` to encrypt your SMTP password:

python
from utils.helpers import encrypt_password

plain_password = "your_password"
encrypted_password = encrypt_password(plain_password)
print(encrypted_password)


Replace `your_encrypted_password_here` in `config.ini` with the encrypted password output.

### 5. Run the Application

To start the application, run:


python main.py


## 🖥️ Application Overview

1. **Send Emails**: Select a template, target a contact group, and schedule your email campaign.
2. **Manage Contacts**: Add or import contacts, group them, and keep track of details like phone and birthdate.
3. **Templates**: Create HTML email templates with placeholders for personalized fields.
4. **Settings**: Adjust SMTP, paths, spam protection, and general settings directly from the app.

## 🛠️ Key Modules

- **`sender.py`**: Handles the process of sending emails, including adding attachments and managing placeholders in templates.
- **`db_manager.py`**: Manages contact storage, updates, imports, and exports within an SQLite database.
- **`settings_manager.py`**: Reads and writes app configuration, handles encryption for sensitive data, and validates settings.
- **`helpers.py`**: Provides helper functions for encryption, validation, logging, and string manipulation.

## 🔒 Security

- **Encryption**: Email credentials are encrypted using the `cryptography` library.
- **Spam Protection**: Throttling is built in to manage sending speed and prevent account flags.
- **Logs**: All activities and errors are logged in `email_sender.log` for easy troubleshooting.

## 📄 License

This project is licensed under the MIT License.

## 💡 Future Enhancements

- **Multi-Language Support**: Expand the application for a global user base.
- **Advanced Reporting**: Include analytics on open rates and engagement.
- **User Roles**: Add access control for multi-user environments.

## 📬 Contact

For questions or support, please reach out via [LinkedIn](https://www.linkedin.com/in/yourprofile/) or by opening an issue in this repository.

---

### 🌟 Enjoy a streamlined, efficient approach to email advertising!