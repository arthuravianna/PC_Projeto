
class UndoRedo:

    def __init__(self, limit=-1):
        self.isInsertingCommand = False
        self.limit = limit
        self.temp = []
        self.undocommands = []
        self.redocommands = []

    def beginOperation(self):
        if self.isInsertingCommand:
            return False

        self.temp = []
        self.isInsertingCommand = True
        return True

    def endOperation(self):

        if len(self.temp) > 0:

            # insert command
            self.undocommands.insert(0, self.temp)

            # check if reached limit
            if len(self.undocommands) - 1 == self.limit:
                self.temp = self.undocommands.pop()

            self.clearRedo()

        self.isInsertingCommand = False

    def insertCommand(self, _command):

        if self.isInsertingCommand:
            self.temp.insert(0, _command)
            return True

        return False

    def lastCommand(self):
        return self.temp[0]

    def lastOperation(self):
        return self.temp

    def hasUndo(self):
        return len(self.undocommands) > 0

    def hasRedo(self):
        return len(self.redocommands) > 0

    def undo(self):
        if not self.isInsertingCommand:
            if self.hasUndo():
                self.temp = self.undocommands.pop(0)
                self.redocommands.insert(0, self.temp)

    def redo(self):
        if not self.isInsertingCommand:
            if self.hasRedo():
                self.temp = self.redocommands.pop(0)
                self.undocommands.insert(0, self.temp)

    def clear(self):
        self.isInsertingCommand = False
        self.clearRedo()
        self.clearUndo()
        self.temp.clear()

    def clearUndo(self):
        self.undocommands.clear()

    def clearRedo(self):
        self.redocommands.clear()
