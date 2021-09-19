import json

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
        self.selected_points = None

    def set_grid_info(self, x_min, x_max, y_min, y_max, h, k, patches=None):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max

        #self.nx = nx
        #self.ny = ny

        #x_dist = self.x_max - self.x_min # distancia em x
        #y_dist = self.y_max - self.y_min # distancia em y

        #self.h = x_dist / float(self.nx-1) # espacamento horizontal entre os pontos
        #self.k = y_dist / float(self.ny-1) # espacamento vertical entre os pontos

        self.h = h
        self.k = k

        #self.grid = [0 for x in range(self.nx*self.ny)]
        self.nx = 0
        self.ny = 0
        point_x = self.x_min
        while point_x <= self.x_max:
            self.nx += 1
            point_x += h

        point_y = self.y_min
        while point_y <= self.y_max:
            self.ny += 1
            point_y += k
        
        self.grid = [0 for x in range(self.nx*self.ny)]

        print(self.grid)
        print(self.nx, self.ny)
        self.selected_points = {}

        if patches is not None: self.mark_points_inside_patches(patches)
    '''
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
        self.selected_points = {}

        if patches is not None: self.mark_points_inside_patches(patches)
    '''    
    def clear_model(self):
        self.x_min = None
        self.x_max = None
        self.y_min = None
        self.y_max = None

        self.nx = None
        self.ny = None

        self.h = None
        self.k = None

        self.grid = None
        self.selected_points = None
    
    def has_point_inside_model(self):
        result = False
        for value in self.grid:
            if value != 0:
                result = True
                break
        
        return result

    # recebe patches do h_model e verifica quais pontos do grid estao dentro do modelo
    def mark_points_inside_patches(self, patches):
        points_count = 0
        for j in range(self.ny): # linha do grid
            for i in range(self.nx): # coluna do grid

                point_id = self.calculate_point_id(i, j)

                #if self.grid[point_id - 1] != 0: continue

                p = self.calculate_point_value(i, j)
                p1 = MyPoint(p[0]+self.h/2, p[1])
                p2 = MyPoint(p[0]-self.h/2, p[1])
                p3 = MyPoint(p[0], p[1]+self.k/2)
                p4 = MyPoint(p[0], p[1]-self.k/2)
                for patch in patches:
                    if patch.isPointInside(p1) and patch.isPointInside(p2) and patch.isPointInside(p3) and patch.isPointInside(p4):
                    #if patch.isPointInside(MyPoint(p[0], p[1])):
                        points_count += 1
                        self.grid[point_id - 1] = points_count
                        break
        
        print("GRID: ", self.grid)

    def calculate_point_value(self, i, j):

        return [self.h*i + self.x_min, self.k*j + self.y_min]
    
    def calculate_point_id(self, i, j):
        return j*self.nx + i + 1

    def check_point_connectivity(self, i, j):
        if self.grid is None:
            print("Erro MyModel: Grid nao inicializado")
            return
        
        top_id = self.calculate_point_id(i, j+1)
        bottom_id = self.calculate_point_id(i, j-1)
        left_id = self.calculate_point_id(i-1, j)
        right_id = self.calculate_point_id(i+1, j)

        res = [self.grid[right_id-1], self.grid[left_id-1], self.grid[bottom_id-1], self.grid[top_id-1]]
        return res
    
    def check_selected_points(self, pt0_U, pt1_U):
        x_min = min(pt0_U.x(), pt1_U.x())
        y_min = min(pt0_U.y(), pt1_U.y())
        x_max = max(pt0_U.x(), pt1_U.x())
        y_max = max(pt0_U.y(), pt1_U.y())

        for j in range(self.ny):
            for i in range(self.nx):
                point_id = self.calculate_point_id(i, j)

                if self.grid[point_id - 1] == 0: continue # ponto fora do modelo

                pt = self.calculate_point_value(i, j)

                if x_max > pt[0] > x_min and y_max > pt[1] > y_min:
                    self.selected_points[str(point_id)] = None
        
        print("SELECTED POINTS: ", self.selected_points)


    def set_pvc(self, value):
        if self.selected_points is None:
            print("ERRO MyModel: Antes de setar o PVC eh preciso gerar um grid e selecionar os pontos")
            return
        
        if len(self.selected_points) == 0:
            print("ERRO MyModel: Antes de setar o PVC eh preciso selecionar os pontos do grid")
            return

        for k,v in self.selected_points.items():
            if v is None: self.selected_points[k] = value

        print("SET SELECTED POINTS: ", self.selected_points)

    def save_model(self, filename):
        data = {}
        data["h"] = self.h
        data["k"] = self.k

        data["nx"] = self.nx
        data["ny"] = self.ny

        data["cc"] = []
        data["connect"] = []

        for j in range(self.ny):
            for i in range(self.nx):
                point_id = self.calculate_point_id(i, j)

                if self.grid[point_id - 1] == 0: continue # ponto fora do modelo

                if str(point_id) in self.selected_points:
                    value = self.selected_points[str(point_id)]
                    if value is None:
                        print("ERRO MyModel: Defina o valor da Condicao de Contorno!!!")
                        return

                    data["cc"].append((1, value))
                else:
                    data["cc"].append((0, 0))

                data["connect"].append(self.check_point_connectivity(i, j))

        print(data["cc"])
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)






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