# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *
from tkColorChooser import *
from quartjes.models.drink import *

class dialog(Frame):
    def __init__(self, root, type, conn = None,drinks = [Drink(),Drink()], mix = Mix()):
        Frame.__init__(self, root)
        self.root = root
        self.pack()
        if conn is not None:
            self.conn = conn
            self.db = self.conn.get_service_interface("database")
            drinks = self.db.get_drinks()

        self.drinks = drinks
        self.mix = mix
        self.createWidgets(type)

    def add_drink(self):
        d = Drink()
        drink_dialog(Tk(),d)
        print d

    def add_mix(self):        
        dialog(Tk(),"add_mix",mix = self.mix)
        print m

    def edit_drink(self):
        selection = self.lb_drinks.curselection()
        if len(selection) > 0:
            selected = int(selection[0])            
            drink_dialog(Tk(),self.drinks[selected])


    def remove_drink(self):
        print 'hoi'

    def fill_listbox(self,lb_drinks,drinks):
        names = []
        for d in drinks:
            lb_drinks.insert(END,d.name)

    def add_to_mix(self):
        selection = self.lb_drinks.curselection()
        if len(selection) > 0:
            selected = int(selection[0])
            self.mix.insert_drink(self.drinks[selected])
            self.refill_listboxes()

    def remove_from_mix(self):
        selection = self.lb_mix.curselection()
        if len(selection) > 0:
            selected = int(selection[0])
            self.mix.remove_drink([selected])
            self.refill_listboxes()

    def refill_listboxes(self):
        self.lb_drinks.delete(0,END)
        self.lb_mix.delete(0,END)
        self.fill_listbox(self.lb_drinks,self.drinks)
        self.fill_listbox(self.lb_mix,self.mix.drinks)

    def createWidgets(self,type):
        font16 = ("Arial", 16, "bold")
        if type is "edit_db":
            self.root.title('Edit database')
            self.lb_drinks = Listbox(self,font = font16)
            self.lb_drinks.grid(row = 0,column=0,rowspan=10,sticky=EW, padx = 20, pady = 20)

            self.b_add_drink = Button(self, text = "Add drink",command =  self.add_drink, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 0,column=1,sticky=EW, padx = 20, pady = 20)

            self.b_add_drink = Button(self, text = "Add mix",command =  self.add_mix, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 1,column=1,sticky=EW, padx = 20, pady = 20)

            self.b_add_drink = Button(self, text = "Edit drink",command =  self.edit_drink, width = 20, height = 2, font = font16)
            self.b_add_drink.grid(row = 2,column=1,sticky=EW, padx = 20, pady = 20)

            self.b_remove_drink = Button(self, text = "Remove drink", command = self.remove_drink, width = 20, height = 2, font = font16)
            self.b_remove_drink.grid(row = 3,column = 1,sticky=EW, padx = 20, pady = 20)

            self.fill_listbox(self.lb_drinks,self.drinks)
        elif type is "add_mix":
            self.mix = Mix()
            self.root.title('Add mix')

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
            self.refill_listboxes()

class drink_dialog(Frame):
    def __init__(self, root, drink):
        Frame.__init__(self,root)
        self.root = root
        self.tags = ["name","alc_perc","unit_price","unit_amount"]
        self.drink = drink        
        self.temp_color = self.drink.color
        self.pack(padx = 20, pady = 20)
        self.createWidgets()
        self.reset_object_values()

    def reset_object_values(self):
        self.temp_color = self.drink.color
        hexcolor = '#%02x%02x%02x' % self.temp_color
        self.b_color.config(bg = hexcolor)

        for tag in self.tags:
            text = self.drink.__dict__[tag]
            self.__dict__["e_" + tag].delete(0,END)
            self.__dict__["e_" + tag].insert(END,text)
            
    def set_color(self):
        color = askcolor(master=self,initialcolor = self.temp_color)
        self.temp_color = color[0]
        self.b_color.config(bg = color[1])

    def cancel(self):
        self.root.destroy()

    def save(self):
        self.drink.color = self.temp_color
        for tag in self.tags:
            self.drink.__dict__[tag] = self.__dict__["e_" + tag].get()

        self.root.destroy()

    def createWidgets(self):
        self.l_color = Label(self,text = "Color")
        self.l_color.grid(row = len(self.tags)+1,column = 0,sticky=E)
        hexcolor = '#%02x%02x%02x' % self.temp_color
        self.b_color = Button(self,bg = hexcolor,command =  self.set_color)
        self.b_color.grid(row = len(self.tags)+1,column = 1,sticky=EW)

        self.b_reset = Button(self, text = "Reset values",width = 40,command = self.reset_object_values)
        self.b_reset.grid(row = len(self.tags)+2,column = 0,columnspan = 2,pady=10)

        self.b_save = Button(self, text = "Save drink & exit",width = 20, command=self.save)
        self.b_save.grid(row = len(self.tags)+3,column = 0)

        self.b_cancel = Button(self, text = "Cancel",width = 20,command=self.cancel)
        self.b_cancel.grid(row = len(self.tags)+3,column = 1)

        for tag in self.tags:
            self.__dict__["l_" + tag] = Label(self,text = tag)
            self.__dict__["l_" + tag].grid(row = self.tags.index(tag),column = 0,sticky=E)
            
            self.__dict__["e_" + tag] = Entry(self)
            self.__dict__["e_" + tag].grid(row = self.tags.index(tag),column = 1,sticky=EW)

if __name__ == "__main__":
    root = Tk()
    d = Drink()
    print d
    #app = drink_dialog(root,d)
    app = dialog(root,"edit_db")
    app.mainloop()
    print d