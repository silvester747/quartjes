# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$Jul 3, 2011 3:03:58 PM$"

from Tkinter import *

class dialogSell(Frame):
    def __init__(self, root, conn = None):
        root.title('Sell Drinks')
        Frame.__init__(self, root)
        self.root = root
        self.pack()
        self.conn = conn
        self.db = self.conn.get_service_interface("database")
        self.createWidgets()

    def sell_drink(self):
        self.calc_price
        self.selection = self.lb_drinks.curselection()
        if len(self.selection) > 0:
            self.selected = int(self.selection[0])
        else:
            return

        self.entryvalue = self.sv_amount.get()
        if len(self.entryvalue) >0:
            amount = entryvalue
        else:
            return
        self.sex = self.conn.get_service_interface("stock_exchange")
        self.sex.sell(drink[self.selected], amount)

    def fill_drinks_listbox(self,lb_drinks):
        self.drinks = self.db.get_drinks()
        for d in self.drinks:
            lb_drinks.insert(END,d.name)

    def calc_price(self):
        self.entryvalue = self.e_amount.get()
        if len(self.entryvalue) >0:
            amount = int(self.entryvalue)
        else:
            return
        self.selection = self.lb_drinks.curselection()

        if len(self.selection) > 0:
            selected = int(self.selection[0])
        else:
            return
        self.drinks = self.db.get_drinks()
        self.newprice = amount * int(self.drinks[selected].sellprice_quartjes())
        print(self.newprice)
        self.sv_price.set(self.newprice)

    def printklik(self, eventdata):
        print("klik")


    def createWidgets(self):
        font16 = ("Arial", 26, "bold")
        font12 = ("Arial", 18, "bold")
        self.lb_drinks = Listbox(self, height=40, width = 100)
        self.lb_drinks.grid(row = 0,column=0,rowspan=10,sticky=EW, padx = 20, pady = 20)
        self.lb_drinks.bind("<Button-1>", self.printklik)

        self.fill_drinks_listbox(self.lb_drinks)

        self.frame1 = Frame(self)
        self.frame1.grid(row = 0, column = 1)

        self.l_amount = Label(self.frame1, text = " Amount:", width = 20, height = 0, font = font16)
        self.l_amount.grid(row = 0,column=1,sticky=EW, padx = 20, pady = 0)

        self.sv_amount = StringVar()
        self.e_amount = Entry(self.frame1, width = 10, textvariable = self.sv_amount, font = font16, text = 1)
        self.e_amount.grid(row = 1,column=1,sticky=EW, padx = 0, pady = 0)
        self.e_amount.insert(0,1)

        self.sv_price = StringVar()
        self.l_price = Label(self.frame1, textvariable = self.sv_price, width = 20, height = 0, font = font16)
        self.l_price.grid(row = 2,column=1,sticky=EW, padx = 20, pady = 0)

        self.b_update_price = Button(self.frame1, width = 10, text = "Update Price", font = font12, command = self.calc_price)
        self.b_update_price.grid(row = 1, column = 2)

        self.b_sell = Button(self, text = "Sell", bg="#999999", command = self.sell_drink, activebackground="#ff5555", width = 20, height = 2, font = font16)
        self.b_sell.grid(row = 1,column=1,sticky=EW, padx = 20, pady = 20)


if __name__ == "__main__":
    root = Tk()
    app = dialogSell(root)
    app.mainloop()