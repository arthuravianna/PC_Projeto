
from he.dataStructure.edge import Edge
from he.dataStructure.linkedlist import Linkedlist


# Vertex class declaration
class Vertex(Linkedlist):

    def __init__(self, point=None, he=None):
        Linkedlist.__init__(self)
        self.point = point
        self.he = he
        self.ID = None

    def delete(self):
        if self.next is not None:
            self.next.prev = self.prev
        if self.prev is not None:
            self.prev.next = self.next

    def getType(self):
        return 'VERTEX'

    def incidentFaces(self):
        adjFaces = []
        he = self.he
        heBegin = he
        while True:
            adjFaces.append(he.loop.face)
            he = he.mate().next
            if he == heBegin:
                break

        return adjFaces

    def incidentEdges(self):
        adjEdges = []
        he = self.he
        heBegin = he

        if he.edge is None:
            return adjEdges

        while True:
            adjEdges.append(he.edge)
            he = he.mate().next

            if he == heBegin:
                break

        return adjEdges

    def adjacentVertices(self):
        adjVertexes = []
        he = self.he
        heBegin = he

        while True:
            he = he.mate()
            if he.mate().vertex != self:
                adjVertexes.append(he.vertex)

            he = he.next

            if he == heBegin:
                break

        return adjVertexes
