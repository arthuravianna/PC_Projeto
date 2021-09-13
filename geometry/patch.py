from geometry.point import Point
from compgeom.tesselation import Tesselation


class Patch:

    def __init__(self):
        self.pts = []  # boundary points
        self.segments = []  # vector of boundary segments
        # orientations of segments with respect to counter-clockwise region boundary
        self.segmentOrients = []
        self.mesh = None
        self.selected = False
        self.holes = []  # vector of region holes
        self.holesOrients = []
        self.isDeleted = False
        self.face = None

    def __del__(self):
        if self.mesh:
            del self.mesh

    def getPoints(self):
        return self.pts

    def getSegments(self):
        return self.segments

    def getSegmentOrients(self):
        return self.segmentOrients

    def setSelected(self, _select):
        self.selected = _select

    def isSelected(self):
        return self.selected

    def setMesh(self, _mesh):
        self.mesh = _mesh

    def getMesh(self):
        return self.mesh

    def getBoundBox(self):

        if len(self.pts) == 0:
            return

        xmin = self.pts[0].getX()
        ymin = self.pts[0].getY()
        xmax = self.pts[0].getX()
        ymax = self.pts[0].getY()

        if len(self.pts) == 1:
            return

        for j in range(1, len(self.pts)):
            xmin = min(xmin, self.pts[j].getX())
            xmax = max(xmax, self.pts[j].getX())
            ymin = min(ymin, self.pts[j].getY())
            ymax = max(ymax, self.pts[j].getY())

        return xmin, xmax, ymin, ymax

    def getSegmentsdvs(self):
        loop = []
        loops = []
        for i in range(0, len(self.segments)):
            nsegmentsdv = self.segments[i].getNumberOfSubdiv()
            loop.append(nsegmentsdv)

        loops.append(loop)
        return loops

    def getSegmentsdvPts(self):
        bound = []
        for i in range(0, len(self.segments)):
            segmentPts = self.segments[i].getSubdivPoints()
            if self.segmentOrients[i]:
                for j in range(0, len(segmentPts)-1):
                    bound.append(segmentPts[j])
            else:
                for j in range(len(segmentPts)-1, 0, -1):
                    bound.append(segmentPts[j])

        return bound

    def delMesh(self):
        if self.mesh is not None:
            del self.mesh
            self.mesh = None

    def setBoundary(self, _boundarysegments, _isOriented):
        self.segments = _boundarysegments.copy()
        self.segmentOrients = _isOriented.copy()
        self.pts = self.boundaryPolygon()

    def setHoles(self, _holessegments, _isOriented):
        self.holes = _holessegments
        self.holesOrients = _isOriented

    def isPointInside(self, _pt):
        numIntersec = 0
        for i in range(0, len(self.segments)):
            numIntersec += self.segments[i].ray(_pt)

        if numIntersec % 2 != 0:
            for i in range(0, len(self.holes)):
                numIntersec = 0
                for j in range(0, len(self.holes[i])):
                    numIntersec += self.holes[i][j].ray(_pt)

                if numIntersec % 2 != 0:
                    return False

            return True

        else:
            return False

    def boundaryPolygon(self):
        polygon = []
        for i in range(0, len(self.segments)):
            segmentPol = self.segments[i].eqPolyline(1e-3)
            if self.segmentOrients[i]:
                for j in range(0, len(segmentPol)-1):
                    polygon.append(segmentPol[j])
            else:
                for j in range(len(segmentPol)-1, 0, -1):
                    polygon.append(segmentPol[j])

        return polygon

    def boundaryHole(self):
        polygons = []

        for i in range(0, len(self.holes)):
            polygon = []
            for j in range(0, len(self.holes[i])):
                segmentpol = self.holes[i][j].eqPolyline(1e-3)
                if self.holesOrients[i][j]:
                    for m in range(0, len(segmentpol)-1):
                        polygon.append(segmentpol[m])
                else:
                    for m in range(len(segmentpol)-1, 0, -1):
                        polygon.append(segmentpol[m])

            polygon.reverse()
            polygons.append(polygon)

        return polygons

    def Area(self):
        Area = 0
        pts = self.pts
        triangs = Tesselation.triangleParing(pts)
        for j in range(0, len(triangs)):
            a = Point(pts[triangs[j][0]].getX(),
                      pts[triangs[j][0]].getY())
            b = Point(pts[triangs[j][1]].getX(),
                      pts[triangs[j][1]].getY())
            c = Point(pts[triangs[j][2]].getX(),
                      pts[triangs[j][2]].getY())

            Area += (a.getX()*b.getY() - a.getY()*b.getX()
                     + a.getY()*c.getX() - a.getX()*c.getY()
                     + b.getX()*c.getY() - c.getX()*b.getY()) / 2.0

        pts_holes = self.boundaryHole()

        for pts_hole in pts_holes:
            triangs = Tesselation.triangleParing(pts_hole)
            for j in range(0, len(triangs)):
                a = Point(pts_hole[triangs[j][0]].getX(),
                          pts_hole[triangs[j][0]].getY())
                b = Point(pts_hole[triangs[j][1]].getX(),
                          pts_hole[triangs[j][1]].getY())
                c = Point(pts_hole[triangs[j][2]].getX(),
                          pts_hole[triangs[j][2]].getY())

                Area -= (a.getX()*b.getY() - a.getY()*b.getX()
                         + a.getY()*c.getX() - a.getX()*c.getY()
                         + b.getX()*c.getY() - c.getX()*b.getY()) / 2.0

        return Area
