# gui/app.py

import os
import threading
import logging
import csv
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from email_sender.sender import EmailSender
from database.db_manager import DBManager
from settings.settings_manager import SettingsManager
from utils.helpers import validate_email, read_template, log_exception
from datetime import datetime
from string import Template

class EmailSenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Email Sender")
        self.settings = SettingsManager()
        self.setup_logging()
        self.db_manager = DBManager(self.settings.get('DATABASE', 'database_file'))
        self.create_widgets()
        self.email_sender = EmailSender()
    
    def setup_logging(self):
        log_file = self.settings.get('GENERAL', 'log_file')
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        logging.info("Application started.")
    
    def create_widgets(self):
        self.tabControl = ttk.Notebook(self.root)
        self.tab_send = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab_send, text='Send Emails')
        self.tab_contacts = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab_contacts, text='Contacts')
        self.tab_templates = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab_templates, text='Templates')
        self.tab_settings = ttk.Frame(self.tabControl)
        self.tabControl.add(self.tab_settings, text='Settings')
        self.tabControl.pack(expand=1, fill="both")
        self.create_send_email_tab()
        self.create_contacts_tab()
        self.create_templates_tab()
        self.create_settings_tab()
    
    def create_send_email_tab(self):
        frame = ttk.Frame(self.tab_send)
        frame.pack(padx=10, pady=10, fill=BOTH, expand=True)
        ttk.Label(frame, text="Select Template:").grid(column=0, row=0, sticky=W, pady=5)
        self.template_var = StringVar()
        self.template_combo = ttk.Combobox(frame, textvariable=self.template_var, state='readonly')
        self.template_combo.grid(column=1, row=0, padx=10, pady=5, sticky=E)
        self.load_templates()
        ttk.Label(frame, text="Group:").grid(column=0, row=1, sticky=W, pady=5)
        self.group_var = StringVar()
        self.group_combo = ttk.Combobox(frame, textvariable=self.group_var, state='readonly')
        self.group_combo['values'] = self.get_groups()
        self.group_combo.grid(column=1, row=1, padx=10, pady=5, sticky=E)
        ttk.Label(frame, text="Schedule (YYYY-MM-DD HH:MM):").grid(column=0, row=2, sticky=W, pady=5)
        self.schedule_var = StringVar()
        self.schedule_entry = ttk.Entry(frame, textvariable=self.schedule_var)
        self.schedule_entry.grid(column=1, row=2, padx=10, pady=5, sticky=E)
        self.send_button = ttk.Button(frame, text="Send Emails", command=self.send_emails)
        self.send_button.grid(column=0, row=3, columnspan=2, padx=10, pady=10)
        self.status_text = StringVar()
        self.status_label = ttk.Label(frame, textvariable=self.status_text)
        self.status_label.grid(column=0, row=4, columnspan=2, sticky=W)
        self.progress = ttk.Progressbar(frame, orient=HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(column=0, row=5, columnspan=2, padx=10, pady=5)
    
    def create_contacts_tab(self):
        frame = ttk.Frame(self.tab_contacts)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.contacts_tree = ttk.Treeview(frame, columns=('Name', 'Email', 'Group', 'Subject', 'Phone', 'Birthdate'), show='headings')
        self.contacts_tree.heading('Name', text='Name')
        self.contacts_tree.heading('Email', text='Email')
        self.contacts_tree.heading('Group', text='Group')
        self.contacts_tree.heading('Subject', text='Subject')
        self.contacts_tree.heading('Phone', text='Phone')
        self.contacts_tree.heading('Birthdate', text='Birthdate')
        self.contacts_tree.pack(fill=BOTH, expand=True)
        self.load_contacts()
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=X, pady=5)
        self.add_contact_button = ttk.Button(btn_frame, text="Add Contact", command=self.add_contact)
        self.add_contact_button.pack(side=LEFT, padx=5)
        self.remove_contact_button = ttk.Button(btn_frame, text="Remove Contact", command=self.remove_contact)
        self.remove_contact_button.pack(side=LEFT, padx=5)
        self.import_contacts_button = ttk.Button(btn_frame, text="Import Contacts", command=self.import_contacts)
        self.import_contacts_button.pack(side=LEFT, padx=5)
        self.export_contacts_button = ttk.Button(btn_frame, text="Export Contacts", command=self.export_contacts)
        self.export_contacts_button.pack(side=LEFT, padx=5)
    
    def create_templates_tab(self):
        frame = ttk.Frame(self.tab_templates)
        frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.templates_listbox = Listbox(frame)
        self.templates_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        self.load_template_list()
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(side=RIGHT, fill=Y, padx=5)
        self.add_template_button = ttk.Button(btn_frame, text="Add Template", command=self.add_template)
        self.add_template_button.pack(fill=X, pady=2)
        self.edit_template_button = ttk.Button(btn_frame, text="Edit Template", command=self.edit_template)
        self.edit_template_button.pack(fill=X, pady=2)
        self.remove_template_button = ttk.Button(btn_frame, text="Remove Template", command=self.remove_template)
        self.remove_template_button.pack(fill=X, pady=2)
    
    def create_settings_tab(self):
        frame = ttk.Frame(self.tab_settings)
        frame.pack(padx=10, pady=10, fill=BOTH, expand=True)
        smtp_frame = ttk.LabelFrame(frame, text="SMTP Settings")
        smtp_frame.pack(fill=X, padx=5, pady=5)
        ttk.Label(smtp_frame, text="Email Address:").grid(column=0, row=0, sticky=W, padx=5, pady=5)
        self.email_var = StringVar(value=self.settings.get('SMTP', 'email_address'))
        ttk.Entry(smtp_frame, textvariable=self.email_var, width=40).grid(column=1, row=0, padx=5, pady=5)
        ttk.Label(smtp_frame, text="Password:").grid(column=0, row=1, sticky=W, padx=5, pady=5)
        self.password_var = StringVar(value=self.settings.get('SMTP', 'password'))
        ttk.Entry(smtp_frame, textvariable=self.password_var, show="*", width=40).grid(column=1, row=1, padx=5, pady=5)
        ttk.Label(smtp_frame, text="SMTP Server:").grid(column=0, row=2, sticky=W, padx=5, pady=5)
        self.smtp_server_var = StringVar(value=self.settings.get('SMTP', 'smtp_server'))
        ttk.Entry(smtp_frame, textvariable=self.smtp_server_var, width=40).grid(column=1, row=2, padx=5, pady=5)
        ttk.Label(smtp_frame, text="SMTP Port:").grid(column=0, row=3, sticky=W, padx=5, pady=5)
        self.smtp_port_var = StringVar(value=self.settings.get('SMTP', 'smtp_port'))
        ttk.Entry(smtp_frame, textvariable=self.smtp_port_var, width=40).grid(column=1, row=3, padx=5, pady=5)
        ttk.Label(frame, text="Business ID:").pack(anchor=W, padx=5, pady=(10, 0))
        self.business_id_var = StringVar(value=self.settings.get('GENERAL', 'business_id'))
        ttk.Entry(frame, textvariable=self.business_id_var, width=40).pack(fill=X, padx=5, pady=5)
        self.save_settings_button = ttk.Button(frame, text="Save Settings", command=self.save_settings)
        self.save_settings_button.pack(pady=10)
        backup_frame = ttk.LabelFrame(frame, text="Configuration Management")
        backup_frame.pack(fill=X, padx=5, pady=5)
        self.backup_button = ttk.Button(backup_frame, text="Backup Config", command=self.backup_config)
        self.backup_button.pack(side=LEFT, padx=5, pady=5)
        self.restore_button = ttk.Button(backup_frame, text="Restore Config", command=self.restore_config)
        self.restore_button.pack(side=LEFT, padx=5, pady=5)
        self.reset_button = ttk.Button(backup_frame, text="Reset to Defaults", command=self.reset_settings)
        self.reset_button.pack(side=LEFT, padx=5, pady=5)
        self.export_settings_button = ttk.Button(backup_frame, text="Export Settings", command=self.export_settings)
        self.export_settings_button.pack(side=LEFT, padx=5, pady=5)
        self.import_settings_button = ttk.Button(backup_frame, text="Import Settings", command=self.import_settings)
        self.import_settings_button.pack(side=LEFT, padx=5, pady=5)
    
    def get_groups(self):
        return self.db_manager.get_groups()
    
    def load_contacts(self):
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)
        contacts = self.db_manager.get_contacts()
        for contact in contacts:
            self.contacts_tree.insert('', 'end', values=contact)
    
    def load_templates(self):
        templates_dir = self.settings.get('PATHS', 'templates_dir')
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        templates = [f for f in os.listdir(templates_dir) if os.path.isfile(os.path.join(templates_dir, f))]
        self.template_combo['values'] = templates
    
    def load_template_list(self):
        self.templates_listbox.delete(0, END)
        templates_dir = self.settings.get('PATHS', 'templates_dir')
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        templates = [f for f in os.listdir(templates_dir) if os.path.isfile(os.path.join(templates_dir, f))]
        for template in templates:
            self.templates_listbox.insert(END, template)
    
    def add_contact(self):
        def save_contact():
            name = name_var.get().strip()
            email = email_var.get().strip()
            group = group_var.get().strip() or 'General'
            subject = subject_var.get().strip() or 'ARLICO – SUPER OFERTĂ!'
            phone = phone_var.get().strip()
            birthdate = birthdate_var.get().strip()
            if not name or not email:
                messagebox.showerror("Missing Information", "Name and Email are required.")
                return
            if phone and not validate_phone_number(phone):
                messagebox.showerror("Invalid Phone", "Please enter a valid phone number.")
                return
            if birthdate:
                try:
                    datetime.strptime(birthdate, '%Y-%m-%d')
                except ValueError:
                    messagebox.showerror("Invalid Birthdate", "Please enter birthdate in YYYY-MM-DD format.")
                    return
            if not validate_email(email):
                messagebox.showerror("Invalid Email", "Please enter a valid email address.")
                return
            success = self.db_manager.add_contact(name, email, group, subject, phone if phone else None, birthdate if birthdate else None)
            if success:
                messagebox.showinfo("Contact Added", f"Contact {name} <{email}> added successfully.")
                self.load_contacts()
                self.group_combo['values'] = self.get_groups()
                add_window.destroy()
            else:
                messagebox.showerror("Duplicate Email", "This email address already exists.")
        add_window = Toplevel(self.root)
        add_window.title("Add Contact")
        ttk.Label(add_window, text="Name:").grid(column=0, row=0, padx=10, pady=5, sticky=W)
        name_var = StringVar()
        ttk.Entry(add_window, textvariable=name_var, width=30).grid(column=1, row=0, padx=10, pady=5)
        ttk.Label(add_window, text="Email:").grid(column=0, row=1, padx=10, pady=5, sticky=W)
        email_var = StringVar()
        ttk.Entry(add_window, textvariable=email_var, width=30).grid(column=1, row=1, padx=10, pady=5)
        ttk.Label(add_window, text="Group:").grid(column=0, row=2, padx=10, pady=5, sticky=W)
        group_var = StringVar()
        ttk.Entry(add_window, textvariable=group_var, width=30).grid(column=1, row=2, padx=10, pady=5)
        ttk.Label(add_window, text="Subject:").grid(column=0, row=3, padx=10, pady=5, sticky=W)
        subject_var = StringVar()
        ttk.Entry(add_window, textvariable=subject_var, width=30).grid(column=1, row=3, padx=10, pady=5)
        ttk.Label(add_window, text="Phone:").grid(column=0, row=4, padx=10, pady=5, sticky=W)
        phone_var = StringVar()
        ttk.Entry(add_window, textvariable=phone_var, width=30).grid(column=1, row=4, padx=10, pady=5)
        ttk.Label(add_window, text="Birthdate (YYYY-MM-DD):").grid(column=0, row=5, padx=10, pady=5, sticky=W)
        birthdate_var = StringVar()
        ttk.Entry(add_window, textvariable=birthdate_var, width=30).grid(column=1, row=5, padx=10, pady=5)
        ttk.Button(add_window, text="Save", command=save_contact).grid(column=0, row=6, columnspan=2, pady=10)
    
    def remove_contact(self):
        selected_item = self.contacts_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a contact to remove.")
            return
        contact = self.contacts_tree.item(selected_item, 'values')
        email = contact[1]
        confirm = messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove {contact[0]} <{email}>?")
        if confirm:
            self.db_manager.remove_contact(email)
            self.load_contacts()
            self.group_combo['values'] = self.get_groups()
            messagebox.showinfo("Contact Removed", f"Contact {contact[0]} <{email}> has been removed.")
    
    def import_contacts(self):
        filename = filedialog.askopenfilename(title="Select CSV File", filetypes=(("CSV Files", "*.csv"),))
        if not filename:
            return
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            contacts = []
            for row in reader:
                name = row.get('Name', '').strip()
                email = row.get('Email', '').strip()
                group = row.get('Group', 'General').strip()
                subject = row.get('Subject', 'ARLICO – SUPER OFERTĂ!').strip()
                phone = row.get('Phone', '').strip()
                birthdate = row.get('Birthdate', '').strip()
                if name and email and validate_email(email):
                    if phone and not validate_phone_number(phone):
                        logging.warning(f"Invalid phone for contact {email}. Skipping.")
                        continue
                    if birthdate:
                        try:
                            datetime.strptime(birthdate, '%Y-%m-%d')
                        except ValueError:
                            logging.warning(f"Invalid birthdate for contact {email}. Skipping.")
                            continue
                    contacts.append((name, email, group, subject, phone if phone else None, birthdate if birthdate else None))
                else:
                    logging.warning(f"Invalid contact skipped: {row}")
        if contacts:
            success = self.db_manager.import_contacts(contacts)
            if success:
                messagebox.showinfo("Contacts Imported", f"Imported {len(contacts)} contacts successfully.")
                self.load_contacts()
                self.group_combo['values'] = self.get_groups()
            else:
                messagebox.showerror("Import Failed", "Some contacts could not be imported due to errors.")
        else:
            messagebox.showwarning("No Valid Contacts", "No valid contacts found in the selected file.")
    
    def export_contacts(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filename:
            return
        group = self.group_var.get()
        success = self.db_manager.export_contacts(filename, group if group else None)
        if success:
            messagebox.showinfo("Export Successful", f"Contacts exported to {filename} successfully.")
        else:
            messagebox.showerror("Export Failed", "Failed to export contacts.")
    
    def add_template(self):
        def save_template():
            template_name = template_name_var.get().strip()
            content = template_text.get("1.0", END).strip()
            if not template_name or not content:
                messagebox.showerror("Missing Information", "Template name and content are required.")
                return
            template_path = os.path.join(self.settings.get('PATHS', 'templates_dir'), template_name)
            if os.path.exists(template_path):
                messagebox.showerror("Template Exists", "A template with this name already exists.")
                return
            with open(template_path, 'w', encoding='utf-8') as file:
                file.write(content)
            messagebox.showinfo("Template Saved", f"Template '{template_name}' has been saved.")
            self.load_templates()
            self.load_template_list()
            add_window.destroy()
        add_window = Toplevel(self.root)
        add_window.title("Add Template")
        ttk.Label(add_window, text="Template Name:").grid(column=0, row=0, padx=10, pady=5, sticky=W)
        template_name_var = StringVar()
        ttk.Entry(add_window, textvariable=template_name_var, width=40).grid(column=1, row=0, padx=10, pady=5)
        ttk.Label(add_window, text="Content:").grid(column=0, row=1, padx=10, pady=5, sticky=NW)
        template_text = Text(add_window, width=60, height=20)
        template_text.grid(column=1, row=1, padx=10, pady=5)
        ttk.Button(add_window, text="Save Template", command=save_template).grid(column=0, row=2, columnspan=2, pady=10)
    
    def edit_template(self):
        selected = self.templates_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a template to edit.")
            return
        template_name = self.templates_listbox.get(selected[0])
        template_path = os.path.join(self.settings.get('PATHS', 'templates_dir'), template_name)
        def save_edited_template():
            content = template_text.get("1.0", END).strip()
            if not content:
                messagebox.showerror("Missing Content", "Template content cannot be empty.")
                return
            with open(template_path, 'w', encoding='utf-8') as file:
                file.write(content)
            messagebox.showinfo("Template Updated", f"Template '{template_name}' has been updated.")
            self.load_templates()
            self.load_template_list()
            edit_window.destroy()
        edit_window = Toplevel(self.root)
        edit_window.title(f"Edit Template: {template_name}")
        ttk.Label(edit_window, text="Content:").pack(anchor=NW, padx=10, pady=5)
        template_text = Text(edit_window, width=60, height=20)
        template_text.pack(padx=10, pady=5)
        with open(template_path, 'r', encoding='utf-8') as file:
            content = file.read()
            template_text.insert(END, content)
        ttk.Button(edit_window, text="Save Changes", command=save_edited_template).pack(pady=10)
    
    def remove_template(self):
        selected = self.templates_listbox.curselection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a template to remove.")
            return
        template_name = self.templates_listbox.get(selected[0])
        confirm = messagebox.askyesno("Confirm Remove", f"Are you sure you want to remove the template '{template_name}'?")
        if confirm:
            template_path = os.path.join(self.settings.get('PATHS', 'templates_dir'), template_name)
            try:
                os.remove(template_path)
                messagebox.showinfo("Template Removed", f"Template '{template_name}' has been removed.")
                self.load_templates()
                self.load_template_list()
            except Exception as e:
                logging.error(f"Failed to remove template '{template_name}': {e}")
                messagebox.showerror("Error", f"Failed to remove template: {e}")
    
    def save_settings(self):
        self.settings.set('SMTP', 'email_address', self.email_var.get().strip())
        self.settings.set('SMTP', 'password', self.password_var.get().strip())
        self.settings.set('SMTP', 'smtp_server', self.smtp_server_var.get().strip())
        self.settings.set('SMTP', 'smtp_port', self.smtp_port_var.get().strip())
        self.settings.set('GENERAL', 'business_id', self.business_id_var.get().strip())
        self.settings.save_config()
        messagebox.showinfo("Settings Saved", "SMTP settings have been updated.")
        self.email_sender = EmailSender()
    
    def backup_config(self):
        backup_path = filedialog.asksaveasfilename(defaultextension=".ini", filetypes=[("INI Files", "*.ini")], title="Backup Config")
        if backup_path:
            self.settings.backup_config()
            try:
                shutil.copyfile(self.settings.config_file, backup_path)
                messagebox.showinfo("Backup Successful", f"Configuration backed up to {backup_path}.")
            except Exception as e:
                logging.error(f"Backup failed: {e}")
                messagebox.showerror("Backup Failed", f"Failed to backup configuration: {e}")
    
    def restore_config(self):
        restore_path = filedialog.askopenfilename(title="Restore Config", filetypes=[("INI Files", "*.ini")])
        if restore_path:
            self.settings.restore_config()
            self.load_templates()
            self.load_contacts()
            self.load_template_list()
            self.group_combo['values'] = self.get_groups()
            messagebox.showinfo("Restore Successful", f"Configuration restored from {restore_path}.")
    
    def reset_settings(self):
        confirm = messagebox.askyesno("Confirm Reset", "Are you sure you want to reset settings to default?")
        if confirm:
            self.settings.reset_to_defaults()
            self.load_templates()
            self.load_contacts()
            self.load_template_list()
            self.group_combo['values'] = self.get_groups()
            messagebox.showinfo("Reset Successful", "Settings have been reset to default.")
    
    def export_settings(self):
        export_path = filedialog.asksaveasfilename(defaultextension=".ini", filetypes=[("INI Files", "*.ini")], title="Export Settings")
        if export_path:
            success = self.settings.export_settings(export_path)
            if success:
                messagebox.showinfo("Export Successful", f"Settings exported to {export_path}.")
            else:
                messagebox.showerror("Export Failed", "Failed to export settings.")
    
    def import_settings(self):
        import_path = filedialog.askopenfilename(title="Import Settings", filetypes=[("INI Files", "*.ini")])
        if import_path:
            self.settings.import_settings(import_path)
            self.load_templates()
            self.load_contacts()
            self.load_template_list()
            self.group_combo['values'] = self.get_groups()
            messagebox.showinfo("Import Successful", f"Settings imported from {import_path}.")
    
    def send_emails(self):
        template_name = self.template_var.get()
        group = self.group_var.get()
        schedule_str = self.schedule_var.get().strip()
        if not template_name:
            messagebox.showerror("No Template Selected", "Please select an email template.")
            return
        contacts = self.db_manager.get_contacts(group if group else None)
        if not contacts:
            messagebox.showwarning("No Contacts", "No contacts available for the selected group.")
            return
        if schedule_str:
            try:
                schedule_time = datetime.strptime(schedule_str, '%Y-%m-%d %H:%M')
                delay = (schedule_time - datetime.now()).total_seconds()
                if delay < 0:
                    delay = 0
            except ValueError:
                messagebox.showerror("Invalid Schedule", "Please enter the date and time in the format YYYY-MM-DD HH:MM.")
                return
        else:
            delay = 0
        threading.Thread(target=self.send_email_thread, args=(contacts, template_name, delay), daemon=True).start()
    
    def send_email_thread(self, contacts, template_name, delay):
        if delay > 0:
            self.status_text.set(f"Emails scheduled to send in {int(delay)} seconds.")
            sleep(delay)
        self.status_text.set("Sending emails...")
        def update_status(sent, total):
            self.status_text.set(f"Sent {sent}/{total} emails.")
            progress = (sent / total) * 100
            self.progress['value'] = progress
            self.root.update_idletasks()
        success = self.email_sender.send_emails(contacts, template_name, status_callback=update_status)
        if success:
            messagebox.showinfo("Emails Sent", "All emails have been sent successfully.")
            self.status_text.set("All emails have been sent.")
            self.progress['value'] = 100
        else:
            messagebox.showerror("Sending Failed", "An error occurred while sending emails.")
            self.status_text.set("Sending failed.")
    
    def on_closing(self):
        self.db_manager.close()
        logging.info("Application closed.")
        self.root.destroy()
