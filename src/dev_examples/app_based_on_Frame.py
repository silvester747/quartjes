from Tkinter import *
import tkMessageBox

class app(Frame):
    def __init__(self,root=None):
        Frame.__init__(self,root)        
        self.frame = Entry(self)
        self.frame.bind("<KeyRelease>", self.key)
        self.frame.pack()
        self.frame.focus_set()
    
    def key(self,event):    
        self.frame.focus_force()
        print self.frame.get()

if __name__ == "__main__":
    root = Tk()
    a=app(root)
    b=app(root)
    c=app(root)
    d=app(root)

    a.pack()
    b.pack()
    c.pack()
    d.pack()

    root.mainloop()
