from threading import Event
from PyQt5 import QtOpenGL, QtCore
from PyQt5.QtWidgets import *
from OpenGL.GL import *

from he.hecontroller import HeController
from he.hemodel import HeModel
from geometry.segments.line import Line
from geometry.point import Point
from compgeom.tesselation import Tesselation
from math import *

from mymodel import MyModel

class MyCanvas(QtOpenGL.QGLWidget):

    def __init__(self):
        super(MyCanvas, self).__init__()
        self.m_model = None
        self.m_w = 0 # width: GL canvas horizontal size
        self.m_h = 0 # height: GL canvas vertical size
        self.m_L = -1000.0
        self.m_R = 1000.0
        self.m_B = -1000.0
        self.m_T = 1000.0
        self.list = None
        self.m_buttonPressed = False
        self.m_pt0 = QtCore.QPoint(0.0,0.0)
        self.m_pt1 = QtCore.QPoint(0.0,0.0)

        self.m_hmodel = HeModel()
        self.m_controller = HeController(self.m_hmodel)

        self.fence = False

    def initializeGL(self):
        #glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        # enable smooth line display
        glEnable(GL_LINE_SMOOTH)
        self.list = glGenLists(1)

    def resizeGL(self, _width, _height):
        # store GL canvas sizes in object properties
        self.m_w = _width
        self.m_h = _height
        # Setup world space window limits based on model bounding box
        if (self.m_model == None) or (self.m_model.isEmpty()):
            self.scaleWorldWindow(1.0)
        else:
           self.m_L, self.m_R, self.m_B, self.m_T = self.m_model.getBoundBox()
           self.scaleWorldWindow(1.1)
        # setup the viewport to canvas dimensions
        glViewport(0, 0, self.m_w, self.m_h)
        # reset the coordinate system
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # establish the clipping volume by setting up an
        # orthographic projection
        #glOrtho(0.0, self.m_w, 0.0, self.m_h, -1.0, 1.0)
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        # setup display in model coordinates
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        # clear the buffer with the current clear color
        glClear(GL_COLOR_BUFFER_BIT)
        # draw a triangle with RGB color at the 3 vertices
        # interpolating smoothly the color in the interior
        glCallList(self.list)
        glDeleteLists(self.list, 1)
        self.list = glGenLists(1)
        glNewList(self.list, GL_COMPILE)
        # Display model polygon RGB color at its vertices
        # interpolating smoothly the color in the interior
        #glShadeModel(GL_SMOOTH)

        if not((self.m_model == None) and (self.m_model.isEmpty())):
            pass
            '''
            verts = self.m_model.getVerts()
            glColor3f(0.0, 1.0, 0.0) # green
            glBegin(GL_TRIANGLES)
            for vtx in verts:
                glVertex2f(vtx.getX(), vtx.getY())
            glEnd()
            curves = self.m_model.getCurves()
            glColor3f(0.0, 0.0, 1.0) # blue
            glBegin(GL_LINES)
            for curv in curves:
                glVertex2f(curv.getP1().getX(), curv.getP1().getY())
                glVertex2f(curv.getP2().getX(), curv.getP2().getY())
            glEnd()
            '''

        if not(self.m_hmodel.isEmpty()):
            #print("teste")
            patches = self.m_hmodel.getPatches()
            for pat in patches:
                pts = pat.getPoints()
                triangs = Tesselation.tessellate(pts)
                for j in range(0, len(triangs)):
                    glColor3f(1.0, 0.0, 1.0) # 
                    glBegin(GL_TRIANGLES)
                    glVertex2d(pts[triangs[j][0]].getX(),pts[triangs[j][0]].getY())
                    glVertex2d(pts[triangs[j][1]].getX(),pts[triangs[j][1]].getY())
                    glVertex2d(pts[triangs[j][2]].getX(),pts[triangs[j][2]].getY())
                    glEnd()

            segments = self.m_hmodel.getSegments()
            for curv in segments:
                ptc = curv.getPointsToDraw()
                glColor3f(0.0, 1.0, 1.0) # 
                glBegin(GL_LINES)
                #for curv in curves:
                glVertex2f(ptc[0].getX(), ptc[0].getY())
                glVertex2f(ptc[1].getX(), ptc[1].getY())
                glEnd()
        
        if self.m_model.grid is not None:
            for j in range(self.m_model.ny): # linha do grid
                for i in range(self.m_model.nx): # coluna do grid
                    glColor3f(0.0,1.0,0.0)
                    glPointSize(2.0)

                    point_id = self.m_model.calculate_point_id(i, j)

                    p = self.m_model.calculate_point_value(i, j)

                    if self.m_model.grid[point_id - 1] == 0: continue # o ponto nao esta dentro do modelo
                    #print(point_id, p)
                    # desenha o ponto
                    glBegin(GL_POINTS)
                    glVertex2f(p[0], p[1])
                    glEnd()

                    # desenha o ponto que esta dentro da cerca
                    if str(point_id) in self.m_model.selected_points:
                        glColor3f(1.0,0.0,0.0)
                        glPointSize(3.0)
                        glBegin(GL_POINTS)
                        glVertex2f(p[0], p[1])
                        glEnd()

                    # desenha a particula(circulo)
                    glBegin(GL_LINE_LOOP)
                    for angulo in range(0, 360, 2):
                        radiano = (angulo * pi) / 180
                        glVertex2f(p[0] + self.m_model.h/2 * cos(radiano), p[1] + self.m_model.k/2 * sin(radiano))
                    glEnd()

            #self.m_model.clear_grid_info()

        pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
        pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)
        
        if(self.fence):
            glColor3f(0.0,0.0,1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(pt0_U.x(), pt0_U.y())
            glVertex2f(pt1_U.x(), pt0_U.y())
            glVertex2f(pt1_U.x(), pt1_U.y())
            glVertex2f(pt0_U.x(), pt1_U.y())
            glEnd()
        else:        
            glColor3f(1.0, 0.0, 0.0)
            glBegin(GL_LINE_STRIP)
            glVertex2f(pt0_U.x(), pt0_U.y())
            glVertex2f(pt1_U.x(), pt1_U.y())
            glEnd()

        glEndList()

    def convertPtCoordsToUniverse(self, _pt):
        dX = self.m_R - self.m_L
        dY = self.m_T - self.m_B
        mX = _pt.x() * dX / self.m_w
        mY = (self.m_h - _pt.y()) * dY / self.m_h
        x = self.m_L + mX
        y = self.m_B + mY
        return QtCore.QPointF(x,y)

    def mousePressEvent(self, event):
        if(event.button() == 1):
            self.m_buttonPressed = True

        elif(event.button() == 2):
            self.fence = True
            #self.m_model.selected_points = {} #reset vetor pontos

        self.m_pt0 = event.pos()
        self.m_pt1 = self.m_pt0

    def mouseMoveEvent(self, event):
        if self.m_buttonPressed or self.fence:
            self.m_pt1 = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        pt0_U = self.convertPtCoordsToUniverse(self.m_pt0)
        pt1_U = self.convertPtCoordsToUniverse(self.m_pt1)

        if pt0_U == pt1_U: return
        
        if event.button() == 1:
            #self.m_model.setCurve(pt0_U.x(),pt0_U.y(),pt1_U.x(),pt1_U.y())

            p0 = Point(pt0_U.x(),pt0_U.y())
            p1 = Point(pt1_U.x(),pt1_U.y())
            segment = Line(p0,p1)
            self.m_controller.insertSegment(segment,0.01)

            self.update()
            self.repaint()

            #self.m_model.setCurve(self.m_pt0.x(),self.m_pt0.y(),self.m_pt1.x(),self.m_pt1.y())
            self.m_buttonPressed = False
            self.m_pt0.setX(0.0)
            self.m_pt0.setY(0.0)
            self.m_pt1.setX(0.0)
            self.m_pt1.setY(0.0)

            self.update()
            self.repaint()

        elif event.button() == 2:
            self.m_model.check_selected_points(pt0_U, pt1_U)

            self.m_pt0.setX(0.0)
            self.m_pt0.setY(0.0)
            self.m_pt1.setX(0.0)
            self.m_pt1.setY(0.0)
            
            self.update()
            self.repaint()
            self.fence = False

    def setModel(self,_model):
        self.m_model = _model

    def fitWorldToViewport(self):
        if self.m_hmodel == None:
            return
        self.m_L, self.m_R, self.m_B, self.m_T = self.m_hmodel.getBoundBox()
        self.scaleWorldWindow(1.10)
        self.update()

    def scaleWorldWindow(self,_scaleFac):
        # Compute canvas viewport distortion ratio.
        vpr = self.m_h / self.m_w
        # Get current window center.
        #/*** COMPLETE HERE - GLCANVAS: 01 ***/
        cx = (self.m_L + self.m_R) / 2.0
        cy = (self.m_B + self.m_T) / 2.0
        #/*** COMPLETE HERE - GLCANVAS: 01 ***/
        # Set new window sizes based on scaling factor.
        #/*** COMPLETE HERE - GLCANVAS: 02 ***/
        sizex = (self.m_R - self.m_L) * _scaleFac
        sizey = (self.m_T - self.m_B) * _scaleFac
        #/*** COMPLETE HERE - GLCANVAS: 02 ***/
        # Adjust window to keep the same aspect ratio of the viewport.
        #/*** COMPLETE HERE - GLCANVAS: 03 ***/
        if sizey > (vpr*sizex):
            sizex = sizey / vpr
        else:
            sizey = sizex * vpr
        self.m_L = cx - (sizex * 0.5)
        self.m_R = cx + (sizex * 0.5)
        self.m_B = cy - (sizey * 0.5)
        self.m_T = cy + (sizey * 0.5)
        #/*** COMPLETE HERE - GLCANVAS: 03 ***/
        # Establish the clipping volume by setting up an
        # orthographic projection
        glMatrixMode(GL_PROJECTION) 
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        
    def panWorldWindow(self, _panFacX, _panFacY):
        # Compute pan distances in horizontal and vertical directions.
        panX = (self.m_R - self.m_L) * _panFacX
        panY = (self.m_T - self.m_B) * _panFacY
        # Shift current window.
        self.m_L += panX
        self.m_R += panX
        self.m_B += panY
        self.m_T += panY
        # Establish the clipping volume by setting up an
        # orthographic projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)

        self.update()


    def generateGrid(self, h, k):
        xmin, xmax, ymin, ymax = self.m_hmodel.getBoundBox()

        self.m_model.set_grid_info(xmin, xmax, ymin, ymax, h, k, self.m_hmodel.patches)

        if not self.m_model.has_point_inside_model():
            print("Nenhum ponto do grid está dentro do domínio!!!")
            return

        self.update()
        self.repaint()
    
    def clear_hmodel(self):
        self.m_hmodel.clearAll()

        self.update()
        self.repaint()        
