from he.dataStructure.linkedlist import Linkedlist


class Face(Linkedlist):

    def __init__(self, shell=None, loop=None, prev=None, next=None, patch=None):
        Linkedlist.__init__(self, prev, next)
        self.shell = shell
        self.loop = loop  # external loop
        self.intLoops = []  # list of internal loops
        self.patch = patch
        self.ID = None

    def delete(self):

        # update linked list
        if self.next is not None:
            self.next.prev = self.prev
        if self.prev is not None:
            self.prev.next = self.next

    def getType(self):
        return 'FACE'

    def adjacentFaces(self):
        adjFaces = []
        loop = self.loop
        if loop.he is not None:
            he = loop.he
            heBegin = he

            while True:
                if he.mate().loop.face != self:
                    adjFaces.append(he.mate().loop.face)

                he = he.next
                if he == heBegin:
                    break

        return adjFaces

    def incidentEdges(self):
        adjEdges = []
        he = self.loop.he
        heBegin = he

        while True:
            adjEdges.append(he.edge)
            he = he.next

            if he == heBegin:
                break

        return adjEdges

    def incidentVertices(self):
        adjVertexes = []
        he = self.loop.he
        heBegin = he

        while True:
            adjVertexes.append(he.vertex)
            he = he.next

            if he == heBegin:
                break

        return adjVertexes

    def internalFaces(self):
        internalFaces = []

        loop = self.loop.next

        while loop is not None:
            if loop.he.mate().loop != loop:
                if loop.he.mate().loop.isClosed:
                    internalFaces.append(loop.he.mate().loop.face)

            loop = loop.next

        return internalFaces

    def updateBoundary(self):
        he_init = self.loop.he
        he = he_init
        bound = []
        orientation = []
        while True:
            if he.edge is not None:
                bound.append(he.edge.segment)
                orientation.append(he == he.edge.he1)

            he = he.next

            if he == he_init:
                break

        self.patch.setBoundary(bound, orientation)

    def updateHoles(self):
        loop = self.loop.next
        self.intLoops.clear()  # clear the list of inner loops
        bound = []
        orientation = []

        while loop is not None:
            self.intLoops.append(loop)
            he_init = loop.he
            he = he_init
            loop_bound = []
            loop_orientation = []

            if he.edge is not None:
                while True:
                    if he.mate().loop.isClosed:
                        loop_bound.append(he.edge.segment)
                        loop_orientation.append(he == he.edge.he1)
                    he = he.next

                    if he == he_init:
                        break

                if len(loop_bound) > 0:
                    bound.append(loop_bound)
                    orientation.append(loop_orientation)

            loop = loop.next

        self.patch.setHoles(bound, orientation)
