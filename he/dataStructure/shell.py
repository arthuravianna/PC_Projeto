from he.dataStructure.linkedlist import Linkedlist


# Shell class declaration
class Shell(Linkedlist):

    def __init__(self, face=None, prev=None, next=None):
        Linkedlist.__init__(self, prev, next)
        self.face = face
        self.vertices = []
        self.edges = []
        self.faces = []
        self.num_vertices = 0
        self.num_edges = 0
        self.num_faces = -1
        self.num_loops = 0
        self.num_he = 0

    def delete(self):

        # update linked list
        if self.next is not None:
            self.next.prev = self.prev
        if self.prev is not None:
            self.prev.next = self.next

    def insertVertex(self, _vertex):
        self.vertices.append(_vertex)

        if _vertex.ID is None:
            self.num_vertices += 1
            _vertex.ID = self.num_vertices

        if _vertex.he is not None:
            if _vertex.he.ID is None:
                self.num_he += 1
                _vertex.he.ID = self.num_he

            if _vertex.he.loop.ID is None:
                self.num_loops += 1
                _vertex.he.loop.ID = self.num_loops

        if len(self.vertices) > 0:
            _vertex.prev = self.vertices[-1]
            self.vertices[-1].next = _vertex

    def insertEdge(self, _edge):
        self.edges.append(_edge)

        if _edge.ID is None:
            self.num_edges += 1
            _edge.ID = self.num_edges

        if _edge.he1 is not None:
            if _edge.he1.ID is None:
                self.num_he += 1
                _edge.he1.ID = self.num_he

        if _edge.he2 is not None:
            if _edge.he2.ID is None:
                self.num_he += 1
                _edge.he2.ID = self.num_he

        if len(self.edges) > 0:
            _edge.prev = self.edges[-1]
            self.edges[-1].next = _edge

    def insertFace(self, _face):
        self.faces.append(_face)

        if _face.ID is None:
            self.num_faces += 1
            _face.ID = self.num_faces

        if _face.loop.ID is None:
            self.num_loops += 1
            _face.loop.ID = self.num_loops

    def removeVertex(self, _vertex):
        self.vertices.remove(_vertex)

    def removeEdge(self, _edge):
        self.edges.remove(_edge)

    def removeFace(self, _face):
        self.faces.remove(_face)

    def renumberHe(self):

        self.num_he = 0
        self.num_loops = -1

        for face in self.faces:
            loop = face.loop
            self.num_loops += 1
            loop.ID = self.num_loops

            while loop is not None:
                he = loop.he
                he_begin = he

                if he is not None:
                    while True:
                        self.num_he += 1
                        he.ID = self.num_he

                        he = he.next

                        if he == he_begin:
                            break

                loop = loop.next
