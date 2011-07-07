# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 7, 2011 9:25:16 PM$"

from Tkinter import *
from quartjes.models.drink import *

class mix_dialog(Frame):
    '''
    this dialog is used for creating a mix from the suplyed drinks
    '''
    def __init__(self, root, mix):
        Frame.__init__(self, root)
        self.mix = mix
        self.create_widgets()
        self.pack()

    def add_to_mix(self):
        selection = self.lb_drinks.curselection()
        if len(selection) > 0:
            selected = int(selection[0])
            self.mix.insert_drink(self.master.drinks[selected])
            self.update_listboxes()

    def remove_from_mix(self):
        selection = self.lb_mix.curselection()
        if len(selection) > 0:
            selected = int(selection[0])
            self.mix.remove_drink(selected)
            self.update_listboxes()

    def update_listboxes(self):
        self.update_listbox(self.lb_drinks,self.master.drinks)
        self.update_listbox(self.lb_mix,self.mix.drinks)

    def update_listbox(self,lb,drinks):
        lb.delete(0,END)
        for d in drinks:
            lb.insert(END,d.name)

    def create_widgets(self):
        font16 = ("Arial", 16, "bold")        
        self.l_drinks = Label(self,text="Drinks",font = font16)
        self.l_drinks.grid(row = 0,column = 0,sticky=EW)
        self.lb_drinks = Listbox(self,font = font16)
        self.lb_drinks.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)

        self.f1 = Frame(self)
        self.b_add_to_mix = Button(self.f1, text = "->", width = 5, height = 2, font = font16,command = self.add_to_mix)
        self.b_add_to_mix.grid(row = 0,column=0,sticky=EW)

        self.b_remove_from_mix = Button(self.f1, text = "<-", width = 5, height = 2, font = font16,command = self.remove_from_mix)
        self.b_remove_from_mix.grid(row = 1,column=0,sticky=EW)
        self.f1.grid(row = 1,column=1,sticky=EW, padx = 10, pady = 20)

        self.l_mix = Label(self,text="Mix parts",font = font16)
        self.l_mix.grid(row = 0,column = 2,sticky=EW)
        self.lb_mix = Listbox(self,font = font16)
        self.lb_mix.grid(row = 1,column=2,sticky=EW, padx = 20, pady = 20)

        self.b_cancel = Button(self, text = "cancel", width = 20, height = 2, font = font16)
        self.b_cancel.grid(row = 2,column=0,sticky=EW, padx = 20, pady = 20)

        self.b_save = Button(self, text = "Save mix", width = 20, height = 2, font = font16)
        self.b_save.grid(row = 2,column=2,sticky=EW, padx = 20, pady = 20)
        self.update_listboxes()

if __name__ == "__main__":
    master = Tk()
    master.drinks = [Drink(),Drink(),Mix()]
    d = Mix()
    app = mix_dialog(master,d)
    app.mainloop()
