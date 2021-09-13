class MyPoint:

    def __init__(self,_x=0,_y=0):
        self.m_x = _x
        self.m_y = _y
    def setX(self,_x):
        self.m_x = _x
    def setY(self,_y):
        self.m_y = _y
    def getX(self):
        return self.m_x
    def getY(self):
        return self.m_y

class MyCurve:

    def __init__(self,_p1=None,_p2=None):
        self.m_p1 = _p1
        self.m_p2 = _p2
    def setP1(self,_p1):
        self.m_p1 = _p1
    def setP2(self,_p2):
        self.m_p2 = _p2
    def getP1(self):
        return self.m_p1
    def getP2(self):
        return self.m_p2

class MyModel:

    def __init__(self):
        self.m_verts = []
        self.m_curves = []

        # Adicionado para o Projeto
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        self.nx = None
        self.ny = None

        self.h = None
        self.k = None

        self.grid = None

    def set_grid_info(self, x_min, x_max, y_min, y_max, nx, ny, patches=None):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        self.nx = nx
        self.ny = ny

        x_dist = self.x_max - self.x_min # distancia em x
        y_dist = self.y_max - self.y_min # distancia em y

        self.h = x_dist / float(self.nx-1) # espacamento horizontal entre os pontos
        self.k = y_dist / float(self.ny-1) # espacamento vertical entre os pontos

        self.grid = [0 for x in range(self.nx*self.ny)]

        if patches is not None: self.mark_points_inside_patches(patches)
    
    def has_point_inside_model(self):
        result = False
        for value in self.grid:
            if value != 0:
                result = True
                break
        
        return result

    def calculate_point_value(self, i, j):
        return [self.h*i + self.x_min, self.k*j + self.y_min]
    
    def calculate_point_id(self, i, j):
        return j*self.nx + i + 1

    # recebe patches do h_model e verifica quais pontos do grid estao dentro do modelo
    def mark_points_inside_patches(self, patches):
        points_count = 0
        for i in range(self.nx):
            for j in range(self.ny):
                points_count += 1

                point_id = self.calculate_point_id(i, j)

                if self.grid[point_id - 1] != 0: continue

                p = self.calculate_point_value(i, j)
                for patch in patches:
                    if patch.isPointInside(MyPoint(p[0], p[1])):
                        self.grid[point_id - 1] = points_count
                        break
    
    def check_point_connectivity(self, i, j):
        if self.grid is None:
            print("Erro MyModel: Grid nao inicializado")
            return
        
        top_id = self.calculate_point_id(i, j+1)
        bottom_id = self.calculate_point_id(i, j-1)
        left_id = self.calculate_point_id(i-1, j)
        right_id = self.calculate_point_id(i+1, j)

        return [self.grid[top_id-1], self.grid[bottom_id-1], self.grid[left_id-1], self.grid[right_id-1]]







    def setVerts(self,_x,_y):
        self.m_verts.append(MyPoint(_x,_y))
    def getVerts(self):
        return self.m_verts
    def setCurve(self,_x1,_y1,_x2,_y2):
        self.m_curves.append(MyCurve(MyPoint(_x1,_y1),MyPoint(_x2,_y2)))
    def getCurves(self):
        return self.m_curves
    def isEmpty(self):
        return (len(self.m_verts) == 0) and (len(self.m_curves) == 0)
    def getBoundBox(self):
        if (len(self.m_verts) < 1) and (len(self.m_curves) < 1):
            return 0.0,10.0,0.0,10.0
        if len(self.m_verts) > 0:
            xmin = self.m_verts[0].getX()
            xmax = xmin
            ymin = self.m_verts[0].getY()
            ymax = ymin
            for i in range(1,len(self.m_verts)):
                if self.m_verts[i].getX() < xmin:
                    xmin = self.m_verts[i].getX()
                if self.m_verts[i].getX() > xmax:
                    xmax = self.m_verts[i].getX()
                if self.m_verts[i].getY() < ymin:
                    ymin = self.m_verts[i].getY()
                if self.m_verts[i].getY() > ymax:
                    ymax = self.m_verts[i].getY()
        if len(self.m_curves) > 0:
            if len(self.m_verts) == 0:
                xmin = min(self.m_curves[0].getP1().getX(),self.m_curves[0].getP2().getX())
                xmax = max(self.m_curves[0].getP1().getX(),self.m_curves[0].getP2().getX())
                ymin = min(self.m_curves[0].getP1().getY(),self.m_curves[0].getP2().getY())
                ymax = max(self.m_curves[0].getP1().getY(),self.m_curves[0].getP2().getY())
            for i in range(1,len(self.m_curves)):
                temp_xmin = min(self.m_curves[i].getP1().getX(),self.m_curves[i].getP2().getX())
                temp_xmax = max(self.m_curves[i].getP1().getX(),self.m_curves[i].getP2().getX())
                temp_ymin = min(self.m_curves[i].getP1().getY(),self.m_curves[i].getP2().getY())
                temp_ymax = max(self.m_curves[i].getP1().getY(),self.m_curves[i].getP2().getY())
                if temp_xmin < xmin:
                    xmin = temp_xmin
                if temp_xmax > xmax:
                    xmax = temp_xmax
                if temp_ymin < ymin:
                    ymin = temp_ymin
                if temp_ymax > ymax:
                    ymax = temp_ymax
        return xmin,xmax,ymin,ymax
        

'''
m_p1.getY(),self.m_p2.getX(),self.m_p2.getY()

class MyModel:

    def __init__(self):
        self.m_verts = []
        self.m_curves = []
    def setVerts(self,_x,_y):
        self.m_verts.append(MyPoint(_x,y))
    def setCurve(self,_x1,_y1,_x2,_y2):
        self.m_verts.append(MyCurve(_x1,_y1,_x2,_y2))
    def getVerts(self):
        return self.m_verts
    def getCurves(self):
        return self.m_curves
    def isEmpty(self):
        return (len(self.m_verts) == 0) and (len(self.m_curves) == 0)
    def getBoundBox(self):
        print("getBoundBox")
        if (len(self.m_verts) < 1) and (len(self.m_curves) < 1):
            print("vazia")
            return 0.0,10.0,0.0,10.0
        if len(self.m_verts) > 0:
            xmin = self.m_verts[0].getX()
            xmax = xmin
            ymin = self.m_verts[0].getY()
            ymax = ymin
            for i in range(1,len(self.m_verts)):
                if self.m_verts[i].getX() < xmin:
                    xmin = self.m_verts[i].getX()
                if self.m_verts[i].getX() > xmax:
                    xmax = self.m_verts[i].getX()
                if self.m_verts[i].getY() < ymin:
                    ymin = self.m_verts[i].getY()
                if self.m_verts[i].getY() > ymax:
                    ymax = self.m_verts[i].getY()
        if len(self.m_curves) > 0:
            if len(self.m_verts) == 0:
                xmin = self.m_curves[0].getX()
                xmax = xmin
                ymin = self.m_verts[0].getY()
                ymax = ymin
            for i in range(1,len(self.m_curves)):
                if self.m_verts[i].getX() < xmin:
                    xmin = self.m_verts[i].getX()
                if self.m_verts[i].getX() > xmax:
                    xmax = self.m_verts[i].getX()
                if self.m_verts[i].getY() < ymin:
                    ymin = self.m_verts[i].getY()
                if self.m_verts[i].getY() > ymax:
                    ymax = self.m_verts[i].getY()
        return xmin,xmax,ymin,ymax
        

'''