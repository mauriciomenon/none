from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt
import sys
import os
import re
import PyPDF2

class PDFRenamer(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.label = QLabel("Selecione um arquivo PDF para renomear.")
        layout.addWidget(self.label)

        self.btn = QPushButton("Selecionar Arquivo")
        self.btn.clicked.connect(self.openFileNameDialog)
        layout.addWidget(self.btn)

        self.setLayout(layout)

    def openFileNameDialog(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Selecione um arquivo PDF", "", "PDF Files (*.pdf);;Todos os Arquivos (*)")
        if filePath:
            info = self.extract_info_from_pdf(filePath)
            if all(value != 'Unknown' for value in info.values()):
                new_path = self.rename_file(filePath, info)
                self.label.setText(f"Arquivo renomeado para: {new_path}")
            else:
                self.label.setText("Informações não encontradas no PDF.")

    def extract_info_from_pdf(self, pdf_path):
        info = {'ISBN': 'Unknown', 'Name': 'Unknown', 'Year': 'Unknown', 'Publisher': 'Unknown'}
        
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)

            # Segunda página (índice 1 em notação zero-based)
            text_page_2 = reader.pages[1].extract_text()
            # Terceira página (índice 2 em notação zero-based)
            text_page_3 = reader.pages[2].extract_text()

            # Procurando informações na segunda página
            name = re.search(r'(.+?)\n', text_page_2)
            info['Name'] = name.group(1) if name else 'Unknown'

            # Procurando informações na terceira página
            isbn = re.search(r'ISBN (\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1})', text_page_3)
            year = re.search(r'Copyright \u00A9 (\d{4})', text_page_3)
            publisher = re.search(r'Published by (.+?)\n', text_page_3)
            
            info['ISBN'] = isbn.group(1) if isbn else 'Unknown'
            info['Year'] = year.group(1) if year else 'Unknown'
            info['Publisher'] = publisher.group(1) if publisher else 'Unknown'

        return info


    def rename_file(self, old_path, info):
        new_name = f"{info['ISBN']}_{info['Name']}_{info['Year']}_{info['Publisher']}.pdf"
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        os.rename(old_path, new_path)
        return new_path

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = PDFRenamer()
    window.setWindowTitle("PDF Renamer")
    window.setGeometry(100, 100, 400, 200)
    window.show()

    sys.exit(app.exec())
