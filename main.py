
import sys
import os
from tkinter import Tk
from gui.app import EmailSenderApp

def main():
    root = Tk()
    app = EmailSenderApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == '__main__':
    main()
