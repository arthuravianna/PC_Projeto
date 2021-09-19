from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from mycanvas import *
from mymodel import *

# Globals
GRID = 0
PVC = 1
SAVE = 2
GRID_ICON = "icons/grid.png"
PVC_ICON = "icons/pvc.png"
SAVE_ICON = "icons/save.png"

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

        grid = QAction(QIcon(GRID_ICON),"generate grid",self)
        tb.addAction(grid)

        pvc = QAction(QIcon(PVC_ICON),"set boundary value",self)
        tb.addAction(pvc)

        save = QAction(QIcon("icons/save.png"),"save model",self)
        tb.addAction(save)

        clear = QAction(QIcon("icons/clear.png"),"clear model",self)
        tb.addAction(clear)

        tb.actionTriggered[QAction].connect(self.tbpressed)
#        tb2 = self.addToolBar("Draw")
#        line = QAction(QIcon("icons/fit.jpg"),"line",self)
#        tb2.addAction(line)

    def tbpressed(self,a):
        if a.text() == "fit":
            self.canvas.fitWorldToViewport()

        elif a.text() == "panR":
            self.canvas.panWorldWindow(-0.2, 0.0)

        elif a.text() == "generate grid":
            self.buildPopup("Grid Options", GRID)

        elif a.text() == "set boundary value":
            self.buildPopup("PVC Value", PVC)

        elif a.text() == "save model":
            self.buildPopup("Filename", SAVE)

        elif a.text() == "clear model":
            self.model.clear_model()
            self.canvas.clear_hmodel()


    def buildPopup(self, name, popUpType, geometry = [200, 200, 300, 100]):
        self.popUp = Popup(name, popUpType, self.canvas, self.model)
        self.popUp.setGeometry(geometry[0], geometry[1], geometry[2], geometry[3])
        self.popUp.show()

class Popup(QWidget):
    def __init__(self, name, popUpType, canvas_ref, model_ref):
        super().__init__()

        self.name = name
        self.vbox = None
        self.canvas = canvas_ref
        self.model = model_ref

        self.initUI(popUpType)

    def initUI(self, popUpType):
        self.setWindowTitle(self.name)
        self.vbox = QVBoxLayout()

        if popUpType == GRID:
            self.setWindowIcon(QIcon(GRID_ICON))
            self.gridUI()
        
        elif popUpType == PVC:
            self.setWindowIcon(QIcon(PVC_ICON))
            self.pvcUI()

        elif popUpType == SAVE:
            self.setWindowIcon(QIcon(SAVE_ICON))
            self.saveUI()

    def gridUI(self):
        #r1 = QLabel("Qtd de pontos no eixo x(x > 1)")
        r1 = QLabel("Digite o espaçamento horizontal")
        t1 = QLineEdit()
        
        #r2 = QLabel("Qtd de pontos no eixo y(y > 1)")
        r2 = QLabel("Digite o espaçamento vertical")
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
                h = float(t1.text())
                k = float(t2.text())

            except ValueError:
                print("ERROR: Os campos devem ser preenchidos com um número.")
                return

            print("Gerando Grid...")
            self.canvas.generateGrid(h, k)
            self.close()
            

        b1.clicked.connect(callGridGenerator)

    def pvcUI(self):
        r1 = QLabel("Valor do PVC para os pontos selecionados")
        t1 = QLineEdit()
        
        b1 = QPushButton("OK")

        self.vbox.addWidget(r1)
        self.vbox.addWidget(t1)

        self.vbox.addWidget(b1)

        self.setLayout(self.vbox)

        # Connecting the signal
        def callSetPVC():
            try:
                pvc_value = float(t1.text())

            except ValueError:
                print("ERROR: O campo deve ser preenchido com um número.")
                return


            print("PVC info gerada!!!")
            self.model.set_pvc(pvc_value)
            self.close()
            

        b1.clicked.connect(callSetPVC)
    

    def saveUI(self):
        r1 = QLabel("Digite o nome do arquivo(Use a extensão \".json\")")
        t1 = QLineEdit()
        
        b1 = QPushButton("Save")

        self.vbox.addWidget(r1)
        self.vbox.addWidget(t1)

        self.vbox.addWidget(b1)

        self.setLayout(self.vbox)

        # Connecting the signal
        def callSaveModel():
            filename = t1.text()
            if len(filename) == 0: print("ERRO: Eh necessario dar um nome ao arquivo.")

            print("Salvando Modelo...")
            self.model.save_model(filename)
            self.close()
            

        b1.clicked.connect(callSaveModel)