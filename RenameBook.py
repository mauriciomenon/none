from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel, QCheckBox
from PyQt6.QtCore import Qt
import sys
import os
import re
import PyPDF2
from ebooklib import epub

class FileRenamer(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.label = QLabel("Selecione um arquivo (PDF/EPUB) para renomear.")
        layout.addWidget(self.label)

        self.btn = QPushButton("Selecionar Arquivo")
        self.btn.clicked.connect(self.openFileNameDialog)
        layout.addWidget(self.btn)

        self.confirm_btn = QPushButton("Confirmar")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.executeRenaming)
        layout.addWidget(self.confirm_btn)

        self.check_boxes = {'Year': QCheckBox('Ano'), 'ISBN': QCheckBox('ISBN'), 'Author': QCheckBox('Autor'), 'Publisher': QCheckBox('Editora'), 'Title': QCheckBox('Título')}
        for box in self.check_boxes.values():
            layout.addWidget(box)

        self.setLayout(layout)
        self.selected_file = None
        self.info = {}

    def openFileNameDialog(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Selecione um arquivo", "", "PDF Files (*.pdf);;EPUB Files (*.epub);;Todos os Arquivos (*)")
        
        if filePath:
            self.selected_file = filePath
            self.confirm_btn.setEnabled(True)

    def executeRenaming(self):
        if self.selected_file:
            ext = os.path.splitext(self.selected_file)[1]
            if ext == '.pdf':
                self.info = self.extract_info_from_pdf(self.selected_file)
            elif ext == '.epub':
                self.info = self.extract_info_from_epub(self.selected_file)

            if all(value != 'Unknown' for value in self.info.values()):
                selected_order = [key for key, box in self.check_boxes.items() if box.isChecked()]
                new_path = self.rename_file(self.selected_file, self.info, selected_order)
                self.label.setText(f"Arquivo renomeado para: {new_path}")
            else:
                missing_info = ', '.join([key for key, value in self.info.items() if value == 'Unknown'])
                self.label.setText(f"Informações não encontradas. Faltando: {missing_info}")
                
        self.confirm_btn.setEnabled(False)

    def extract_info_from_pdf(self, pdf_path):
        info = {'ISBN': 'Unknown', 'Title': 'Unknown', 'Year': 'Unknown', 'Publisher': 'Unknown', 'Author': 'Unknown'}
        
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text_page_2 = reader.pages[1].extract_text()
                text_page_3 = reader.pages[2].extract_text()

                name = re.search(r'(.+?)\n', text_page_2)
                isbn = re.search(r'ISBN (\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1})', text_page_3)
                year = re.search(r'Copyright \u00A9 (\d{4})', text_page_3)
                publisher = re.search(r'Published by (.+?)\n', text_page_3)

                info['Title'] = name.group(1) if name else 'Unknown'
                info['ISBN'] = isbn.group(1) if isbn else 'Unknown'
                info['Year'] = year.group(1) if year else 'Unknown'
                info['Publisher'] = publisher.group(1) if publisher else 'Unknown'
        except Exception as e:
            self.label.setText(f"Erro ao processar o PDF: {e}")

        return info

    def extract_info_from_epub(self, epub_path):
        info = {'ISBN': 'Unknown', 'Title': 'Unknown', 'Year': 'Unknown', 'Publisher': 'Unknown', 'Author': 'Unknown'}
        
        try:
            book = epub.read_epub(epub_path)
            info['Title'] = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else 'Unknown'
            info['ISBN'] = book.get_metadata('DC', 'identifier')[0][0] if book.get_metadata('DC', 'identifier') else 'Unknown'
            info['Year'] = book.get_metadata('DC', 'date')[0][0] if book.get_metadata('DC', 'date') else 'Unknown'
            info['Publisher'] = book.get_metadata('DC', 'publisher')[0][0] if book.get_metadata('DC', 'publisher') else 'Unknown'
            info['Author'] = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else 'Unknown'
        except Exception as e:
            self.label.setText(f"Erro ao processar o EPUB: {e}")

        return info

    def rename_file(self, old_path, info, selected_order):
        new_name_elements = [info[key] for key in selected_order]
        new_name = '_'.join(new_name_elements) + os.path.splitext(old_path)[1]
        new_path = os.path.join(os.path.dirname(old_path), new_name)
        os.rename(old_path, new_path)
        return new_path

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = FileRenamer()
    window.setWindowTitle("File Renamer")
    window.setGeometry(100, 100, 400, 200)
    window.show()

    sys.exit(app.exec())
