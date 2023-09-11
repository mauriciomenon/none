from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel, QCheckBox, QSpinBox, QHBoxLayout, QScrollArea, QSizePolicy, QMainWindow, QGridLayout, QMessageBox
from PyQt6.QtCore import Qt, QDir
from PyQt6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from functools import partial
import sys
import os
import re
import shutil
import PyPDF2
from ebooklib import epub

class FileRenamer(QWidget):
    def __init__(self):
        super().__init__()
        
        grid = QGridLayout()
        
        # variáveis de instância
        self.counter = 1
        self.field_counter = {}
        self.check_boxes = {}
        self.order_spinboxes = {}
        self.selected_files = []
        self.info = {}

        # dicionário de mapeamento 
        self.key_to_display = {
            'Year': 'Ano',
            'ISBN': 'ISBN',
            'Author': 'Autor',
            'Publisher': 'Editora',
            'Title': 'Título'
        }

        self.label = QLabel("Selecione um arquivo (PDF/EPUB) para renomear.")
        self.label.setWordWrap(True)
        grid.addWidget(self.label, 0, 0, 1, 2)

        btn = QPushButton("Selecionar Arquivo(s)")
        btn.clicked.connect(self.openFileNameDialog)
        grid.addWidget(btn, 1, 0)

        self.copy_check = QCheckBox("Copiar - Manter original inalterado")
        grid.addWidget(self.copy_check, 1, 1)

        self.create_check_boxes(grid, ['Year', 'ISBN', 'Author', 'Publisher', 'Title'])

        self.confirm_btn = QPushButton("Confirmar")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.executeRenaming)
        grid.addWidget(self.confirm_btn, 8, 0, 1, 2)
        
        grid.setRowMinimumHeight(0, 65)
        
        self.setLayout(grid)

        self.setGeometry(100, 100, 400, 250)
        self.setAcceptDrops(True)

        self.dropArea = QLabel("Arraste e solte arquivos aqui.")
        self.dropArea.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dropArea.setStyleSheet("border: 2px solid gray")
        grid.addWidget(self.dropArea, 2, 0, 1, 2)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent):
        self.dropArea.clear()

    def dropEvent(self, event: QDropEvent):
        file_paths = []
        for url in event.mimeData().urls():
            file_paths.append(str(QDir.toNativeSeparators(url.toLocalFile())))
        self.selected_files = file_paths
        self.label.setText("Arquivo(s) selecionado(s) via arrastar e soltar: " + ", ".join(file_paths))
        self.confirm_btn.setEnabled(True)

    def create_check_boxes(self, grid, fields):
        for i, field in enumerate(fields):
            display_field = self.key_to_display.get(field, field)  # Obter a tradução, se disponível
            check = QCheckBox(display_field)
        for i, field in enumerate(fields):
            check = QCheckBox(field)
            spinbox = QSpinBox()
            spinbox.setEnabled(False)
            spinbox.setMaximum(10)
            check.stateChanged.connect(partial(self.handleAutoNumbering, field=field, spinbox=spinbox))
            self.check_boxes[field] = check
            self.order_spinboxes[field] = spinbox
            grid.addWidget(check, i+3, 0)
            grid.addWidget(spinbox, i+3, 1)

    def openFileNameDialog(self):
        options = QFileDialog.Option
        files, _ = QFileDialog.getOpenFileNames(self, "Selecione um ou mais arquivos", "", "PDF Files (*.pdf);;EPUB Files (*.epub)")

        if files:
            self.selected_files = files
            self.label.setText("Arquivo(s) selecionado(s): " + ", ".join(files))
            self.confirm_btn.setEnabled(True)

    def executeRenaming(self):
        
        if not self.selected_files:
            return

        for selected_file in self.selected_files:
            ext = os.path.splitext(selected_file)[1]

            if ext == '.pdf':
                info = self.extract_info_from_pdf(selected_file)
            elif ext == '.epub':
                info = self.extract_info_from_epub(selected_file)
            else:
                info = {}

            selected_order = sorted([(key, self.order_spinboxes[key].value()) for key, box in self.check_boxes.items() if box.isChecked()], key=lambda x: x[1])
            if any(info[key] != 'Unknown' for key, _ in selected_order):
                new_path = self.rename_file(selected_file, info, [key for key, _ in selected_order], self.copy_check.isChecked())
                self.label.setText(f"Arquivo renomeado para: {new_path}\n")
            else:
                missing_info = ', '.join([key for key, value in info.items() if value == 'Unknown'])
                self.label.setText(f"Informações não encontradas. Faltando: {missing_info}\n")

            self.confirm_btn.setEnabled(False)

        self.checkDuplicateNumbers()

    def extract_info_from_pdf(self, pdf_path):
        info = {'ISBN': 'Unknown', 'Title': 'Unknown', 'Year': 'Unknown', 'Publisher': 'Unknown', 'Author': 'Unknown'}
        generic_isbn_regex = r'\b\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1}\b'
        your_isbn_regex = r'ISBN (\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1})'  # Seu regex específico

        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                metadata = reader.metadata
                
                # Fase 1: busca por dados no próprio arquivo (similar ao que foi feito anteriormente)
                if metadata:
                    info['Title'] = metadata.get('dc:title', 'Unknown')
                    info['Author'] = metadata.get('dc:creator', 'Unknown')
                    info['Year'] = metadata.get('xmp:CreateDate', 'Unknown')[:4]
                    info['Publisher'] = metadata.get('pdf:Producer', 'Unknown')

                # Índice de páginas a serem escaneadas: 10 primeiras e 3 últimas
                indices = list(range(min(10, total_pages))) + list(range(-min(3, total_pages), 0))

                for idx in indices:
                    page = reader.pages[idx]
                    text = page.extract_text()

                    # Fase 2: Abordagem direta da regex especificada no seu código
                    if info['ISBN'] == 'Unknown':
                        isbn_match = re.search(your_isbn_regex, text)
                        if isbn_match:
                            info['ISBN'] = isbn_match.group(1)
                    
                    # Fase 3: Abordagem mais genérica para todos os campos
                    if info['Author'] == 'Unknown':
                        author_match = re.search(r'(?:[Aa]uthor|Written\sby|By)[:\s]*([^\n\r]+)', text)
                        if author_match:
                            info['Author'] = author_match.group(1).strip()

                    if info['ISBN'] == 'Unknown':
                        isbn_match = re.search(generic_isbn_regex, text)
                        if isbn_match:
                            info['ISBN'] = isbn_match.group(0)

                    # Buscas adicionais para Year, Publisher e Title poderiam ser adicionadas aqui, se necessário

        except Exception as e:
            print(f"Exception: {e}")  # Debugging statement
            self.label.setText(f"Erro ao processar o PDF: {e}")

        return info


    def extract_info_from_epub(self, epub_path):
        info = {'ISBN': 'Unknown', 'Title': 'Unknown', 'Year': 'Unknown', 'Publisher': 'Unknown', 'Author': 'Unknown'}
        try:
            book = epub.read_epub(epub_path)
            if 'title' in book.metadata['http://purl.org/dc/elements/1.1/']:
                info['Title'] = book.metadata['http://purl.org/dc/elements/1.1/']['title'][0][0]
            if 'creator' in book.metadata['http://purl.org/dc/elements/1.1/']:
                info['Author'] = book.metadata['http://purl.org/dc/elements/1.1/']['creator'][0][0]
            if 'publisher' in book.metadata['http://purl.org/dc/elements/1.1/']:
                info['Publisher'] = book.metadata['http://purl.org/dc/elements/1.1/']['publisher'][0][0]
            if 'date' in book.metadata['http://purl.org/dc/elements/1.1/']:
                info['Year'] = book.metadata['http://purl.org/dc/elements/1.1/']['date'][0][0][:4]
            # Para ISBN, um exemplo simplificado
            # Mais lógica pode ser adicionada aqui para uma extração mais precisa
            if 'identifier' in book.metadata['http://purl.org/dc/elements/1.1/']:
                for identifier in book.metadata['http://purl.org/dc/elements/1.1/']['identifier']:
                    isbn_match = re.search(r'\b\d{3}-\d{1,5}-\d{1,7}-\d{1,7}-\d{1}\b', identifier[0])
                    if isbn_match:
                        info['ISBN'] = isbn_match.group(0)
                        break
        except Exception as e:
            self.label.setText(f"Erro ao processar o EPUB: {e}")

        return info

    def rename_file(self, selected_file, info, selected_order, copy):
        new_name = ' - '.join([info[field] for field in selected_order])
        ext = os.path.splitext(selected_file)[1]
        new_path = os.path.join(os.path.dirname(selected_file), new_name + ext)
        
        if copy:
            shutil.copy(selected_file, new_path)
        else:
            os.rename(selected_file, new_path)

        return new_path

    def handleAutoNumbering(self, state, field, spinbox):
        if state == Qt.CheckState.Checked:
            self.field_counter[field] = self.counter
            spinbox.setValue(self.counter)
            spinbox.setEnabled(True)
            self.counter += 1
        else:
            # Verificando a existência da chave antes de excluí-la
            if field in self.field_counter:
                last_value = self.field_counter[field]  # Armazenando o valor para uso posterior
                del self.field_counter[field]
            
            spinbox.setValue(0)
            spinbox.setEnabled(False)
            
            # Reorganizando os contadores
            for f, c in sorted(self.field_counter.items(), key=lambda item: item[1]):
                if c > last_value:  # Usando o valor armazenado aqui
                    self.field_counter[f] = c - 1
                    self.order_spinboxes[f].setValue(c - 1)

            self.counter -= 1

        self.checkDuplicateNumbers()


    def checkDuplicateNumbers(self):
        unique_values = set()
        for spinbox in self.order_spinboxes.values():
            if spinbox.isEnabled():
                val = spinbox.value()
                if val in unique_values:
                    QMessageBox.critical(self, "Erro", "Valores duplicados encontrados nos números de ordem!")
                    return
                unique_values.add(val)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileRenamer()
    ex.show()
    sys.exit(app.exec())
