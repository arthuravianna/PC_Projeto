
class Segment:

    # Atributos da classe
    nSdv = 1
    selected = False
    PARAM_TOL = 1e-7
    edge = None

    def getSubdivPoints(self):
        sdvPts = []
        for i in range(0, self.nSdv):
            t = i / self.nSdv
            sdvPts.append(self.getPoint(t))
        return sdvPts

    def getNumberOfPoints(self):
        return self.nPts

    def setNumberOfSubdiv(self, _nSdv):
        self.nSdv = _nSdv

    def getNumberOfSubdiv(self):
        return self.nSdv

    def setSelected(self, _select):
        self.selected = _select

    def isSelected(self):
        return self.selected

    def getBoundBox(self):
        return self.getBoundBox()
