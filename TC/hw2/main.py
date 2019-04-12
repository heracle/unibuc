# 4. Sa se scrie un program care implementeaza algoritmul pentru gramatici LR(1). 
# Programul primeste la intrare elementele unei gramatici  
# independente de context oarecare. Programul determina tabela 
# de analiza sintactica asociata si decide daca gramatica data este LR(1). 
# In caz afirmativ, programul permite citirea unui nr oarecare de siruri peste alfabetul terminalilor. 
# Pentru fiecare sir terminal se determina, pe baza tabelei de analiza sintactica obtinuta, 
# daca este in limbajul generat de gramatica respectiva iar in caz afirmativ se afiseaza 
# derivarea sa dreapta (o succesiune de numere, fiecare numar reprezintand numarul productiei aplicate)

import string

parseFile = "gramN.txt"
reductionString = "->"
endSign = "_$_"
errorParseMessage = "The data file %s could not be parsed. \n\
    Please be sure that the format is proper: \n\
        The states are capitalized strings \n\
        The terminals are not capitalized strings \n\
        The operators are any other character readable \n\
        There is a space separator between any 2 consecutive states \n\
        There is a '->' marking the reduction\n\
    Example: \n\
        St -> E1 \n\
        E1 -> Tee \n\
        E1 -> E1 + Tee \n\
        Tee -> int \n\
        Tee -> (E1)" %(parseFile)

def parseGrammar(filePath):
    productions = dict()
    fileDescriptor = open(filePath, "r")
    for actLine in fileDescriptor:
        elementsList = actLine.split()
        if not elementsList[0][0].isupper():
            raise ValueError("first element of a line is not capitalized %s" %(elementsList[0]))
        if elementsList[1] != reductionString:
            raise ValueError("second string of a line is not a reduction string: %s", actLine)
        if not elementsList[0] in productions:
            productions[elementsList[0]] = []
        productions[elementsList[0]].append(elementsList[2:]) 
    return productions

# BlockLine is used as a production inside any block. 'fst' means symbols to the left of dot;
# 'scd' means symbols to the right of dot; 'next' means the special symbol of the production. 
class blockLine():
    def __init__(self, fst, scd, next):
        self.fst = fst
        self.scd = scd
        self.next = next
    def equalTo(self, other):
        if self.fst == other.fst and self.scd == other.scd and self.next == other.next:
            return True
        return False

def getBlockHash(block):
    value = 0
    # Iterate the state.
    for state in block:
        # Iterate the index inside a state.
        for index in block[state]:
            # Itarate fst of our object.
            for fstIndex in index.fst:
                value += hash(fstIndex)
            for scdIndex in index.scd:
                value += hash(scdIndex)
            value += hash(index.next)
    return value

# Add a production to a block if not already existent.
def addInBlock(block, before, after, sign, state):
    if not state in block:
        block[state] = []
    actObj = blockLine(before, after, sign)
    for prod in block[state]:
        if prod.equalTo(actObj):
            return False
    block[state].append(actObj)
    return True

# Add those lines which need to be there because of expanding a dot placed exactly before a state.
def addSupplementaryLines(block, productions):
    somethingChanged =  True
    while somethingChanged:
        somethingChanged = False
        tmpBlock = block.copy()
        for state in tmpBlock:
            for prod in block[state]:
                # There is a need to extend all the production where a dot is placed exactly before a state. The state is stored at 'scd[0]' and the sign at 'scd[1]'.
                if len(prod.scd) == 0 or not prod.scd[0][0].isupper():
                    # This is not a state.
                    continue
                if len(prod.scd) > 1:
                    # Take the next string in the list as the sign.
                    sign = prod.scd[1]
                else:
                    # Take the same sign as the production extended.
                    sign = prod.next

                state = prod.scd[0]
                for origStateProd in productions[state]:
                    if addInBlock(block, [], origStateProd, sign, state):
                        somethingChanged = True

# Receive a block and generate all the resulting blocks after shifting with any element.
def findFurtherBlocks(automaton, block, elemAvailable, productions):
    addedSomething = False
    for fixedElem in elemAvailable:
        newBlock = dict()
        for state in block:
            for prod in block[state]:
                if len(prod.scd) > 0 and prod.scd[0] == fixedElem:
                    newProd = prod.fst.copy()
                    newProd.append(prod.scd[0])
                    addInBlock(newBlock, newProd, prod.scd[1:], prod.next, state)
        addSupplementaryLines(newBlock, productions)

        if automaton.addBlock(newBlock):
            addedSomething = True
        automaton.addEdge(block, newBlock, fixedElem)
    return addedSomething

# Find all the elements mentioned in the initial productions.
def getAllElem(productions):
    res = dict()
    for state in productions:
        for stateProd in productions[state]:
            for prodElem in stateProd:
                res[prodElem] = True
    return res

class automatonObj():
    class pairBlockKey():
        def __init__(self, block, key):
            self.block = block
            self.key = key

    class pairEdge():
        def __init__(self, index1, index2, sign):
            self.first = index1
            self.second = index2
            self.sign = sign

    def __init__(self):
        self.edges = []
        self.blocks = []

    def addBlock(self, block):
        hashBock = getBlockHash(block)
        for localBlock in self.blocks:
            if localBlock.key == hashBock:
                return False
        self.blocks.append(self.pairBlockKey(block, hashBock))
        return True
            
    def addEdge(self, block1, block2, reqSign):
        hashBlock1 = getBlockHash(block1)
        hashBlock2 = getBlockHash(block2)
        index1 = -1
        index2 = -1
        for i in range(len(self.blocks)):
            if self.blocks[i].key == hashBlock1:
                index1 = i
            if self.blocks[i].key == hashBlock2:
                index2 = i
        if index1 == -1 or index2 == -1:
            raise ValueError("asked to add edges between blocks that are not already inserted in the automaton")
        for localEdge in self.edges:
            if (localEdge.first == index1 and localEdge.second == index2 and localEdge.sign == reqSign):
                return
        self.edges.append(self.pairEdge(index1, index2, reqSign))
    
    def print(self):
        for block in self.blocks:
            print ("block key = " + str(block.key))
            for state in block.block:
                print ("\t" + state)
                # Iterate the index inside a state.
                for index in  block.block[state]:
                    # Iterate fst of our object.
                    print ("\t\t before dot:")
                    for fstIndex in index.fst:
                        print ("\t\t\t " + fstIndex)
                    print ("\t\t after dot:")
                    for scdIndex in index.scd:
                        print ("\t\t\t " + scdIndex)
                    print ("\t\t sign " + index.next)
                    print ("\t\t -----")
            print ("edges:")
        for edge in self.edges:
            print("\t" + str(edge.first) + " " + edge.sign + "  " + str(edge.second))

def getAutomaton(productions):
    automaton = automatonObj()
    actBlock = dict()
    for state in productions:
        for dest in productions[state]:
            addInBlock(actBlock, [], dest, endSign, state)
    addSupplementaryLines(actBlock, productions)
    automaton.addBlock(actBlock)
    elemAvailable = getAllElem(productions)

    somethingChanged = True
    while somethingChanged:
        somethingChanged = False
        for block in automaton.blocks:
            if findFurtherBlocks(automaton, block.block, elemAvailable, productions):
                somethingChanged = True
    automaton.print()
    return automaton

# Main
if __name__ == "__main__":
    productions = parseGrammar(parseFile)
    # print (productions)
    automaton = getAutomaton(productions)
    pass
