import sys
import ollama
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QFileDialog, QComboBox,
                             QTextEdit, QHBoxLayout, QSizePolicy)
from PyQt6.QtGui import QPixmap, QGuiApplication, QTextOption
from PyQt6.QtCore import Qt, QTimer
from enum import Enum

class CopyState(Enum):
    READY = 0
    SUCCESS = 1
    ERROR = 2

class ImageAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.copy_state = CopyState.READY
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Prompt from picture with llama3.2-vision")
        self.setGeometry(100, 100, 600, 400)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Bildauswahl und Anzeige (ohne ScrollArea)
        self.image_label = QLabel("Kein Bild ausgewählt")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(300)  # Höhe auf 400px fixiert
        layout.addWidget(self.image_label)

        self.select_image_button = QPushButton("Bild auswählen")
        self.select_image_button.clicked.connect(self.select_image)
        layout.addWidget(self.select_image_button)

        self.instruction_label = QLabel("Anweisung:")
        layout.addWidget(self.instruction_label)

        self.instruction_combo = QComboBox()
        self.load_instructions()
        layout.addWidget(self.instruction_combo)

        self.custom_instruction_label = QLabel("Oder eigene Anweisung:")
        layout.addWidget(self.custom_instruction_label)

        self.custom_instruction_input = QTextEdit()
        self.custom_instruction_input.setFixedHeight(50)
        layout.addWidget(self.custom_instruction_input)

        analyze_layout = QHBoxLayout()
        self.analyze_button = QPushButton("Bild analysieren")
        self.analyze_button.clicked.connect(self.analyze_image)
        analyze_layout.addWidget(self.analyze_button)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.custom_instruction_input.setFixedHeight(100)
        text_options = self.text_output.document().defaultTextOption()
        text_options.setWrapMode(QTextOption.WrapMode.WrapAtWordBoundaryOrAnywhere)
        self.text_output.document().setDefaultTextOption(text_options)
        layout.addWidget(self.text_output)
        layout.addLayout(analyze_layout)

        self.copy_button = QPushButton("Text in Zwischenablage kopieren")
        self.copy_button.clicked.connect(self.copy_text_to_clipboard)
        layout.addWidget(self.copy_button)


        self.image_path = None

    def load_instructions(self):
        try:
            with open("anweisungen.txt", "r") as f:
                instructions = f.read().split("\n\n")
                self.instruction_combo.addItems(instructions)
        except FileNotFoundError:
            self.instruction_combo.addItems(["Datei 'anweisungen.txt' nicht gefunden"])

    def select_image(self):
        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Bilder (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            self.image_path = file_dialog.selectedFiles()[0]
            pixmap = QPixmap(self.image_path)

            scaled_pixmap = pixmap.scaledToHeight(400, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

    def analyze_image(self):
        if self.image_path:
            selected_instruction = self.instruction_combo.currentText()
            custom_instruction = self.custom_instruction_input.toPlainText().strip()
            instruction = custom_instruction if custom_instruction else selected_instruction

            if not instruction or instruction == "Datei 'anweisungen.txt' nicht gefunden":
                self.text_output.setText("Bitte eine Anweisung auswählen oder eingeben.")
                return

            try:
                self.text_output.setText("Analysiere...")
                QApplication.processEvents()
                response = ollama.chat(
                    model='llama3.2-vision',
                    messages=[
                        {
                            'role': 'user',
                            'content': instruction,
                            'images': [self.image_path]
                        }
                    ]
                )
                self.text_output.setText(response['message']['content'])
            except ollama.OllamaError as e:
                self.text_output.setText(f"Ollama Fehler: {e}")
            except Exception as e:
                self.text_output.setText(f"Unerwarteter Fehler: {e}")

        else:
            self.text_output.setText("Bitte zuerst ein Bild auswählen.")

    def copy_text_to_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        text = self.text_output.toPlainText()
        if text:
            clipboard.setText(text)
            self.copy_state = CopyState.SUCCESS
        else:
            self.copy_state = CopyState.ERROR
        self.update_copy_button_style()
        QTimer.singleShot(2000, self.reset_copy_button_style)

    def update_copy_button_style(self):
        if self.copy_state == CopyState.SUCCESS:
            self.copy_button.setStyleSheet("background-color: green; color: white;")
        elif self.copy_state == CopyState.ERROR:
            self.copy_button.setStyleSheet("background-color: red; color: white;")
        else:
            self.copy_button.setStyleSheet("")

    def reset_copy_button_style(self):
        self.copy_state = CopyState.READY
        self.update_copy_button_style()

def main():
    app = QApplication(sys.argv)
    main_window = ImageAnalyzerApp()
    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
