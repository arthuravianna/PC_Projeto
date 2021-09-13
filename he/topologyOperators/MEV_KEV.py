from he.dataStructure.edge import Edge
from he.dataStructure.vertex import Vertex
from he.dataStructure.halfedge import HalfEdge


# MakeEdgeVertex class declaration
class MEV:
    def __init__(self, point, segment, v_begin, v_next1, v_next2, face1, face2, vertex=None, edge=None):

        if point is not None:
            self.vertex = Vertex(point)
            self.edge = Edge(segment)
        else:
            self.vertex = vertex
            self.edge = edge

        self.v_begin = v_begin
        self.v_next1 = v_next1
        self.v_next2 = v_next2
        self.face1 = face1
        self.face2 = face2

    def name(self):
        return 'MEV'

    def execute(self):

        # print('-----------------MEV-----------------')

        # get half-edges
        he1 = HalfEdge.inBetween(self.v_begin, self.v_next1, self.face1)
        he2 = HalfEdge.inBetween(self.v_begin, self.v_next2, self.face2)

        he = he1

        while he != he2:
            he.vertex = self.vertex
            he = he.mate().next

        self.edge.AddHe(he2.vertex, he1, False)
        self.edge.AddHe(self.vertex, he2, True)

        self.vertex.he = he2.prev
        he2.vertex.he = he2

    def unexecute(self):
        kev = KEV(self.edge, self.vertex)
        kev.execute()


# KillEdgeVertex class declaration
class KEV:
    def __init__(self, edge=None, vertex=None):
        self.edge = edge
        self.vertex = vertex
        self.v_begin = None
        self.v_next1 = None
        self.v_next2 = None
        self.face1 = None
        self.face2 = None

    def name(self):
        return 'KEV'

    def execute(self):

        # print('------------KEV-------------------')

        he1 = self.edge.he1
        he2 = self.edge.he2

        # switch half-edges such that he1.vertex will be deleted
        if he1.vertex != self.vertex:
            temp = he1
            he1 = he2
            he2 = temp

        # Store the necessary entities for undo
        self.v_begin = he2.vertex

        if he2.next == he1 and he1.next == he2:
            self.v_next1 = self.v_begin
            self.v_next2 = self.v_begin

        elif he2.next != he1 and he1.next == he2:
            self.v_next1 = he2.next.mate().vertex
            self.v_next2 = he1.next.mate().vertex
        else:
            self.v_next1 = he1.next.mate().vertex
            self.v_next2 = he1.next.mate().vertex  # é he1 msm?

        self.face1 = he1.loop.face
        self.face2 = he2.loop.face

        # Now, execute the operation
        he = he2.next

        while he != he1:
            he.vertex = he2.vertex
            he = he.mate().next

        he2.vertex.he = he1.next
        he1.loop.he = he1.delete()
        he2.loop.he = he2.delete()

        # cleaning the removed entities
        self.edge.he1 = None
        self.edge.he2 = None
        self.vertex.he = None

        if he1.prev.next != he1:
            del he1

        if he2.prev.next != he2:
            del he2

        self.vertex.delete()
        self.edge.delete()

    def unexecute(self):
        mev = MEV(None, None, self.v_begin, self.v_next1,
                  self.v_next2, self.face1, self.face2, self.vertex, self.edge)
        mev.execute()
