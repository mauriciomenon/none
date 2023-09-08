from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel, QCheckBox, QSpinBox, QHBoxLayout, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt
import sys
import os
import re
import shutil
import PyPDF2
from ebooklib import epub

class FileRenamer(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Configuração da QScrollArea
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)

        # Configuração do QLabel para exibir os resultados

        self.label = QLabel("Selecione um arquivo (PDF/EPUB) para renomear.")
        self.label.setWordWrap(True)  # Habilitar quebra de linha
        self.label.setMinimumSize(400, 100)  # Definir tamanho mínimo
        self.label.setMaximumSize(500, 150)  # Definir tamanho máximo (opcional)
        #self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.label)

        # Adicionar QLabel à QScrollArea
        scroll.setWidget(self.label)

        # Adicionar QScrollArea ao layout principal
        #layout.addWidget(scroll)

        self.btn = QPushButton("Selecionar Arquivo(s)")
        self.btn.clicked.connect(self.openFileNameDialog)
        layout.addWidget(self.btn)

        self.copy_check = QCheckBox("Copiar - Manter original inalterado")
        layout.addWidget(self.copy_check)

        self.check_boxes = {}
        self.spin_boxes = {}
        for field in ['Year', 'ISBN', 'Author', 'Publisher', 'Title']:
            hbox = QHBoxLayout()
            check = QCheckBox(field)
            spin = QSpinBox()
            spin.setMinimum(0)
            spin.setMaximum(5)
            spin.setMaximumWidth(50)
            spin.setDisabled(True)
            check.stateChanged.connect(lambda state, s=spin: s.setEnabled(bool(state)))
            hbox.addWidget(check)
            hbox.addWidget(spin)
            layout.addLayout(hbox)
            self.check_boxes[field] = check
            self.spin_boxes[field] = spin

        self.confirm_btn = QPushButton("Confirmar")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.executeRenaming)
        layout.addWidget(self.confirm_btn)

        self.setLayout(layout)
        self.selected_files = []  # Agora uma lista para suportar múltiplos arquivos
        self.info = {}

        # Ajuste da altura da janela
        self.setGeometry(100, 100, 400, 250)

    def openFileNameDialog(self):
        # Apagar qualquer mensagem de status anterior
        self.label.setText("")
        
        filePaths, _ = QFileDialog.getOpenFileNames(self, "Selecione um ou mais arquivos", "", "PDF Files (*.pdf);;EPUB Files (*.epub);;Todos os Arquivos (*)")
        
        if filePaths:
            self.selected_files = filePaths
            self.label.setText("Arquivos selecionados:\n" + '\n'.join(filePaths))
            self.confirm_btn.setEnabled(True)

    def executeRenaming(self):
        if not self.selected_files:  # Se a lista estiver vazia, retorne
            return

        for selected_file in self.selected_files:  # Iterando sobre cada arquivo
            ext = os.path.splitext(selected_file)[1]  # Obtendo a extensão para um único arquivo

            if ext == '.pdf':
                info = self.extract_info_from_pdf(selected_file)
            elif ext == '.epub':
                info = self.extract_info_from_epub(selected_file)
            else:
                info = {}

            selected_order = sorted([(key, self.spin_boxes[key].value()) for key, box in self.check_boxes.items() if box.isChecked()], key=lambda x: x[1])

            if any(info[key] != 'Unknown' for key, _ in selected_order):
                new_path = self.rename_file(selected_file, info, [key for key, _ in selected_order], self.copy_check.isChecked())
                self.label.setText(f"Arquivo renomeado para: {new_path}\n")
            else:
                missing_info = ', '.join([key for key, value in info.items() if value == 'Unknown'])
                self.label.setText(f"Informações não encontradas. Faltando: {missing_info}\n")

            self.confirm_btn.setEnabled(False)

        # Chama a função para verificar números duplicados nos spin boxes.
        self.checkDuplicateNumbers()

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

    def rename_file(self, old_path, info, selected_order, copy):
        new_name_elements = [info[key] for key in selected_order if info[key] != 'Unknown']
        new_name = '_'.join(new_name_elements) + os.path.splitext(old_path)[1]
        new_path = os.path.join(os.path.dirname(old_path), new_name)

        if copy:
            shutil.copy(old_path, new_path)
        else:
            os.rename(old_path, new_path)
        return new_path
    
    def checkDuplicateNumbers(self):
        active_numbers = [self.spin_boxes[key].value() for key, box in self.check_boxes.items() if box.isChecked()]
        duplicates = {num for num in active_numbers if active_numbers.count(num) > 1}

        if duplicates:
            duplicate_msg = ', '.join(map(str, duplicates))
            current_label_text = self.label.text()
            self.label.setText(f"{current_label_text}Alerta: Números repetidos detectados - {duplicate_msg}")
        else:
            current_label_text = self.label.text()
            self.label.setText(f"{current_label_text}Nenhum número repetido detectado.")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = FileRenamer()
    window.setWindowTitle("File Renamer")
    window.setGeometry(100, 100, 400, 200)
    window.show()

    sys.exit(app.exec())
