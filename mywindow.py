from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from mycanvas import *
from mymodel import *

# Globals
GRID = 0
GRID_ICON = "icons/grid.png"

class MyWindow(QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(100,100,600,400)
        self.setWindowTitle("MyGLDrawer")
        self.canvas = MyCanvas()
        self.setCentralWidget(self.canvas)
        # create a model object and pass it to canvas object
        self.model = MyModel()
        self.canvas.setModel(self.model)
        # create a Toolbar
        tb = self.addToolBar("File")

        fit = QAction(QIcon("icons/fit.jpg"),"fit",self)
        tb.addAction(fit)

        panR = QAction(QIcon("icons/panright.jpg"),"panR",self)
        tb.addAction(panR)

        grid = QAction(QIcon(GRID_ICON),"grid",self)
        tb.addAction(grid)
        
        tb.actionTriggered[QAction].connect(self.tbpressed)
#        tb2 = self.addToolBar("Draw")
#        line = QAction(QIcon("icons/fit.jpg"),"line",self)
#        tb2.addAction(line)

    def tbpressed(self,a):
        if a.text() == "fit":
            self.canvas.fitWorldToViewport()

        elif a.text() == "panR":
            self.canvas.panWorldWindow(-0.2, 0.0)

        elif a.text() == "grid":
            self.buildPopup("Grid Options", GRID)
    
    def buildPopup(self, name, popUpType, geometry = [200, 200, 300, 100]):
        self.popUp = Popup(name, popUpType, self.canvas)
        self.popUp.setGeometry(geometry[0], geometry[1], geometry[2], geometry[3])
        self.popUp.show()

class Popup(QWidget):
    def __init__(self, name, popUpType, canvas_ref):
        super().__init__()

        self.name = name
        self.vbox = None
        self.canvas = canvas_ref

        self.initUI(popUpType)

    def initUI(self, popUpType):
        self.setWindowTitle(self.name)
        self.vbox = QVBoxLayout()

        if popUpType == GRID:
            self.setWindowIcon(QIcon(GRID_ICON))
            self.gridUI()

    def gridUI(self):
        r1 = QLabel("Qtd de pontos no eixo x(x > 1)")
        t1 = QLineEdit()
        
        r2 = QLabel("Qtd de pontos no eixo y(y > 1)")
        t2 = QLineEdit()

        b1 = QPushButton("Gerar Grid")

        self.vbox.addWidget(r1)
        self.vbox.addWidget(t1)

        self.vbox.addWidget(r2)
        self.vbox.addWidget(t2)

        self.vbox.addWidget(b1)

        self.setLayout(self.vbox)

        # Connecting the signal
        def callGridGenerator():
            try:
                gridX = int(t1.text())
                gridY = int(t2.text())

            except ValueError:
                print("ERROR: Os campos devem ser preenchidos com um número inteiro")
                return

            if gridX <= 1 or gridY <= 1:
                print("ERROR: Os valores devem ser maiores que 1")
                return

            print("Gerando Grid!!!")
            self.canvas.generateGrid(gridX, gridY)
            self.close()
            

        b1.clicked.connect(callGridGenerator)
