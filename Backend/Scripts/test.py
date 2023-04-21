import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QGridLayout
from PyQt5.QtCore import Qt

class Calculator(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.setWindowTitle('Calculator')

        # Create the grid layout
        grid = QGridLayout()
        self.setLayout(grid)

        # Create the display label
        self.display = QLabel('0')
        self.display.setAlignment(Qt.AlignRight)
        self.display.setFixedHeight(50)
        grid.addWidget(self.display, 0, 0, 1, 4)

        # Create the buttons
        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]
        positions = [(i, j) for i in range(1, 5) for j in range(4)]

        for position, button in zip(positions, buttons):
            if button == '=':
                btn = QPushButton(button)
                btn.clicked.connect(self.calculate)
                grid.addWidget(btn, *position)
            else:
                btn = QPushButton(button)
                btn.clicked.connect(self.buttonClicked)
                grid.addWidget(btn, *position)

        self.setGeometry(300, 300, 300, 200)
        self.show()

    def buttonClicked(self):

        button = self.sender()
        digit = button.text()

        if self.display.text() == '0':
            self.display.setText(digit)
        else:
            self.display.setText(self.display.text() + digit)

    def calculate(self):

        equation = self.display.text()
        try:
            result = str(eval(equation))
            self.display.setText(result)
        except:
            self.display.setText('Error')

if __name__ == '__main__':

    app = QApplication(sys.argv)
    calc = Calculator()
    sys.exit(app.exec_())