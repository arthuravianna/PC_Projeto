from he.dataStructure.vertex import Vertex
from he.dataStructure.halfedge import HalfEdge
from he.dataStructure.loop import Loop


# MakeVertexRing class declaration
class MVR:
    def __init__(self, point, face, vertex=None):

        if point is not None:
            self.vertex = Vertex(point)
        else:
            self.vertex = vertex

        self.face = face

    def name(self):
        return 'MVR'

    def execute(self):

        #print('------------- MVR -------------------')

        # create topological entities
        newloop = Loop(self.face)
        newhe = HalfEdge(self.vertex, newloop)

        # set parameters
        newloop.he = newhe
        newhe.prev = newhe
        newhe.next = newhe
        self.vertex.he = newhe

    def unexecute(self):
        kvr = KVR(self.vertex, self.face)
        kvr.execute()


# KillVertexRing class declaration
class KVR:
    def __init__(self, vertex, face):
        self.vertex = vertex
        self.face = face

    def name(self):
        return 'KVR'

    def execute(self):

        #print('------------- KVR -------------------')

        he = self.vertex.he
        loop = he.loop

        self.vertex.he = None

        he.delete()
        loop.delete()

        del he

    def unexecute(self):
        mvr = MVR(None, self.face, self.vertex)
        mvr.execute()
