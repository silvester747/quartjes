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
        root.title('Mix dialog')
        Frame.__init__(self, root)
        self.mix = mix
        self.orig_mix_drinks_list = self.mix.drinks[:]
        self.drinks = []

        self.create_widgets()
        self.reset_values()
        self.pack()

    def reset_values(self):
        for drink in self.master.drinks:
            if drink.__class__.__name__ == "Drink":
                self.drinks.append(drink)
        self.e_mixname.delete(0,END)
        self.e_mixname.insert(END,self.mix.name)

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

    def cancel(self):
        self.mix.drinks = self.orig_mix_drinks_list
        print self.mix
        self.mix.update_properties()
        self.master.destroy()

    def save(self):
        self.mix.name = self.e_mixname.get()
        self.master.destroy()

    def create_widgets(self):
        font16 = ("Arial", 16, "bold")
        
        #define frames
        self.f0 = Frame(self) # mixname
        self.f1 = Frame(self) # column 1
        self.f2 = Frame(self) # column 2
        self.f3 = Frame(self) # column 3
             
        l1 = Label(self.f0, text="Mix name",font = font16)
        self.e_mixname = Entry(self.f0,font=font16)
        
        self.l_drinks = Label(self.f1,text="Drinks",font = font16)
        self.lb_drinks = Listbox(self.f1,font = font16)

        self.b_add_to_mix = Button(self.f2, text = "->", width = 5, height = 2, font = font16,command = self.add_to_mix)
        self.b_remove_from_mix = Button(self.f2, text = "<-", width = 5, height = 2, font = font16,command = self.remove_from_mix)
        
        self.l_mix = Label(self.f3,text="Mix parts",font = font16)
        self.lb_mix = Listbox(self.f3,font = font16)
        
        self.b_cancel = Button(self.f1, text = "cancel",  command = self.cancel, width = 20, height = 2, font = font16)
        self.b_save = Button(self.f3, text = "Save mix", command = self.save, width = 20, height = 2, font = font16)
        
        # f0 children
        l1.grid(row = 0,column=0)
        self.e_mixname.grid(row = 0, column = 1)
        # end
        
        # f1 children
        self.l_drinks.grid(row = 0,column = 0,sticky=EW)
        self.lb_drinks.grid(row = 1,column=0,sticky=EW, padx = 20, pady = 20)
        self.b_cancel.grid(row = 2,column=0,sticky=EW, padx = 20, pady = 20)
        
        # f2 children
        self.b_add_to_mix.grid(row = 0,column=0,sticky=EW)
        self.b_remove_from_mix.grid(row = 1,column=0,sticky=EW)
        # end
        
        # f3 children
        self.l_mix.grid(row = 0,column = 2,sticky=EW)
        self.lb_mix.grid(row = 1,column=2,sticky=EW, padx = 20, pady = 20)        
        self.b_save.grid(row = 2,column=2,sticky=EW, padx = 20, pady = 20)
        # end
        
        self.f0.grid(row = 0,columnspan = 3,padx = 20, pady = 20)
        self.f1.grid(row = 1,column = 0)
        self.f2.grid(row = 1,column = 1,sticky=EW, padx = 10, pady = 20)
        self.f3.grid(row = 1,column = 2)
        
        self.update_listboxes()

if __name__ == "__main__":
    master = Tk()
    master.drinks = [Drink(name="cola"),Drink(name="bacardi",alc_perc=40),Mix(name="baco1")]
    d = Mix()
    app = mix_dialog(master,d)
    app.mainloop()
