import sqlite3
import os
import logging
from utils.helpers import log_exception, remove_duplicates

class DBManager:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_database()

    def setup_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                group_name TEXT DEFAULT 'General',
                subject TEXT DEFAULT 'ARLICO – SUPER OFERTĂ!',
                phone TEXT,
                birthdate TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY,
                group_name TEXT NOT NULL UNIQUE
            )
        ''')
        self.conn.commit()

    def add_contact(self, name, email, group='General', subject='ARLICO – SUPER OFERTĂ!', phone=None, birthdate=None):
        try:
            self.cursor.execute(
                "INSERT INTO contacts (name, email, group_name, subject, phone, birthdate) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, group, subject, phone, birthdate)
            )
            self.conn.commit()
            logging.info(f"Added contact: {name} <{email}>")
            return True
        except sqlite3.IntegrityError:
            logging.error(f"Duplicate email: {email}")
            return False

    def remove_contact(self, email):
        self.cursor.execute("DELETE FROM contacts WHERE email = ?", (email,))
        self.conn.commit()
        logging.info(f"Removed contact with email: {email}")

    def update_contact(self, email, name=None, group=None, subject=None, phone=None, birthdate=None):
        fields = {}
        if name:
            fields['name'] = name
        if group:
            fields['group_name'] = group
        if subject:
            fields['subject'] = subject
        if phone:
            fields['phone'] = phone
        if birthdate:
            fields['birthdate'] = birthdate
        if not fields:
            return False
        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [email]
        self.cursor.execute(f"UPDATE contacts SET {set_clause} WHERE email = ?", values)
        self.conn.commit()
        logging.info(f"Updated contact: {email}")
        return True

    def get_contacts(self, group=None, search=None):
        query = "SELECT name, email, group_name, subject, phone, birthdate FROM contacts"
        params = []
        conditions = []
        if group:
            conditions.append("group_name = ?")
            params.append(group)
        if search:
            conditions.append("(name LIKE ? OR email LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def import_contacts(self, contacts):
        contacts = remove_duplicates([tuple(contact) for contact in contacts])
        try:
            self.cursor.executemany(
                "INSERT INTO contacts (name, email, group_name, subject, phone, birthdate) VALUES (?, ?, ?, ?, ?, ?)",
                contacts
            )
            self.conn.commit()
            logging.info(f"Imported {len(contacts)} contacts.")
            return True
        except sqlite3.IntegrityError as e:
            logging.error(f"Import error: {e}")
            return False

    def add_group(self, group_name):
        try:
            self.cursor.execute("INSERT INTO groups (group_name) VALUES (?)", (group_name,))
            self.conn.commit()
            logging.info(f"Added group: {group_name}")
            return True
        except sqlite3.IntegrityError:
            logging.error(f"Duplicate group: {group_name}")
            return False

    def remove_group(self, group_name):
        self.cursor.execute("DELETE FROM groups WHERE group_name = ?", (group_name,))
        self.cursor.execute("UPDATE contacts SET group_name = 'General' WHERE group_name = ?", (group_name,))
        self.conn.commit()
        logging.info(f"Removed group: {group_name} and reassigned contacts to 'General'")

    def get_groups(self):
        self.cursor.execute("SELECT group_name FROM groups")
        groups = [row[0] for row in self.cursor.fetchall()]
        groups.insert(0, "General")
        return groups

    def search_contacts(self, keyword):
        keyword = f"%{keyword}%"
        self.cursor.execute(
            "SELECT name, email, group_name, subject, phone, birthdate FROM contacts WHERE name LIKE ? OR email LIKE ?",
            (keyword, keyword)
        )
        return self.cursor.fetchall()

    def export_contacts(self, file_path, group=None):
        contacts = self.get_contacts(group=group)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("Name,Email,Group,Subject,Phone,Birthdate\n")
                for contact in contacts:
                    f.write(",".join([str(field) if field else "" for field in contact]) + "\n")
            logging.info(f"Exported {len(contacts)} contacts to {file_path}")
            return True
        except Exception as e:
            logging.error(f"Export error: {e}")
            return False

    def get_contact_by_email(self, email):
        self.cursor.execute(
            "SELECT name, email, group_name, subject, phone, birthdate FROM contacts WHERE email = ?",
            (email,)
        )
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()
        logging.info("Database connection closed.")
