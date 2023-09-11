from PyQt6.QtWidgets import QApplication, QWidget, QFileDialog, QVBoxLayout, QPushButton, QLabel, QCheckBox, QSpinBox, QHBoxLayout, QScrollArea, QSizePolicy, QMainWindow, QGridLayout,QMessageBox
from PyQt6.QtCore import Qt
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
        
        # Inicialização do contador
        self.counter = 1
        self.field_counter = {}  # Para guardar a contagem de cada campo

        self.label = QLabel("Selecione um arquivo (PDF/EPUB) para renomear.")
        self.label.setWordWrap(True)
        grid.addWidget(self.label, 0, 0, 1, 2)
        
        self.check_boxes = {}  # Inicializa o dicionário para as caixas de seleção
        self.order_labels = {}  # Inicializa o dicionário para os rótulos de ordem
        self.checked_order = []

        btn = QPushButton("Selecionar Arquivo(s)")
        btn.clicked.connect(self.openFileNameDialog)
        grid.addWidget(btn, 1, 0)

        self.copy_check = QCheckBox("Copiar - Manter original inalterado")
        grid.addWidget(self.copy_check, 1, 1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Chamando o método refatorado para criar caixas de seleção e rótulos
        self.create_check_boxes(grid, ['Year', 'ISBN', 'Author', 'Publisher', 'Title'])
        
        self.confirm_btn = QPushButton("Confirmar")
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.clicked.connect(self.executeRenaming)
        grid.addWidget(self.confirm_btn, 8, 0, 1, 2)
        
        # Diminui o espaço entre as linhas 0 e 1
        grid.setRowMinimumHeight(0, 65)

        self.setLayout(grid)
        self.selected_files = []  # Agora uma lista para suportar múltiplos arquivos
        self.info = {}

        # Ajuste da altura da janela
        self.setGeometry(100, 100, 400, 250)


    def create_check_boxes(self, grid, fields):
        for i, field in enumerate(fields):
            check = QCheckBox(field)
            label = QLabel("0")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMaximumWidth(50)
            check.stateChanged.connect(partial(self.handleAutoNumbering, field=field))
            self.check_boxes[field] = check  # Armazena no dicionário
            self.order_labels[field] = label  # Armazena no dicionário
            grid.addWidget(check, i+3, 0)
            grid.addWidget(label, i+3, 1)

    
    def openFileNameDialog(self):
        options = QFileDialog.Option
        #options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Selecione um ou mais arquivos", "", "PDF Files (*.pdf);;EPUB Files (*.epub)")

        if files:
            self.selected_files = files
            self.label.setText("Arquivo(s) selecionado(s): " + ", ".join(files))
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

            selected_order = sorted([(key, int(self.order_labels[key].text())) for key, box in self.check_boxes.items() if box.isChecked()], key=lambda x: x[1])
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
                total_pages = len(reader.pages)

                # Primeira Parte: Seu código original
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

                # Segunda Parte: Abordagem mais genérica
                for i in range(min(5, total_pages)) + list(range(-3, 0, 1)):  # 5 primeiras e 3 últimas páginas
                    page = reader.pages[i]
                    text = page.extract_text()
                    # Busca por autor
                    if info['Author'] == 'Unknown':
                        author_match = re.search(r'(?:[Aa]uthor|Written\sby|By)[:\s]*([^\n\r]+)', text)
                        if author_match:
                            info['Author'] = author_match.group(1).strip()

                # Terceira Parte: busca por dados no próprio arquivo (similar ao que foi feito anteriormente)
                metadata = reader.getDocumentInfo()
                if metadata:
                    info['Title'] = metadata.get('/Title', info['Title'])
                    info['Author'] = metadata.get('/Author', info['Author'])
                    info['Year'] = metadata.get('/CreationDate', info['Year'])[:4]
                    info['Publisher'] = metadata.get('/Producer', info['Publisher'])

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

        if old_path != new_path:  # Adicionada verificação para evitar shutil.SameFileError
            if copy:
                shutil.copy(old_path, new_path)
            else:
                os.rename(old_path, new_path)
        else:
            print(f"Skipping {old_path} as old and new paths are identical.")
        
        return new_path

    
    
    def checkDuplicateNumbers(self):
        active_numbers = [int(self.order_labels[key].text()) for key, box in self.check_boxes.items() if box.isChecked()]
        duplicates = {num for num in active_numbers if active_numbers.count(num) > 1}

        if duplicates:
            duplicate_msg = ', '.join(map(str, duplicates))
            current_label_text = self.label.text()
            self.label.setText(f"{current_label_text}Alerta: Números repetidos detectados - {duplicate_msg}")
        else:
            current_label_text = self.label.text()
            self.label.setText(f"{current_label_text}Nenhum número repetido detectado.")

    
    def handleAutoNumbering(self, state, field):
        if state == Qt.CheckState.Checked:
            # Se o campo já tiver um contador, use-o; caso contrário, use o contador global
            self.order_labels[field].setText(str(self.field_counter.get(field, self.counter)))
            if field not in self.field_counter:
                self.field_counter[field] = self.counter  # Guarde o contador para esse campo
                self.counter += 1  # Incrementa o contador global somente se for um novo campo
            self.checked_order.append(field)

        else:
            if field in self.checked_order:
                self.checked_order.remove(field)
            self.order_labels[field].setText("0")

def show_error(self, message):
    error_dialog = QMessageBox(self)
    error_dialog.setIcon(QMessageBox.Icon.Critical)
    error_dialog.setText(f"Erro: {message}")
    error_dialog.setWindowTitle('Erro')
    error_dialog.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = FileRenamer()
    window.setWindowTitle("File Renamer")
    window.setGeometry(100, 100, 400, 200)
    window.show()

    sys.exit(app.exec())
