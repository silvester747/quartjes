# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 12:34:35$"

import uuid

class Drank():
    """
    Drank class
    """

    def __init__(self,dranknaam):
        self.id = uuid.uuid4()
        self.dranknaam = dranknaam
        self.alc_perc = 0
        self.color = [0,0,0,0]
        self.prijs = 0

if __name__ == "__main__":
    print "Hello World"
