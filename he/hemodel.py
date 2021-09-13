from compgeom.compgeom import CompGeom
from geometry.point import Point
from geometry.segments.polyline import Polyline
import math


class HeModel:

    def __init__(self):
        self.shell = None
        self.infinityFace = None
        self.select_segment = True
        self.select_point = True
        self.select_patch = True
        self.segments = []
        self.points = []
        self.patches = []
        self.updatesortPatches = False

    def insertShell(self, _shell):
        self.shell = _shell

    def insertVertex(self, _vertex):
        self.shell.insertVertex(_vertex)
        self.points.append(_vertex.point)
        _vertex.point.vertex = _vertex

    def insertEdge(self, _edge):
        self.shell.insertEdge(_edge)
        self.segments.append(_edge.segment)
        _edge.segment.edge = _edge

    def insertFace(self, _face):

        if len(self.shell.faces) == 0:
            self.infinityFace = _face

        self.shell.insertFace(_face)
        _face.patch.face = _face
        self.updatesortPatches = True

    def removeVertex(self, _vertex):
        _vertex.point.vertex = None
        self.shell.removeVertex(_vertex)
        self.points.remove(_vertex.point)

    def removeFace(self, _face):
        if _face == self.infinityFace:
            self.infinityFace = None

        self.shell.removeFace(_face)
        _face.patch.face = None
        self.updatesortPatches = True

    def removeEdge(self, _edge):
        self.shell.removeEdge(_edge)
        self.segments.remove(_edge.segment)
        _edge.segment.edge = None

    def removeShell(self):
        self.shell = None

    def isEmpty(self):
        if self.shell is None:
            return True
        else:
            return False

    def clearAll(self):
        self.shell = None
        self.infinityFace = None
        self.segments = []
        self.points = []
        self.patches = []

    def getPoints(self):
        return self.points

    def getSegments(self):
        return self.segments

    def getPatches(self):

        if self.updatesortPatches:
            self.patches = self.sortPatches()

        return self.patches

    def selectedEdges(self):
        selectedEdges = []

        if self.isEmpty():
            return selectedEdges

        edges = self.shell.edges
        for edge in edges:
            if edge.segment.isSelected():
                selectedEdges.append(edge)

        return selectedEdges

    def selectedVertices(self):

        selectedVertices = []

        if self.isEmpty():
            return selectedVertices

        vertices = self.shell.vertices
        for vertex in vertices:
            if vertex.point.isSelected():
                selectedVertices.append(vertex)

        return selectedVertices

    def selectedFaces(self):

        selectedFaces = []

        if self.isEmpty():
            return selectedFaces

        faces = self.shell.faces
        for face in faces:
            if face.patch.isSelected():
                selectedFaces.append(face)

        return selectedFaces

    def getBoundBox(self):

        if self.isEmpty():
            return 0.0, 10.0, 0.0, 10.0

        points = self.points
        x = points[0].getX()
        y = points[0].getY()

        xmin = x
        ymin = y
        xmax = x
        ymax = y

        for i in range(1, len(points)):
            x = points[i].getX()
            y = points[i].getY()
            xmin = min(x, xmin)
            xmax = max(x, xmax)
            ymin = min(y, ymin)
            ymax = max(y, ymax)

        for segment in self.segments:
            xmin_c, xmax_c, ymin_c, ymax_c = segment.getBoundBox()
            xmin = min(xmin_c, xmin)
            xmax = max(xmax_c, xmax)
            ymin = min(ymin_c, ymin)
            ymax = max(ymax_c, ymax)

        return xmin, xmax, ymin, ymax

    def selectPick(self, _x,  _y,  _tol,  _shiftkey):

        if self.isEmpty():
            return

        # select point
        ispointSelected = False
        id_target = -1
        dmin = _tol
        if self.select_point:
            for i in range(0, len(self.points)):
                dist = Point.euclidiandistance(
                    Point(_x, _y), self.points[i])
                if dist < dmin:
                    dmin = dist
                    id_target = i

            # Revert selection of picked point
            if id_target > -1:
                ispointSelected = True
                if self.points[id_target].isSelected():
                    self.points[id_target].setSelected(False)
                else:
                    self.points[id_target].setSelected(True)

        if not _shiftkey:
            # If shift key is not pressed, unselect all points except
            # the picked one (if there was one selected)
            for i in range(0, len(self.points)):
                if i != id_target:
                    self.points[i].setSelected(False)

        # select segment
        issegmentselected = False
        id_target = -1
        dmin = _tol
        if self.select_segment and not ispointSelected:
            for i in range(0, len(self.segments)):
                # Compute distance between given point and segment and
                # update minimum distance
                xC, yC, d = self.segments[i].closestPoint(_x, _y)
                if d < dmin:
                    dmin = d
                    id_target = i

            # Revert selection of picked segment
            if id_target > -1:
                issegmentselected = True
                if self.segments[id_target].isSelected():
                    self.segments[id_target].setSelected(False)
                else:
                    self.segments[id_target].setSelected(True)

        if not _shiftkey:
            # If shift key is not pressed, unselect all segments except
            # the picked one (if there was one selected)
            for i in range(0, len(self.segments)):
                if i != id_target:
                    self.segments[i].setSelected(False)

        if self.select_patch and not ispointSelected and not issegmentselected:
            # Check whether point is inside a patch
            p = Point(_x, _y)
            for i in range(0, len(self.patches)):
                if not self.patches[i].isDeleted:
                    if self.patches[i].isPointInside(p):
                        if self.patches[i].isSelected():
                            self.patches[i].setSelected(False)
                        else:
                            self.patches[i].setSelected(True)
                    else:
                        if not _shiftkey:
                            self.patches[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(self.patches)):
                self.patches[i].setSelected(False)

    def selectFence(self, _xmin, _xmax, _ymin, _ymax, _shiftkey):

        if self.isEmpty():
            return

        if self.select_segment:
            # select segments
            for i in range(0, len(self.segments)):
                xmin_c, xmax_c, ymin_c, ymax_c = self.segments[i].getBoundBox(
                )
                if ((xmin_c < _xmin) or (xmax_c > _xmax) or
                        (ymin_c < _ymin) or (ymax_c > _ymax)):
                    inFence = False
                else:
                    inFence = True

                if inFence:
                    # Select segment inside fence
                    self.segments[i].setSelected(True)
                else:
                    if not _shiftkey:
                        self.segments[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(self.segments)):
                self.segments[i].setSelected(False)

        if self.select_point:
            # select points
            for i in range(0, len(self.points)):
                x = self.points[i].getX()
                y = self.points[i].getY()

                if ((x < _xmin) or (x > _xmax) or
                        (y < _ymin) or (y > _ymax)):
                    inFence = False
                else:
                    inFence = True

                if inFence:
                    # Select segment inside fence
                    self.points[i].setSelected(True)
                else:
                    if not _shiftkey:
                        self.points[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(self.points)):
                self.points[i].setSelected(False)

        if self.select_patch:
            # select patches
            for i in range(0, len(self.patches)):
                if not self.patches[i].isDeleted:
                    xmin_r, xmax_r, ymin_r, ymax_r = self.patches[i].getBoundBox(
                    )
                    if((xmin_r < _xmin) or (xmax_r > _xmax) or
                            (ymin_r < _ymin) or (ymax_r > _ymax)):
                        inFence = False
                    else:
                        inFence = True

                    if inFence:
                        # Select patch inside fence
                        self.patches[i].setSelected(True)
                    else:
                        # If shift key is not pressed, unselect patch outside fence
                        if not _shiftkey:
                            self.patches[i].setSelected(False)
        elif not _shiftkey:
            for i in range(0, len(self.patches)):
                self.patches[i].setSelected(False)

    def snapToSegment(self, _x, _y, _tol):

        if self.isEmpty():
            return False, _x, _y

        xClst = _x
        yClst = _y
        id_target = -1
        dmin = _tol

        for i in range(0, len(self.segments)):
            xC, yC, dist = self.segments[i].closestPoint(_x, _y)
            if dist < dmin:
                xClst = xC
                yClst = yC
                dmin = dist
                id_target = i

        if id_target < 0:
            return False, xClst, yClst

        # try to attract to a corner of the segment
        seg_pts = self.segments[id_target].getPoints()

        dmin = _tol*2
        for pt in seg_pts:
            pt_x = pt.getX()
            pt_y = pt.getY()
            d = math.sqrt((_x-pt_x)*(_x-pt_x)+(_y-pt_y)*(_y-pt_y))

            if d < dmin:
                xClst = pt_x
                yClst = pt_y
                dmin = d

        # If found a closest point, return its coordinates
        return True, xClst, yClst

    def snapToPoint(self, _x, _y, _tol):
        if self.isEmpty():
            return False, _x, _y

        xClst = _x
        yClst = _y
        id_target = -1
        dmin = _tol

        for i in range(0, len(self.points)):
            xC = self.points[i].getX()
            yC = self.points[i].getY()
            if (abs(_x - xC) < _tol) and (abs(_y - yC) < _tol):
                d = math.sqrt((_x-xC)*(_x-xC)+(_y-yC)*(_y-yC))
                if d < dmin:
                    xClst = xC
                    yClst = yC
                    dmin = d
                    id_target = i

        if id_target < 0:
            return False, xClst, yClst

        # If found a closest point, return its coordinates
        return True, xClst, yClst

    def verticesCrossingWindow(self, _xmin, _xmax, _ymin, _ymax):
        vertices = []
        # search the points that are contained in the given rectangle
        vertices_list = self.shell.vertices
        for vertex in vertices_list:
            if _xmin <= vertex.point.getX() and _xmax >= vertex.point.getX():
                if _ymin <= vertex.point.getY() and _ymax >= vertex.point.getY():
                    # then point is in window
                    vertices.append(vertex)

        vertices = list(set(vertices))

        return vertices

    def edgesInWindow(self, _xmin, _xmax, _ymin, _ymax):

        edges_targets = []

        # search the edges that are contained in the given rectangle
        edges_list = self.shell.edges
        for edge in edges_list:
            edge_segment = edge.segment
            edg_xmin, edg_xmax, edg_ymin, edg_ymax = edge_segment.getBoundBox()

            if _xmin <= edg_xmin and _xmax >= edg_xmax:
                if _ymin <= edg_ymin and _ymax >= edg_ymax:
                    # then the edge is in window
                    edges_targets.append(edge)

        return edges_targets

    def edgesCrossingFence(self, _fence):

        edges_targets = []

        xmin, xmax, ymin, ymax = _fence.getBoundBox()

        # get segments crossing fence's bounding box
        edges_list = self.shell.edges
        for edge in edges_list:
            segment = edge.segment
            segment_xmin, segment_xmax, segment_ymin, segment_ymax = segment.getBoundBox()

            if not (xmax < segment_xmin or segment_xmax < xmin or
                    ymax < segment_ymin or segment_ymax < ymin):
                edges_targets.append(edge)

        # Checks if the segment intersects the _fence
        for edge in edges_targets:
            status, pi, param1, param2 = _fence.intersectSegment(edge.segment)

            # If it does not, remove the edge from edgesInFence and go to next edge
            if not status:
                edges_targets.remove(edge)

        return edges_targets

    def edgesCrossingWindow(self, _xmin, _xmax, _ymin, _ymax):
        pts = []

        if _ymin == _ymax or _xmin == _xmax:
            pts.append(Point(_xmin, _ymin))
            pts.append(Point(_xmax, _ymax))
        else:
            # create a retangular fence
            pts.append(Point(_xmin, _ymin))
            pts.append(Point(_xmax, _ymin))
            pts.append(Point(_xmax, _ymax))
            pts.append(Point(_xmin, _ymax))
            pts.append(Point(_xmin, _ymin))

        fence_segment = Polyline(pts)

        edges = self.edgesInWindow(_xmin, _xmax, _ymin, _ymax)

        edges_crossing = self.edgesCrossingFence(fence_segment)
        edges.extend(edges_crossing)

        edges = list(set(edges))  # remove duplicates

        return edges

    def whichFace(self, _pt):
        face = self.infinityFace.next

        while face is not None:
            if face.patch.isPointInside(_pt):
                return face

            face = face.next

        return self.infinityFace

    def sortPatches(self):
        patchesWithoutHoles = []
        facesWithHoles = []

        # initially the faces are organized in two lists of faces with holes
        #  and patches without holes
        faces = self.shell.faces
        for i in range(1, len(faces)):
            if len(faces[i].patch.holes) > 0:
                facesWithHoles.append(faces[i])
            else:
                patchesWithoutHoles.append(faces[i].patch)

        sort_patches = []

        # From this point on, the list of faces with holes is searched looking
        #  for the outermost face. Then the outermost face is added to the new
        #  list of patches with holes
        while len(facesWithHoles) > 0:
            insert = True
            face_target = facesWithHoles[0]
            for j in range(1, len(facesWithHoles)):
                face_point = face_target.loop.he.vertex.point
                poly = facesWithHoles[j].patch.getPoints()

                if CompGeom.isPointInPolygon(poly, face_point):
                    insert = False
                    break

            if insert:
                sort_patches.append(face_target.patch)
                facesWithHoles.pop(0)
            else:
                facesWithHoles.pop(0)
                facesWithHoles.append(face_target)

        sort_patches.extend(patchesWithoutHoles)

        self.updatesortpatches = False

        return sort_patches
