# To change this template, choose Tools | Templates
# and open the template in the editor.

__author__="piet"
__date__ ="$5-jun-2011 12:34:42$"

class Mix():
    """
    Protocol implementation for the Quartjes server. For now we are using a basic
    Netstring receiver to listen for xml messages encoded as netstrings.
    """

    def __init(self,dranken):
        self.id = uuid.uuid4()
        self.dranken = dranken

if __name__ == "__main__":
    print "Hello World"
