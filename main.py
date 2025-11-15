import cv2 as cv
import numpy as np
import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QLineEdit, QFileDialog, 
                            QMessageBox, QProgressBar, QTextEdit, QLabel, QComboBox, QVBoxLayout, QWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import math
import glob
import subprocess

def wyczyscZdjecia(log_callback=None):
    files = glob.glob('work/zdjecia/*')
    pomyslnieusuniete = 0
    nieusuniete = 0
    for f in files:
        try:
            if os.path.isfile(f):
                os.remove(f)
                pomyslnieusuniete += 1
        except Exception as e:
            print(f'Błąd przy usuwaniu zdjęcia -> {e}')
            if log_callback:
                log_callback(f'Błąd przy usuwaniu zdjęcia -> {e}')
            nieusuniete += 1
    print(f'Usunięto {pomyslnieusuniete}, nie udało się usunąć {nieusuniete}')
    if log_callback:
        log_callback(f'Usunięto {pomyslnieusuniete}, nie udało się usunąć {nieusuniete}')

def ekstracjaKlatek(sciezka, docelowa_liczba_klatek, docelowa_rozdzielczosc=None, log_callback=None):
    print(f'Otwieranie filmu: {sciezka}')
    if log_callback:
        log_callback(f'Otwieranie filmu: {sciezka}')
    
    film = cv.VideoCapture(sciezka)
    
    # Pobierz całkowitą liczbę klatek w filmie
    calkowita_liczba_klatek = int(film.get(cv.CAP_PROP_FRAME_COUNT))
    fps = film.get(cv.CAP_PROP_FPS)
    
    # Oblicz interwał co ile klatek zapisywać
    if docelowa_liczba_klatek >= calkowita_liczba_klatek:
        interwal = 1  # Zapisz wszystkie klatki
    else:
        interwal = max(1, calkowita_liczba_klatek // docelowa_liczba_klatek)
    
    print(f'Film ma {calkowita_liczba_klatek} klatek, ekstrakcja co {interwal} klatki')
    if log_callback:
        log_callback(f'Film ma {calkowita_liczba_klatek} klatek, ekstrakcja co {interwal} klatki')
    print(f'Docelowa liczba klatek: {docelowa_liczba_klatek}')
    if log_callback:
        log_callback(f'Docelowa liczba klatek: {docelowa_liczba_klatek}')

    i = 0
    klatki = 0
    zapisane_klatki = 0
    os.makedirs('work/zdjecia', exist_ok=True)
    wyczyscZdjecia(log_callback)
    
    while(film.isOpened()):
        flag, klatka = film.read()
        if flag == False:
            break
        h, w, _ = klatka.shape
        
        if klatki % interwal == 0 and zapisane_klatki < docelowa_liczba_klatek:  
            # Docelowa rozdzielczosc, chyba ze nie wybrana to HD
            if docelowa_rozdzielczosc:
                nowew, noweh = docelowa_rozdzielczosc
                if(h > w):
                    nowew, noweh = noweh, nowew
            else:
                if(h > w):
                    noweh = 1280
                    nowew = 720
                else:
                    noweh = 720
                    nowew = 1280
            
            resized_img = cv.resize(klatka, (nowew, noweh))
            cv.imwrite(f'./work/zdjecia/img_{i:04d}.jpg', resized_img)
            print(f'Zapisano ./work/zdjecia/img_{i:04d}.jpg')
            if log_callback:
                log_callback(f'Zapisano ./work/zdjecia/img_{i:04d}.jpg')
            i += 1
            zapisane_klatki += 1
            
        klatki += 1
        
        # Przerwij jeśli osiągnięto docelową liczbę klatek
        if zapisane_klatki >= docelowa_liczba_klatek:
            break
            
    film.release()
    return zapisane_klatki

class ColmapThread(QThread):
    koniec = pyqtSignal(str)
    err = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, nazwa_modelu, ile_watkow):
        super().__init__()
        self.nazwa_modelu = nazwa_modelu
        self.ile_watkow = ile_watkow

    def run(self):
        import subprocess
        try:
            process = subprocess.Popen(
                ['python3', 'colmap.py', '-o', self.nazwa_modelu, '-nthreads', self.ile_watkow],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log_signal.emit(line)

            process.wait()

            if process.returncode == 0:
                self.koniec.emit(self.nazwa_modelu)
        except subprocess.CalledProcessError as e:
            self.err.emit(str(e))
        except Exception as e:
            self.err.emit(str(e))

class ExtractionThread(QThread):
    progres = pyqtSignal(int)
    koniec = pyqtSignal(int)
    err = pyqtSignal(str)
    log_signal = pyqtSignal(str)

    def __init__(self, sciezka, docelowa_liczba_klatek, docelowa_rozdzielczosc=None):
        super().__init__()
        self.sciezka = sciezka
        self.docelowa_liczba_klatek = docelowa_liczba_klatek
        self.docelowa_rozdzielczosc = docelowa_rozdzielczosc

    def run(self):
        try:
            wyekstraktowane_klatki = ekstracjaKlatek(
                self.sciezka, 
                self.docelowa_liczba_klatek, 
                self.docelowa_rozdzielczosc,
                log_callback=self.log_signal.emit
            )
            self.koniec.emit(wyekstraktowane_klatki)
        except Exception as e:
            self.err.emit(str(e))
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.og_rozdzielczosc = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Fotogrametriowicz")
        self.setGeometry(100, 100, 600, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Wybieranie pliku
        film_layout = QHBoxLayout()
        self.film_label = QLabel("Wybierz film:")
        self.film_sciezka = QLineEdit()
        self.film_sciezka.setPlaceholderText("Kliknij, aby wybrać film")
        self.film_sciezka.setReadOnly(True)
        self.przegladaj_przycisk = QPushButton("Przeglądaj")
        self.przegladaj_przycisk.clicked.connect(self.przegladaj_film)

        film_layout.addWidget(self.film_label)
        film_layout.addWidget(self.film_sciezka)
        film_layout.addWidget(self.przegladaj_przycisk)
        main_layout.addLayout(film_layout)

        # Liczba klatek
        klatki_layout = QHBoxLayout()
        self.klatki_label = QLabel('Docelowa liczba klatek:')
        self.klatki_input = QLineEdit()
        self.klatki_input.setText('100')  # Domyślna wartość
        self.klatki_input.setMaximumWidth(60)
        self.klatki_input.setPlaceholderText('Wprowadź docelową liczbę klatek')

        self.calkowite_klatki_label = QLabel('Całkowita liczba klatek: -')
        self.calkowite_klatki_label.setStyleSheet("color: gray; font-style: italic;")

        klatki_layout.addWidget(self.klatki_label)
        klatki_layout.addWidget(self.klatki_input)
        klatki_layout.addStretch()
        klatki_layout.addWidget(self.calkowite_klatki_label)
        main_layout.addLayout(klatki_layout)

        # Rozdzielczość
        rozdzielczosc_layout = QHBoxLayout()
        self.rozdzielczosc_label = QLabel('Rozdzielczość: -')
        self.rozdzielczosc_label.setStyleSheet("color: gray; font-style: italic;")

        self.docelowa_rozdzielczosc_label = QLabel('Docelowa rozdzielczość:')
        self.rozdzielczosc_combo = QComboBox()
        
        self.typowe_rozdzielczosci = [
            (3840, 2160, "4K (3840x2160)"),
            (2560, 1440, "1440p (2560x1440)"),
            (1920, 1080, "1080p (1920x1080)"),
            (1280, 720, "720p (1280x720)"),
            (854, 480, "480p (854x480)")
        ]

        rozdzielczosc_layout.addWidget(self.rozdzielczosc_label)
        rozdzielczosc_layout.addWidget(self.docelowa_rozdzielczosc_label)
        rozdzielczosc_layout.addWidget(self.rozdzielczosc_combo)
        main_layout.addLayout(rozdzielczosc_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Przycisk od ekstrakcji
        self.extract_btn = QPushButton("Ekstraktuj klatki")
        self.extract_btn.clicked.connect(self.start_extract)
        main_layout.addWidget(self.extract_btn)

        colmap_layout = QHBoxLayout()
        self.nazwa_modelu_label = QLabel('Nazwa modelu 3D:')
        self.nazwa_modelu_input = QLineEdit()
        self.nazwa_modelu_input.setPlaceholderText('Wprowadź nazwę pliku .ply')

        colmap_layout.addWidget(self.nazwa_modelu_label)
        colmap_layout.addWidget(self.nazwa_modelu_input)
        main_layout.addLayout(colmap_layout)

        colmap_btn_layout = QHBoxLayout()
        self.ile_watkow_label = QLabel('Liczba wątków:')
        self.ile_watkow_input = QLineEdit()
        self.ile_watkow_input.setText('4')
        self.ile_watkow_input.setMaximumWidth(100)
        self.uruchom_colmap_btn = QPushButton('Uruchom rekonstrukcję')
        self.uruchom_colmap_btn.clicked.connect(self.uruchom_colmap)
        colmap_btn_layout.addWidget(self.ile_watkow_label)
        colmap_btn_layout.addWidget(self.ile_watkow_input)
        colmap_btn_layout.addStretch()
        colmap_btn_layout.addWidget(self.uruchom_colmap_btn)
        main_layout.addLayout(colmap_btn_layout)

        # Logi
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("background-color: #1f1f1f; color: white; font-family: Consolas;")
        self.log_window.setMinimumHeight(150)
        main_layout.addWidget(self.log_window)

    def update_rozdzielczosc_combo(self):
        if not self.og_rozdzielczosc:
            return
            
        og_w, og_h = self.og_rozdzielczosc
        self.rozdzielczosc_combo.clear()
        
        # OG rozdzielczość jako pierwsza pozycja
        self.rozdzielczosc_combo.addItem(
            f"Oryginalna ({og_w}x{og_h})", 
            (og_w, og_h)
        )
        # Dodawania rozdzielczosci <= od oryginalnej
        added_count = 0
        for width, height, name in self.typowe_rozdzielczosci:
            if width < og_w and height < og_h:
                self.rozdzielczosc_combo.addItem(name, (width, height))
                added_count += 1
                
        # Jak zadnej nie dodalo to przyps bo co to za mala rozdzielczosc lol

    def wybrana_rozdzielczosc(self):
        if self.rozdzielczosc_combo.count() > 0:
            return self.rozdzielczosc_combo.currentData()
        return None

    def log(self, message):
        self.log_window.append(message)
        self.log_window.verticalScrollBar().setValue(self.log_window.verticalScrollBar().maximum())

    def przegladaj_film(self):
        film_sciezka, _ = QFileDialog.getOpenFileName(
            self,
            'Wybierz plik wideo',
            '',
            'Video Files (*.mp4 *.avi *.mov *.mkv *.wmv)'
        )
        if film_sciezka:
            self.film_sciezka.setText(film_sciezka)
            self.aktualizuj_info_klatek(film_sciezka)

    def aktualizuj_info_klatek(self, sciezka):
        film = cv.VideoCapture(sciezka)
        if film.isOpened():
            calkowita_liczba_klatek = int(film.get(cv.CAP_PROP_FRAME_COUNT))
            fps = film.get(cv.CAP_PROP_FPS)
            ret, frame = film.read()
            if ret:
                og_h, og_w, _ = frame.shape
                self.og_rozdzielczosc = (og_w, og_h)
                
                self.update_rozdzielczosc_combo()
                
                if fps > 0:
                    duration = calkowita_liczba_klatek / fps
                    minutes = int(duration // 60)
                    seconds = int(duration % 60)
                    czas_info = f" ({minutes:02d}:{seconds:02d})"
                else:
                    czas_info = ""
                    
                self.calkowite_klatki_label.setText(f"Całkowita liczba klatek: {calkowita_liczba_klatek}{czas_info}")
                self.calkowite_klatki_label.setStyleSheet("color: white; font-style: normal;")

                self.rozdzielczosc_label.setText(f"Rozdzielczość: {og_w}x{og_h}")
                self.rozdzielczosc_label.setStyleSheet("color: white; font-style: normal;")
            else:
                self.show_error("Błąd odczytu klatki")
        else:
            self.show_error("Błąd otwarcia filmu")
        
        film.release()

    def show_error(self, message):
        self.calkowite_klatki_label.setText("Całkowita liczba klatek: Błąd odczytu")
        self.calkowite_klatki_label.setStyleSheet("color: red; font-style: italic;")
        self.rozdzielczosc_label.setText("Rozdzielczość: Błąd odczytu")
        self.rozdzielczosc_label.setStyleSheet("color: red; font-style: italic;")

    def start_extract(self):
        sciezka_filmu = self.film_sciezka.text()
        klatki_text = self.klatki_input.text()

        # Walidacja
        if not sciezka_filmu:
            QMessageBox.warning(self, 'Błąd', 'Proszę wybrać plik wideo!')
            return

        if not os.path.exists(sciezka_filmu):
            QMessageBox.warning(self, 'Błąd', 'Wybrany plik nie istnieje!')
            return

        try:
            docelowa_liczba_klatek = int(klatki_text)
            if docelowa_liczba_klatek <= 0:
                raise ValueError("Liczba klatek musi być dodatnia")
        except ValueError:
            QMessageBox.warning(self, 'Błąd', 'Proszę wprowadzić poprawną liczbę klatek!')
            return

        docelowa_rozdzielczosc = self.wybrana_rozdzielczosc()

        # Wyłącz UI podczas ekstrakcji
        self.extract_btn.setEnabled(False)
        self.przegladaj_przycisk.setEnabled(False)
        self.progress_bar.setVisible(True)

        # Rozpocznij ekstrakcję w osobnym wątku
        self.extraction_thread = ExtractionThread(
            sciezka_filmu, 
            docelowa_liczba_klatek, 
            docelowa_rozdzielczosc
        )
        self.extraction_thread.koniec.connect(self.ekstrakcja_zakonczona)
        self.extraction_thread.err.connect(self.ekstrakcja_bledu)
        self.extraction_thread.log_signal.connect(self.log)
        self.extraction_thread.start()

    def ekstrakcja_zakonczona(self, liczba_klatek):
        # Włącz UI ponownie
        self.extract_btn.setEnabled(True)
        self.przegladaj_przycisk.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(self, 'Sukces', f'Pomyślnie zapisano {liczba_klatek} klatek w folderze ./work/zdjecia/')

    def ekstrakcja_bledu(self, komunikat_bledu):
        # Włącz UI ponownie
        self.extract_btn.setEnabled(True)
        self.przegladaj_przycisk.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, 'Błąd', f'Wystąpił błąd: {komunikat_bledu}')

    def uruchom_colmap(self):
        nazwa_modelu = self.nazwa_modelu_input.text().strip()
        ile_watkow = self.ile_watkow_input.text().strip()
        if not nazwa_modelu:
            QMessageBox.warning(self, 'Błąd', 'Proszę podać nazwę modelu 3D!')
            return

        if not nazwa_modelu.endswith('.ply'):
            nazwa_modelu += '.ply'

        # Trzeba sprawdzic czy sa zdjecia
        zdjecia_folder = './work/zdjecia'
        if not os.path.exists(zdjecia_folder) or not os.listdir(zdjecia_folder):
            QMessageBox.warning(self, 'Błąd', 'Brak wyekstrahowanych klatek! Najpierw wykonaj ekstrakcję.')
            return

        # Wyłączenie GUI na czas rekonstrukcji
        self.uruchom_colmap_btn.setEnabled(False)
        self.extract_btn.setEnabled(False)
        self.przegladaj_przycisk.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)

        # colmap.py w osobnym wątku
        self.colmap_thread = ColmapThread(nazwa_modelu, ile_watkow)
        self.colmap_thread.koniec.connect(self.colmap_finished)
        self.colmap_thread.err.connect(self.colmap_error)
        self.colmap_thread.log_signal.connect(self.log)
        self.colmap_thread.start()

    def colmap_finished(self, nazwa_modelu):
        self.uruchom_colmap_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        self.przegladaj_przycisk.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, 'Sukces', f'Rekonstrukcja zakończona! Model zapisano jako {nazwa_modelu}')

    def colmap_error(self, komunikat_bledu):
        self.uruchom_colmap_btn.setEnabled(True)
        self.extract_btn.setEnabled(True)
        self.przegladaj_przycisk.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, 'Błąd', f'Wystąpił błąd podczas rekonstrukcji: {komunikat_bledu}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())