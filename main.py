import sys
from mywindow import *

def main():
    app = QApplication(sys.argv)
    gui = MyWindow()
    gui.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()