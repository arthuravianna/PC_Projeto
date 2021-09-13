from geometry.segments.segment import Segment
from OpenGL.error import Error
from he.topologyOperators.MEF_KEF import MEF, KEF
from he.topologyOperators.MVFS_KVFS import MVFS, KVFS
from he.topologyOperators.MEKR_KEMR import MEKR, KEMR
from he.topologyOperators.MVR_KVR import MVR, KVR
from he.topologyOperators.MEV_KEV import MEV, KEV
from he.topologyOperators.MVSE_KVJE import MVSE, KVJE
from he.auxoperations import *
from geometry.segments.line import Line
from geometry.point import Point
from he.undoredo import UndoRedo
from compgeom.compgeom import CompGeom
import math
from he.hefile import HeFile


class HeController:
    def __init__(self, _hemodel=None):
        self.undoredo = UndoRedo(10)
        self.hemodel = _hemodel

    def setHeModel(self, _hemodel):
        self.hemodel = _hemodel

    def insertPoint(self, _pt, _tol):
        self.undoredo.beginOperation()

        if self.hemodel.isEmpty():
            shell = self.makeVertexFace(_pt)
            self.hemodel.infinityFace = shell.face
        else:
            self.addPoint(_pt, _tol)

        self.printDebug()
        self.undoredo.endOperation()
        self.update()

    def addPoint(self, _pt, _tol):
        # check whether there is already a point with the same coordinates
        for point in self.hemodel.points:
            tol = Point(_tol, _tol)
            if Point.equal(_pt, point, tol):
                # in this case there is already a vertex with the same coordinates
                return

        # if there isn't one, check whether the point intersects an edge in model
        intersec = False
        edges = self.hemodel.shell.edges
        for edge in edges:
            intersec, param, pi = edge.segment.intersectPoint(_pt, _tol)

            if intersec:
                edge_target = edge
                break

        if intersec:
            # if there is an intersection, then split the edge
            segments = edge_target.segment.splitSegment(param, pi)
            self.splitSegment(pi, edge_target, segments[0], segments[1])

        else:
            # if it do not intersect, then find the face where it lies on.
            #  Then add a new vertex to the model
            face_target = self.hemodel.whichFace(_pt)
            self.makeVertexInsideFace(_pt, face_target)

    def insertSegment(self, _segment, _tol):
        self.undoredo.beginOperation()

        status, pts, params = _segment.selfIntersect()
        if status:
            # if there are self-intersections, split the segment in segments and
            # then insert each segment at a time
            segment_segments = _segment.split(params, pts)

            for segment in segment_segments:
                if segment is not None:
                    pts = segment.getPoints()
                    self.addSegment(segment, _tol)
        else:
            self.addSegment(_segment, _tol)

        self.undoredo.endOperation()
        self.printDebug()
        self.update()

    def addSegment(self, _segment, _tol):
        segmentPts = _segment.getPoints()
        init_pt = segmentPts[0]
        end_pt = segmentPts[-1]
        is_closed = (Point.euclidiandistance(init_pt, end_pt) <= _tol)

        if self.hemodel.isEmpty():
            if is_closed:
                # in this case insert the initial point and then the closed segment
                shell = self.makeVertexFace(init_pt)
                self.makeEdge(_segment, init_pt, init_pt)
            else:
                shell = self.makeVertexFace(init_pt)
                self.makeVertexInsideFace(end_pt, shell.face)
                self.makeEdge(_segment, init_pt, end_pt)

        else:
            if is_closed:
                # in this case insert the initial point and then the closed segment
                self.addPoint(init_pt, _tol)

            # intersect incoming edge with existing model
            incoming_edge_split_map, existent_edges_split_map = self.intersectModel(
                _segment, _tol)

            # split the existing edges
            self.splitExistingEdges(existent_edges_split_map)

            # insert incoming segments
            self.insertIncomingSegments(
                _segment, incoming_edge_split_map, _tol)

    def update(self):

        if self.hemodel.isEmpty():
            return

        faces = self.hemodel.shell.faces
        for i in range(1, len(faces)):
            faces[i].updateBoundary()
            faces[i].updateHoles()

    def makeVertexFace(self, _point):

        # creates, executes and stores the operation

        mvfs = MVFS(_point)
        mvfs.execute()
        self.undoredo.insertCommand(mvfs)

        # insert entities into the model data structure
        insertShell = InsertShell(mvfs.shell, self.hemodel)
        insertShell.execute()
        self.undoredo.insertCommand(insertShell)
        insertFace = InsertFace(mvfs.face, self.hemodel)
        insertFace.execute()
        self.undoredo.insertCommand(insertFace)
        insertVertex = InsertVertex(mvfs.vertex, self.hemodel)
        insertVertex.execute()
        self.undoredo.insertCommand(insertVertex)

        return mvfs

    def makeVertexInsideFace(self, _point, _face):

        # creates, executes and stores the operation
        mvr = MVR(_point, _face)
        mvr.execute()
        self.undoredo.insertCommand(mvr)

        # insert the vertex into the model data structure
        insertVertex = InsertVertex(mvr.vertex, self.hemodel)
        insertVertex.execute()
        self.undoredo.insertCommand(insertVertex)

    def makeEdge(self, _segment, _init_point, _end_point):
        # This function should be used just when the model has already been stitched by the segment.
        # This means that the geometric checks and operations should be done before you call it.
        # If this is the case, then four possibilities may occour:
        # 1: if both end points of the segment belong to vertexes of the model
        # 2: if just the first point of the segment belongs to a vertex of the model
        # 3: if just the last point of the segment belongs to a vertex of the model
        # 4: if the boundary points of the segment do not belong to the model yet

        # check if the points are already present in the model
        initpoint_belongs = False
        endpoint_belongs = False
        init_vertex = _init_point.vertex
        end_vertex = _end_point.vertex

        if init_vertex is not None:
            initpoint_belongs = True

        if end_vertex is not None:
            endpoint_belongs = True

        if initpoint_belongs and endpoint_belongs:

            begin_tan = _segment.tangent(0.0)
            begin_curv = _segment.curvature(0.0)
            begin_tan = Point.normalize(begin_tan)

            he1 = self.getHalfEdge(init_vertex, begin_tan.getX(), begin_tan.getY(),
                                   -begin_tan.getY(), begin_tan.getX(), begin_curv)

            end_tan = _segment.tangent(1.0)
            end_curv = _segment.curvature(1.0)
            end_tan = Point.normalize(end_tan)

            he2 = self.getHalfEdge(end_vertex, - end_tan.getX(), -end_tan.getY(),
                                   -end_tan.getY(), end_tan.getX(), end_curv)

            if init_vertex.point != end_vertex.point:
                # case 1.1: points are different, then it is an open segment
                # checks if the half-edges have the same loop to decide between MEF and MEKR

                if he1.loop != he2.loop:

                    # case 1.1.1: the half-edges belong to the different loops, then it's a MEKR
                    if he1.loop == he1.loop.face.loop:
                        # if he1 belongs to the outter loop, then no need to inverter
                        mekr = MEKR(_segment, init_vertex, end_vertex, he1.mate(
                        ).vertex, he2.mate().vertex, he1.loop.face)
                        mekr.execute()
                        self.undoredo.insertCommand(mekr)
                    else:
                        # if he2 belongs to the outter loop, then inverter the
                        # half-edges to keep the consistency with the parametric
                        # geometric definition
                        mekr = MEKR(_segment, end_vertex, init_vertex, he2.mate(
                        ).vertex, he1.mate().vertex, he2.loop.face)
                        mekr.execute()
                        self.undoredo.insertCommand(mekr)

                        # inverter the half-edges to keep the consistency with
                        # the parametric geometric definition
                        flip = Flip(mekr.edge)
                        flip.execute()
                        self.undoredo.insertCommand(flip)

                    # insert the entities into the model data structure
                    insertEdge = InsertEdge(mekr.edge, self.hemodel)
                    insertEdge.execute()
                    self.undoredo.insertCommand(insertEdge)

                else:  # case 1.1.2: the half-edges belong to same loops, then it's a MEF

                    existent_loop = he1.loop
                    existent_face = existent_loop.face

                    if self.isSegmentLoopOriented(_segment, he1, he2):
                        mef = MEF(_segment, init_vertex, end_vertex, he1.mate(
                        ).vertex, he2.mate().vertex, existent_face)
                        mef.execute()
                        self.undoredo.insertCommand(mef)
                    else:
                        mef = MEF(_segment, end_vertex, init_vertex, he2.mate(
                        ).vertex, he1.mate().vertex, existent_face)
                        mef.execute()
                        self.undoredo.insertCommand(mef)

                        # inverter the half-edges to keep the consistency with
                        # the parametric geometric definition
                        flip = Flip(mef.edge)
                        flip.execute()
                        self.undoredo.insertCommand(flip)

                    # insert the entities into the hemodel data structure
                    insertEdge = InsertEdge(mef.edge, self.hemodel)
                    insertEdge.execute()
                    self.undoredo.insertCommand(insertEdge)
                    insertFace = InsertFace(mef.face, self.hemodel)
                    insertFace.execute()
                    self.undoredo.insertCommand(insertFace)

                    mef.face.updateBoundary()

                    inner_loops = self.findInnerLoops(
                        existent_face, mef.face, existent_loop)
                    migrateLoops = MigrateLoops(
                        existent_face, mef.face, inner_loops)
                    migrateLoops.execute()
                    self.undoredo.insertCommand(migrateLoops)

                    mef.face.updateHoles()

            else:
                # case 1.2: points are the same, then it is a closed segment
                split_point = _segment.getPoint(0.5)
                seg1, seg2 = _segment.splitSegment(0.5, split_point)

                # --------- Insert first segment ---------------------

                # insert point and segment 1 into the half-edge data structure
                mev = MEV(split_point, seg1, init_vertex, he1.mate().vertex,
                          he1.mate().vertex, he1.loop.face, he1.loop.face)
                mev.execute()
                self.undoredo.insertCommand(mev)

                # # inverter the half-edges to keep the consistency with
                # the parametric geometric definition
                flip = Flip(mev.edge)
                flip.execute()
                self.undoredo.insertCommand(flip)

                self.printDebug()

                insertVertex = InsertVertex(mev.vertex, self.hemodel)
                insertVertex.execute()
                self.undoredo.insertCommand(insertVertex)
                insertEdge1 = InsertEdge(mev.edge, self.hemodel)
                insertEdge1.execute()
                self.undoredo.insertCommand(insertEdge1)

                # --------- Insert second segment ---------------------

                begin_tan = seg2.tangent(0.0)
                begin_curv = seg2.curvature(0.0)
                begin_tan = Point.normalize(begin_tan)

                he1 = self.getHalfEdge(mev.vertex, begin_tan.getX(), begin_tan.getY(),
                                       -begin_tan.getY(), begin_tan.getX(), begin_curv)

                end_tan = seg2.tangent(1.0)
                end_curv = seg2.curvature(1.0)
                end_tan = Point.normalize(end_tan)

                he2 = self.getHalfEdge(end_vertex, - end_tan.getX(), -end_tan.getY(),
                                       -end_tan.getY(), end_tan.getX(), end_curv)

                existent_loop = he1.loop
                existent_face = existent_loop.face

                # check segment orientation
                if self.isSegmentLoopOriented(seg2, he1, he2):
                    mef = MEF(seg2, mev.vertex, end_vertex, he1.mate(
                    ).vertex, he2.mate().vertex, existent_face)
                    mef.execute()
                    self.undoredo.insertCommand(mef)
                else:
                    mef = MEF(seg2, end_vertex, mev.vertex, he2.mate(
                    ).vertex, he1.mate().vertex, existent_face)
                    mef.execute()
                    self.undoredo.insertCommand(mef)

                    # inverter the half-edges to keep the consistency with
                    # the parametric geometric definition
                    flip = Flip(mef.edge)
                    flip.execute()
                    self.undoredo.insertCommand(flip)

                # insert the entities into the hemodel data structure
                insertEdge2 = InsertEdge(mef.edge, self.hemodel)
                insertEdge2.execute()
                self.undoredo.insertCommand(insertEdge2)
                insertFace = InsertFace(mef.face, self.hemodel)
                insertFace.execute()
                self.undoredo.insertCommand(insertFace)

                mef.face.updateBoundary()

                inner_loops = self.findInnerLoops(
                    existent_face, mef.face, existent_loop)
                migrateLoops = MigrateLoops(
                    existent_face, mef.face, inner_loops)
                migrateLoops.execute()
                self.undoredo.insertCommand(migrateLoops)

                mef.face.updateHoles()

                # -- Join both segments defining the closed segment ---

                # insert the closed segment into the half-edge data structure
                kvje = KVJE(_segment, mev.vertex, mev.edge, mef.edge)
                kvje.execute()
                self.undoredo.insertCommand(kvje)

                # insert the entities into the hemodel data structure
                removeEdge1 = RemoveEdge(mev.edge, self.hemodel)
                removeEdge1.execute()
                self.undoredo.insertCommand(removeEdge1)
                removeEdge2 = RemoveEdge(mef.edge, self.hemodel)
                removeEdge2.execute()
                self.undoredo.insertCommand(removeEdge2)
                removeVertex = RemoveVertex(mev.vertex, self.hemodel)
                removeVertex.execute()
                self.undoredo.insertCommand(removeVertex)
                insertEdge = InsertEdge(kvje.new_edge, self.hemodel)
                insertEdge.execute()
                self.undoredo.insertCommand(insertEdge)

        elif initpoint_belongs and not endpoint_belongs:
            # case 2: only the initial point of the segment belongs to a vertex of the model

            # get the half-edge of the vertex
            begin_tan = _segment.tangent(0.0)
            begin_curv = _segment.curvature(0.0)
            begin_tan = Point.normalize(begin_tan)
            he = self.getHalfEdge(init_vertex, begin_tan.getX(), begin_tan.getY(),
                                  -begin_tan.getY(), begin_tan.getX(), begin_curv)

            # insert point and incoming segment into the half-edge data structure
            mev = MEV(_end_point, _segment, init_vertex, he.mate().vertex,
                      he.mate().vertex, he.loop.face, he.loop.face)
            mev.execute()
            self.undoredo.insertCommand(mev)

            # inverter the half-edges to keep the consistency with
            # the parametric geometric definition
            flip = Flip(mev.edge)
            flip.execute()
            self.undoredo.insertCommand(flip)

            # insert the entities into the model data structure
            insertEdge = InsertEdge(mev.edge, self.hemodel)
            insertEdge.execute()
            self.undoredo.insertCommand(insertEdge)
            insertVertex = InsertVertex(mev.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertCommand(insertVertex)

        elif not initpoint_belongs and endpoint_belongs:
            # case 3: only the end point of the segment belongs to a vertex of the model

            # get the half-edge of the vertex
            end_tan = _segment.tangent(1.0)
            end_curv = _segment.curvature(1.0)
            end_tan = Point.normalize(end_tan)
            he = self.getHalfEdge(
                end_vertex, - end_tan.getX(), -end_tan.getY(), -end_tan.getY(), end_tan.getX(), end_curv)

            # insert point and incoming segment into the half-edge data structure
            mev = MEV(_init_point, _segment, end_vertex, he.mate().vertex,
                      he.mate().vertex, he.loop.face, he.loop.face)
            mev.execute()
            self.undoredo.insertCommand(mev)

            # insert the entities into the model data structure
            insertEdge = InsertEdge(mev.edge, self.hemodel)
            insertEdge.execute()
            self.undoredo.insertCommand(insertEdge)
            insertVertex = InsertVertex(mev.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertCommand(insertVertex)

        else:
            # case 4: neither of segment's end points belong to the model yet

            # ------------- Insert the init point -------------------

            face_target = self.hemodel.whichFace(_init_point)
            mvr = MVR(_init_point, face_target)
            mvr.execute()
            self.undoredo.insertCommand(mvr)

            # insert the entities into the model data structure
            insertVertex = InsertVertex(mvr.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertCommand(insertVertex)

            # ----- Insert the point 2 and incoming segment -----

            he = mvr.vertex.he
            mev = MEV(_end_point, _segment, mvr.vertex, he.mate().vertex,
                      he.mate().vertex, he.loop.face, he.loop.face)
            mev.execute()
            self.undoredo.insertCommand(mev)

            # inverter the half-edges to keep the consistency with the
            # parametric geometric definition
            flip = Flip(mev.edge)
            flip.execute()
            self.undoredo.insertCommand(flip)

            # insert the entities into the hemodel data structure
            insertEdge = InsertEdge(mev.edge, self.hemodel)
            insertEdge.execute()
            self.undoredo.insertCommand(insertEdge)
            insertVertex = InsertVertex(mev.vertex, self.hemodel)
            insertVertex.execute()
            self.undoredo.insertCommand(insertVertex)

    def delSelectedEntities(self):

        self.undoredo.beginOperation()

        selectedEdges = self.hemodel.selectedEdges()
        selectedVertices = self.hemodel.selectedVertices()

        incidentEdges = []
        for vertex in selectedVertices:
            edges = vertex.incidentEdges()
            incidentEdges.extend(edges)

        selectedEdges.extend(incidentEdges)
        # removes duplicate elements
        selectedEdges = list(set(selectedEdges))
        incidentVertices = []
        for edge in selectedEdges:
            vertices = edge.incidentVertices()
            incidentVertices.extend(vertices)
            self.killEdge(edge)

        selectedVertices.extend(incidentVertices)
        # removes duplicate elements
        selectedVertices = list(set(selectedVertices))

        for vertex in selectedVertices:
            self.killVertex(vertex)

        selectedFaces = self.hemodel.selectedFaces()
        for face in selectedFaces:
            delPatch = DelPatch(face.patch)
            delPatch.execute()
            self.undoredo.insertCommand(delPatch)

        self.undoredo.endOperation()
        self.printDebug()
        self.update()

    def killVertex(self, _vertex):
        he = _vertex.he

        # # case 1: checks if the vertex which will be deleted belongs
        # to a closed segment (in this case the vertex must not be deleted)
        if he.edge is None:
            # case 1.1 : checks if the vertex which will be deleted is the only one (KVFS)
            vertices = _vertex.he.loop.face.shell.vertices
            if len(vertices) == 1:

                face = _vertex.he.loop.face
                shell = face.shell

                # remove vertex and face from model data structure
                removeFace = RemoveFace(face, self.hemodel)
                removeFace.execute()
                self.undoredo.insertCommand(removeFace)
                removeVertex = RemoveVertex(_vertex, self.hemodel)
                removeVertex.execute()
                self.undoredo.insertCommand(removeVertex)
                removeShell = RemoveShell(shell, self.hemodel)
                removeShell.execute()
                self.undoredo.insertCommand(removeShell)

                # remove shell , face and point from half-edge data structure
                kvfs = KVFS(_vertex, face)
                kvfs.execute()
                self.undoredo.insertCommand(kvfs)

            # case 1.2: the vertex which will be deleted is a floating one (KVR)
            else:

                # remove vertex from model data structure
                removeVertex = RemoveVertex(_vertex, self.hemodel)
                removeVertex.execute()
                self.undoredo.insertCommand(removeVertex)

                kvr = KVR(_vertex, he.loop.face)
                kvr.execute()
                self.undoredo.insertCommand(kvr)

    def killEdge(self, _edge):
        # Case 1: checks if it is a closed Edge (in this case, split the edge
        # and delete both segments) (MVSE - KEF - KEV )
        # Case 2: checks if the Edge belongs to a face (its half-edges are
        # in different loops) (KEF)
        # Case 3: checks if both of the Edge's vertexes are incident to more
        #  than one Edge (KEMR)

        he1 = _edge.he1
        he2 = _edge.he2
        # then it's a closed Edge (MVSE - KEF - KEV )
        if he1.vertex == he2.vertex:

            # split the edge (MVSE)
            split_point = _edge.segment.getPoint(0.5)
            seg1, seg2 = _edge.segment.splitSegment(0.5, split_point)
            mvse = self.splitSegment(split_point, _edge, seg1, seg2)

            # the new edges and the new vertex
            new_edge1 = mvse.edge1
            new_edge2 = mvse.edge2
            new_vertex = mvse.vertex

            #  remove the first segment (KEF)
            he1 = new_edge1.he1
            he2 = new_edge1.he2

            # find which of its half-edges belongs to an outter loop
            if he1.loop == he1.loop.face.loop:
                face_to_delete = he1.loop.face
                face_to_keep = he2.loop.face
            else:
                face_to_delete = he2.loop.face
                face_to_keep = he1.loop.face

            # store inner loops
            loop = face_to_delete.loop.next
            inner_loops = []

            while loop is not None:
                inner_loops.append(loop.he.vertex)
                loop = loop.next

            # migrate loops to face_to_keep
            migrateLoops = MigrateLoops(
                face_to_delete, face_to_keep, inner_loops)
            migrateLoops.execute()
            self.undoredo.insertCommand(migrateLoops)

            # checks if it is necessary to invert the half-edges
            if he1.loop.face == face_to_delete:
                # inverter the half-edges to keep the consistency with
                # the parametric geometric definition
                flip = Flip(new_edge1)
                flip.execute()
                self.undoredo.insertCommand(flip)

            # remove face_to_delete from model data structure
            removeFace = RemoveFace(face_to_delete, self.hemodel)
            removeFace.execute()
            self.undoredo.insertCommand(removeFace)
            removeEdge = RemoveEdge(new_edge1, self.hemodel)
            removeEdge.execute()
            self.undoredo.insertCommand(removeEdge)

            kef = KEF(new_edge1, face_to_delete)
            kef.execute()
            self.undoredo.insertCommand(kef)

            # remove vertex and edge from model data structure
            removeVertex = RemoveVertex(new_vertex, self.hemodel)
            removeVertex.execute()
            self.undoredo.insertCommand(removeVertex)
            removeEdge = RemoveEdge(new_edge2, self.hemodel)
            removeEdge.execute()
            self.undoredo.insertCommand(removeEdge)

            # remove the second segment (KEV)
            kev = KEV(new_edge2, new_vertex)
            kev.execute()
            self.undoredo.insertCommand(kev)

        elif he1.loop != he2.loop:  # then it's a KEF

            # find which of its half-edges belongs to an outter loop
            if he1.loop == he1.loop.face.loop:
                face_to_delete = he1.loop.face
                face_to_keep = he2.loop.face
            else:
                face_to_delete = he2.loop.face
                face_to_keep = he1.loop.face

            # store inner loops
            loop = face_to_delete.loop.next
            inner_loops = []

            while loop is not None:
                inner_loops.append(loop.he.vertex)
                loop = loop.next

            # migrate loops to face_to_keep
            migrateLoops = MigrateLoops(
                face_to_delete, face_to_keep, inner_loops)
            migrateLoops.execute()
            self.undoredo.insertCommand(migrateLoops)

            # checks if it is necessary to invert the half-edges
            if he1.loop.face == face_to_delete:
                # inverter the half-edges to keep the consistency with
                # the parametric geometric definition
                flip = Flip(_edge)
                flip.execute()
                self.undoredo.insertCommand(flip)

            # remove face_to_delete from model data structure
            removeFace = RemoveFace(face_to_delete, self.hemodel)
            removeFace.execute()
            self.undoredo.insertCommand(removeFace)
            removeEdge = RemoveEdge(_edge, self.hemodel)
            removeEdge.execute()
            self.undoredo.insertCommand(removeEdge)

            kef = KEF(_edge, face_to_delete)
            kef.execute()
            self.undoredo.insertCommand(kef)

        else:
            # Test whether the edge belongs to the outter loop of its face
            vertex_out = he1.vertex
            # if he1.loop == he1.loop.face.loop:
            if he1.loop == he1.loop.face.loop:
                if self.isLoopCCW(he1.next, he2):
                    vertex_out = he2.vertex

                    # inverter the half-edges to keep the consistency with
                    # the parametric geometric definition
                    flip = Flip(_edge)
                    flip.execute()
                    self.undoredo.insertCommand(flip)

            # remove edge from model data structure
            removeEdge = RemoveEdge(_edge, self.hemodel)
            removeEdge.execute()
            self.undoredo.insertCommand(removeEdge)

            # remove edge from half-edge data structure
            kemr = KEMR(_edge, vertex_out)
            kemr.execute()
            self.undoredo.insertCommand(kemr)

    def getHalfEdge(self, vertex, _tanx, _tany, _normx, _normy, _curvature):

        # get the incident edges of the vertex
        edges = vertex.incidentEdges()

        # case the vertex contains only one edge then returns its half-edge,
        # otherwise returns the half-edge that is most right of the "new edge"
        if len(edges) < 2:
            return vertex.he

        # computes the angle with the horizontal for the "new edge"
        angle_min = 2*CompGeom.PI
        curv_vec_norm_min = 0
        curv_vec_norm_i = 0
        curv_vec_norm_min_first = True
        angleRef = math.atan2(_tany, _tanx)

        if angleRef < 0:
            angleRef += 2*CompGeom.PI

        # find vector normal to given tangent
        ref_norm = Point.normalize(Point(-_tany, _tany))
        curv_vec_ref = Point(_normx*_curvature, _normy*_curvature)
        dotprod_ref = Point.dotprod(curv_vec_ref, ref_norm)

        # loops over the vertex edges to identify the desired half-edge
        he_i = vertex.he

        while True:
            # computes the angle with the horizontal for the "current edge"
            # get the correct tangent

            if he_i == he_i.edge.he1:
                tan = Point.normalize(he_i.edge.segment.tangent(0.0))
                segment_curvature = he_i.edge.segment.curvature(0.0)
                curv_vec_i = Point(-tan.getY() * segment_curvature,
                                   tan.getX() * segment_curvature)
                angle_i = math.atan2(tan.getY(), tan.getX())
            else:
                tan = Point.normalize(he_i.edge.segment.tangent(1.0))
                segment_curvature = he_i.edge.segment.curvature(1.0)
                curv_vec_i = Point(-tan.getY() * segment_curvature,
                                   tan.getX() * segment_curvature)
                angle_i = math.atan2(-tan.getY(), -tan.getX())

            if angle_i < 0:
                angle_i += 2 * CompGeom.PI

            # obtains only positive values from reference edge in ccw
            angle_i = angleRef - angle_i

            if angle_i < 0:
                angle_i = angle_i + 2.0 * CompGeom.PI

            # check if model segment is above incoming
            if angle_i == 0.0 and Point.dotprod(curv_vec_i, ref_norm) > dotprod_ref:
                angle_i = 2.0 * CompGeom.PI

            if angle_i < angle_min:
                angle_min = angle_i
                he_min = he_i
            elif angle_i == angle_min:  # tie break using curvature
                curv_vec_norm_i = Point.dotprod(curv_vec_i, curv_vec_i)

                if curv_vec_norm_min_first:
                    curv_vec_norm_min_first = False
                    curv_vec_norm_min = curv_vec_norm_i
                elif curv_vec_norm_i < curv_vec_norm_min:
                    curv_vec_norm_min = curv_vec_norm_i
                    he_min = he_i

            he_i = he_i.mate().next

            if he_i == vertex.he:
                break

        return he_min

    def intersectModel(self, _segment, _tol):
        incoming_edge_split_map = []
        existent_edges_split_map = []

        # gets the incoming segment bounding box
        xmin, xmax, ymin, ymax = _segment.getBoundBox()

        # -------------------------VERTEX INTERSECTION-------------------------
        # OBS: only floating vertices
        verticesInBound = self.hemodel.verticesCrossingWindow(
            xmin, xmax, ymin, ymax)
        for vertex in verticesInBound:
            if vertex.he.edge is None:
                status, param, pi = _segment.intersectPoint(
                    vertex.point, _tol)
                if status:
                    incoming_edge_split_map.append([param, vertex.point])

        # -------------------------EDGE INTERSECTION---------------------------
        edgesInBound = self.hemodel.edgesCrossingWindow(
            xmin, xmax, ymin, ymax)
        for edge in edgesInBound:
            existent_edge_split_map = []
            segment = edge.segment
            status, pts, existent_params, incoming_params = segment.intersectSegment(
                _segment)

            if status:
                for i in range(0, len(pts)):
                    if abs(existent_params[i]) <= CompGeom.ABSTOL:
                        point = edge.he1.vertex.point
                    elif abs(existent_params[i]-1.0) <= CompGeom.ABSTOL:
                        point = edge.he2.vertex.point
                    else:
                        point = pts[i]
                        # insert at existent params map
                        existent_edge_split_map.append(
                            [existent_params[i], point])

                    # insert in incoming params map
                    incoming_edge_split_map.append(
                        [incoming_params[i], point])

                if len(existent_edge_split_map) > 0:

                    uniqueList = []
                    # remove duplicates
                    for item in existent_edge_split_map:
                        insert = True
                        for unique_item in uniqueList:
                            if abs(item[0]-unique_item[0]) <= _tol:
                                insert = False
                                break

                        if insert:
                            uniqueList.append(item)

                    existent_edge_split_map = uniqueList
                    existent_edge_split_map.sort()

                    existent_edges_split_map.append(
                        [edge, existent_edge_split_map])

        # removes duplicate elements
        uniqueList = []
        for item in incoming_edge_split_map:
            if item not in uniqueList:
                uniqueList.append(item)

        incoming_edge_split_map = uniqueList
        incoming_edge_split_map.sort()

        # try to insert init and end points
        segment_pts = _segment.getPoints()
        if len(incoming_edge_split_map) == 0:
            incoming_edge_split_map.append([0.0, segment_pts[0]])
            incoming_edge_split_map.append([1.0, segment_pts[-1]])
        else:
            if incoming_edge_split_map[0][0] != 0.0:
                incoming_edge_split_map.insert(0, [0.0, segment_pts[0]])
            if incoming_edge_split_map[-1][0] != 1.0:
                incoming_edge_split_map.append([1.0, segment_pts[-1]])

        return incoming_edge_split_map, existent_edges_split_map

    def splitExistingEdges(self, _edges_split_map):

        # split each intersected existent segment and insert its segments
        for edge_split_map in _edges_split_map:
            # geometrically split segments
            split_params = []
            split_pts = []
            existent_edge = edge_split_map[0]
            for split_nodes in edge_split_map[1]:
                split_params.append(split_nodes[0])
                split_pts.append(split_nodes[1])

            segments = existent_edge.segment.split(split_params, split_pts)

            # for each split point, split the segment and insert seg1
            # seg2 will have the correct topology of the splitted existent edge
            # and the geometric information of the splitted existent edge
            # each subsequent call will insert a segment (seg1) which will both
            # have geometric and topological information
            # this loop go as far as there is more than 2 segments remaining

            initial_segment = existent_edge.segment.clone()
            while len(segments) > 2:

                # split the existent segment
                segment1, segment2 = initial_segment.splitSegment(
                    split_params[0], split_pts[0])

                # split the segment
                mvse = self.splitSegment(split_pts[0],
                                         existent_edge, segments[0], segment2)

                # update the next segment to be splitted
                existent_edge = mvse.edge2

                segments.pop(0)
                split_params.pop(0)
                split_pts.pop(0)

            # at this point there are only two segments to be inserted
            # then insert them both at the same time
            mvse = self.splitSegment(split_pts[0], existent_edge,
                                     segments[0], segments[1])

    def joinSegments(self, _edge1, _edge2, _vertex):

        if _edge1.segment.getType() != _edge2.segment.getType():
            return False

        segment1_pts = _edge1.segment.getPoints()
        segment2_pts = _edge2.segment.getPoints()

        if _edge1.segment.getType() == 'LINE':
            if not CompGeom.checkCollinearSegments(segment1_pts[0], segment1_pts[1],
                                                   segment2_pts[0], segment2_pts[1]):
                return False

        joined_pts = []

        if segment1_pts[0] == _vertex.point:
            joined_pts.append(segment1_pts[-1])
        else:
            joined_pts.append(segment1_pts[0])

        if segment2_pts[0] == _vertex.point:
            joined_pts.append(segment2_pts[-1])
        else:
            joined_pts.append(segment2_pts[0])

        if not CompGeom.isCounterClockwisePolygon(joined_pts):
            joined_pts.reverse()

        if _edge1.segment.getType() == 'LINE':
            joined_segment = Line(joined_pts[0], joined_pts[1])

        # remove edges and vertex from model data structure
        removeEdge = RemoveEdge(_edge1, self.hemodel)
        removeEdge.execute()
        self.undoredo.insertCommand(removeEdge)
        removeEdge = RemoveEdge(_edge2, self.hemodel)
        removeEdge.execute()
        self.undoredo.insertCommand(removeEdge)
        removeVertex = RemoveVertex(_vertex, self.hemodel)
        removeVertex.execute()
        self.undoredo.insertCommand(removeVertex)

        kvje = KVJE(joined_segment, _vertex, _edge1, _edge2)
        kvje.execute()
        self.undoredo.insertCommand(kvje)

        # insert the new edge in the model data structure
        insertEdge = InsertEdge(kvje.new_edge, self.hemodel)
        insertEdge.execute()
        self.undoredo.insertCommand(insertEdge)

        return True

    def splitSegment(self, _pt, _split_edge, _seg1, _seg2):

        if _seg1 is None or _seg2 is None:
            print('ERROR: SPLITSEGEMNT')
            if len(self.undoredo.temp) > 0:
                self.undoredo.endOperation()
                self.undo()
                self.undoredo.clearRedo()
            else:
                self.undoredo.endOperation()
            raise Error

        # insert and remove entities in model data structure
        removeEdge = RemoveEdge(_split_edge, self.hemodel)
        removeEdge.execute()
        self.undoredo.insertCommand(removeEdge)

        mvse = MVSE(_pt, _seg1, _seg2, _split_edge)
        mvse.execute()
        self.undoredo.insertCommand(mvse)

        insertVertex = InsertVertex(mvse.vertex, self.hemodel)
        insertVertex.execute()
        self.undoredo.insertCommand(insertVertex)
        insertEdge = InsertEdge(mvse.edge1, self.hemodel)
        insertEdge.execute()
        self.undoredo.insertCommand(insertEdge)
        insertEdge = InsertEdge(mvse.edge2, self.hemodel)
        insertEdge.execute()
        self.undoredo.insertCommand(insertEdge)

        return mvse

    def insertIncomingSegments(self, _segment, _incoming_segment_split_map, _tol):
        # get the splitted segments
        split_params = []
        split_pts = []
        points = []

        for split_nodes in _incoming_segment_split_map:
            split_params.append(split_nodes[0])
            split_pts.append(split_nodes[1])
            points.append(split_nodes[1])

        split_params.pop(0)
        split_params.pop()
        split_pts.pop(0)
        split_pts.pop()

        segments = _segment.split(split_params, split_pts)

        # insert segments in model
        init_point = points.pop(0)

        for seg in segments:

            if seg is None:
                print('ERROR: INSERTSEGMENT')
                if len(self.undoredo.temp) > 0:
                    self.undoredo.endOperation()
                    self.undo()
                    self.undoredo.clearRedo()
                else:
                    self.undoredo.endOperation()
                raise Error

            # get end vertex and increment
            end_point = points.pop(0)

            # The list of vertices of the hemodel is checked, verifying if the
            # init_point and end_point are already exists in the model
            init_vertex = None
            end_vertex = None
            vertices = self.hemodel.shell.vertices
            for vertex in vertices:
                if vertex.point == init_point:
                    init_vertex = vertex
                    init_point = init_vertex.point

                if vertex.point == end_point:
                    end_vertex = vertex
                    end_point = end_vertex.point

            # check if the segment to be inserted already exists in the model
            make_segment = True
            if seg.length(0, 1) <= _tol:
                make_segment = False

            elif init_vertex is not None and end_vertex is not None:
                if init_vertex.he is not None and end_vertex.he is not None:
                    edgesBetween = self.edgesBetween(init_vertex, end_vertex)
                    for edge in edgesBetween:
                        if seg.isEqual(edge.segment, _tol):
                            make_segment = False
                            break

            if make_segment:
                # insert the segment
                self.makeEdge(seg, init_point, end_point)

            # change the initial vertex
            init_point = end_point

    def isSegmentLoopOriented(self, _segment, _he1, _he2):
        he = _he1
        area = 0.0

        while he != _he2:
            if he == he.edge.he1:
                area += he.edge.segment.boundIntegral()
            else:
                area -= he.edge.segment.boundIntegral()

            he = he.next

        area -= _segment.boundIntegral()

        return area >= 0

    def isLoopCCW(self, _he1, _he2):
        area = 0.0
        he = _he1

        while he != _he2:
            if he == he.edge.he1:
                area += he.edge.segment.boundIntegral()
            else:
                area -= he.edge.segment.boundIntegral()

            he = he.next

        return area > CompGeom.ABSTOL

    def findInnerLoops(self, _existent_face, _new_face, _existent_loop):
        loop = _existent_face.loop.next
        inner_loops = []

        while loop is not None:
            if loop != _existent_loop:
                if _new_face.patch.isPointInside(loop.he.vertex.point):
                    inner_loops.append(loop.he.vertex)

            loop = loop.next

        return inner_loops

    def edgesBetween(self, _v1, _v2):
        segments_between = []
        he = _v1.he
        he_begin = he

        # check for floating vertex
        if he.edge is None:
            return segments_between

        while True:
            he = he.mate()
            if he.vertex == _v2:
                segments_between.append(he.edge)

            he = he.next

            if he == he_begin:
                break

        return segments_between

    def createPatch(self):

        self.undoredo.beginOperation()
        segments = []
        edges = self.hemodel.shell.edges
        for edge in edges:
            if edge.segment.isSelected():
                segments.append(edge.segment)

        num_segments = len(segments)
        segments = set(segments)  # transforms the list into a set
        if num_segments == 0:
            return

        faces = self.hemodel.shell.faces
        for i in range(1, len(faces)):
            if faces[i].patch.isDeleted:
                # transforms the list into a set
                patch_segments = set(faces[i].patch.getSegments())
                if len(patch_segments) == num_segments:
                    # makes the intersection between the two sets
                    sets_intersection = segments & patch_segments
                    if len(sets_intersection) == num_segments:
                        createPatch = CreatePatch(faces[i].patch)
                        createPatch.execute()
                        self.undoredo.insertCommand(createPatch)

        self.undoredo.endOperation()

    def undo(self):
        # check whether has redo
        if not self.undoredo.hasUndo():
            return

        # update undo stack
        self.undoredo.undo()

        # undo last operation
        lastOperation = self.undoredo.lastOperation()
        for comand in lastOperation:
            comand.unexecute()

        self.printDebug()
        self.update()

    def redo(self):

        # check whether has redo
        if not self.undoredo.hasRedo():
            return

        # update redo stack
        self.undoredo.redo()

        lastOperation = self.undoredo.lastOperation()
        for i in range(len(lastOperation)-1, -1, -1):
            lastOperation[i].execute()

        self.printDebug()
        self.update()

    def saveFile(self, _filename):
        shell = self.hemodel.shell
        HeFile.saveFile(shell, _filename)

        # renumber he
        self.hemodel.shell.renumberHe()

    def openFile(self, _filename):
        points, segments = HeFile.loadFile(_filename)

        self.undoredo.clear()
        self.hemodel.clearAll()

        for pt in points:
            self.insertPoint(pt, 0.01)

        for segment in segments:
            self.insertSegment(segment, 0.01)

        # renumber he
        self.hemodel.shell.renumberHe()

    def drawHe_entity(self, _entity):
        lines_he = []
        triangles_he = []
        type = _entity.getType()
        checkpoint = 0
        int_points = []

        if type == 'VERTEX':
            he = _entity.he

            if he.edge is None:
                return checkpoint, lines_he, triangles_he, int_points

            orient = (he.edge.he1 == he)
            line_he, tr_he = he.edge.segment.drawHe(0.35, 0.65, orient)
            lines_he.append(line_he)
            triangles_he.append(tr_he)
            return checkpoint, lines_he, triangles_he, int_points

        elif type == 'EDGE':
            line_he1, tr_he1 = _entity.segment.drawHe(0.35, 0.65, True)
            lines_he.append(line_he1)
            triangles_he.append(tr_he1)
            line_he2, tr_he2 = _entity.segment.drawHe(0.35, 0.65, False)
            lines_he.append(line_he2)
            triangles_he.append(tr_he2)
            return checkpoint, lines_he, triangles_he, int_points

        else:
            # its a face
            loop_ext = _entity.loop  # external loop
            he = loop_ext.he
            he_begin = he

            while True:
                if he == he.edge.he1:
                    line_he, tr_he = he.edge.segment.drawHe(0.35, 0.65, True)
                else:
                    line_he, tr_he = he.edge.segment.drawHe(0.35, 0.65, False)

                lines_he.append(line_he)
                triangles_he.append(tr_he)
                checkpoint += 1
                he = he.next

                if he == he_begin:
                    checkpoint -= 1
                    break

            loop_int = loop_ext.next

            while loop_int is not None:
                he = loop_int.he
                he_begin = he
                if he.edge is not None:
                    while True:
                        if he == he.edge.he1:
                            line_he, tr_he = he.edge.segment.drawHe(
                                0.35, 0.65, True)
                        else:
                            line_he, tr_he = he.edge.segment.drawHe(
                                0.35, 0.65, False)

                        lines_he.append(line_he)
                        triangles_he.append(tr_he)
                        he = he.next

                        if he == he_begin:
                            break
                else:
                    int_points.append(he.vertex.point)

                loop_int = loop_int.next

            return checkpoint, lines_he, triangles_he, int_points

    def printDebug(self):

        return

        if self.hemodel.isEmpty():
            print('-------model is empty----------')
            return

        shell = self.hemodel.shell
        face = shell.face

        print('############   DEBUG  ##############')
        # print(f'regioes: {self.model.m_patchs} ')
        while face is not None:
            loop = face.loop
            print(f' ------------------face: {face.ID}------------')
            cont = 1
            while loop is not None:
                he = loop.he
                he_begin = he

                if he is None:
                    loop = loop.next
                    continue

                print(f'------------------loop: {cont}-----------------')
                print(f'LoopisClosed : {loop.isClosed}')
                print(f'Check Face.ID: {loop.face.ID}')
                # if loop.isClosed:
                # print(f'isCCW: {self.isLoopCCW(he.next,he.mate())}')
                while True:
                    print(f'orient {he == he.edge.he1}')
                    point = he.vertex.point
                    print(point.getX(), point.getY())

                    he = he.next

                    if he == he_begin:
                        break

                loop = loop.next
                cont += 1

            face = face.next
