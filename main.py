import cv2 as cv
import numpy as np
import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QPushButton, QLabel, QLineEdit, QFileDialog, 
                            QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import math
import glob

def wyczyscZdjecia():
    files = glob.glob('./zdjecia/*')
    pomyslnieusuniete = 0
    nieusuniete = 0
    for f in files:
        try:
            if os.path.isfile(f):
                os.remove(f)
                pomyslnieusuniete += 1
        except Exception as e:
            print(f'Błąd przy usuwaniu zdjęcia -> {e}')
            nieusuniete += 1
    print(f'Usunięto {pomyslnieusuniete}, nie udało się usunąć {nieusuniete}')

def ekstracjaKlatek(sciezka, docelowa_liczba_klatek):
    print(f'Otwieranie filmu: {sciezka}')
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
    print(f'Docelowa liczba klatek: {docelowa_liczba_klatek}')
    
    i = 0
    klatki = 0
    zapisane_klatki = 0
    os.makedirs('./zdjecia', exist_ok=True)
    wyczyscZdjecia()
    
    while(film.isOpened()):
        flag, klatka = film.read()

        if flag == False:
            break

        if klatki % interwal == 0 and zapisane_klatki < docelowa_liczba_klatek:  
            cv.imwrite(f'./zdjecia/img_{i}.jpg', klatka)
            print(f'Zapisano ./zdjecia/img_{i}.jpg')
            i += 1
            zapisane_klatki += 1
            
        klatki += 1
        
        # Przerwij jeśli osiągnięto docelową liczbę klatek
        if zapisane_klatki >= docelowa_liczba_klatek:
            break
            
    film.release()
    return zapisane_klatki


class ExtractionThread(QThread):
    progres = pyqtSignal(int)
    koniec = pyqtSignal(int)
    err = pyqtSignal(str)

    def __init__(self, sciezka, docelowa_liczba_klatek):
        super().__init__()
        self.sciezka = sciezka
        self.docelowa_liczba_klatek = docelowa_liczba_klatek

    def run(self):
        try:
            wyekstraktowane_klatki = ekstracjaKlatek(self.sciezka, self.docelowa_liczba_klatek)
            self.koniec.emit(wyekstraktowane_klatki)
        except Exception as e:
            self.err.emit(str(e))
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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
        self.klatki_input.setPlaceholderText('Wprowadź docelową liczbę klatek')

        self.calkowite_klatki_label = QLabel('Całkowita liczba klatek: -')
        self.calkowite_klatki_label.setStyleSheet("color: gray; font-style: italic;")

        klatki_layout.addWidget(self.klatki_label)
        klatki_layout.addWidget(self.klatki_input)
        klatki_layout.addWidget(self.calkowite_klatki_label)
        main_layout.addLayout(klatki_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Przycisk od ekstrakcji
        self.extract_btn = QPushButton("Ekstraktuj klatki")
        self.extract_btn.clicked.connect(self.start_extract)
        main_layout.addWidget(self.extract_btn)

        # Status
        self.status_label = QLabel('Gotowy do pracy')
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

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
            film.release()
            
            if fps > 0:
                duration = calkowita_liczba_klatek / fps
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                czas_info = f" ({minutes:02d}:{seconds:02d})"
            else:
                czas_info = ""
                
            self.calkowite_klatki_label.setText(f"Całkowita liczba klatek: {calkowita_liczba_klatek}{czas_info}")
            self.calkowite_klatki_label.setStyleSheet("color: white; font-style: normal;")
        else:
            self.calkowite_klatki_label.setText("Całkowita liczba klatek: Błąd odczytu")
            self.calkowite_klatki_label.setStyleSheet("color: red; font-style: italic;")

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

        # Wyłącz UI podczas ekstrakcji
        self.extract_btn.setEnabled(False)
        self.przegladaj_przycisk.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText('Ekstrakcja w toku...')

        # Rozpocznij ekstrakcję w osobnym wątku
        self.extraction_thread = ExtractionThread(sciezka_filmu, docelowa_liczba_klatek)
        self.extraction_thread.koniec.connect(self.ekstrakcja_zakonczona)
        self.extraction_thread.err.connect(self.ekstrakcja_bledu)
        self.extraction_thread.start()

    def ekstrakcja_zakonczona(self, liczba_klatek):
        # Włącz UI ponownie
        self.extract_btn.setEnabled(True)
        self.przegladaj_przycisk.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText(f'Ekstrakcja zakończona! Zapisano {liczba_klatek} klatek.')
        QMessageBox.information(self, 'Sukces', f'Pomyślnie zapisano {liczba_klatek} klatek w folderze ./zdjecia/')

    def ekstrakcja_bledu(self, komunikat_bledu):
        # Włącz UI ponownie
        self.extract_btn.setEnabled(True)
        self.przegladaj_przycisk.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText('Błąd podczas ekstrakcji')
        QMessageBox.critical(self, 'Błąd', f'Wystąpił błąd: {komunikat_bledu}')

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())