from Tkinter import *
import tkMessageBox

class test(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.frame = Entry(self)
        self.frame.bind("<KeyRelease>", self.key)
        self.frame.pack()
        self.frame.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.ask_quit)

        self.mainloop()
    
    def key(self,event):    
        self.frame.focus_force()
        print self.frame.get()

    def ask_quit(self):
        if tkMessageBox.askokcancel("Quit", "You want to quit now? *sniff*"):
            self.destroy()

if __name__ == "__main__":
    t=test()

