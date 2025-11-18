Potrzeba pmvs2 i cmvs (chociaz jeszcze nie robilem nic tak duzego zeby musiec rozbijac z tym cmvs)
https://github.com/pmoulon/CMVS-PMVS.git
skompilowałem tam jak jest z tym CMake build system, potem po prostu pliki wykonywalne 
przenioslem do ./dependencies chociaz to w sumie my jestesmy ich dependency ¯\_(ツ)_/¯

# Nasz program

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Proin vulputate facilisis tellus, vitae blandit libero lobortis vitae. Vivamus facilisis aliquet fringilla. Donec laoreet nunc eget feugiat faucibus. Cras vitae nisl purus. Suspendisse lobortis lectus volutpat nisl mattis luctus. Suspendisse eu sem dapibus purus feugiat dictum a eget dolor. Sed vel ex quis ipsum dignissim pellentesque quis non ipsum


## Instalacja
[repo CMVS/PMVS](https://github.com/pmoulon/CMVS-PMVS.git)
Nunc placerat ex quis hendrerit imperdiet. Nulla consequat ultricies justo, eget vehicula libero porttitor in. Etiam turpis nisi, elementum ut est vitae, imperdiet efficitur arcu. Cras ultrices iaculis magna et sagittis.

## Flagi
Program przyjmuje flagi:
- **-o <nazwa>**
        pozwala okreslic nazwe wyjściowej gęstej rekonstrukcji
- **-r**
        pozwala na zresetowanie rekonstrukcji, ktore mogly wczesniej powstać. Także wymusza wykonanie programu.
- **-f**
        wymusza wykonanie całego pipeline'u, ale z zachowaniem pewnych rzeczy ktore usuwa -r, np matched features
- **-nrthreads <n>**
        okresla ilość wykorzystywanych wątków logicznych w programie -- ogolnie to nie powinno chyba byc wieksze niz prawdziwa ich ilosc, mozna zrobic ze -1 uzywa wszystkich dostepnych
- **-l <0|1|2>**
        pozwala okreslic poziom zlozonosci, 0 to minimalna, szybka i najgorsza, 1 to średnia, 2 to najbardziej wymagająca (moze wyjsc zaszumione, ale to mozna zmienic w opcjach)

## Opcje
    Są w pliku **options.yaml** w katalogu work. Domyslnie są tam trzy, te ktore opisalem wyzej, ale potem moznaby zrobić że użytkowik z GUI może niektóre opcje ustawić sobie i np jako kolejny tam wpis.

## Logi
    Plik z logami jest w **work/log**. Zapisuje tam pare rzeczy razem z godzinami -- mozna dodać, można odjąć. Nie zrobiłem póki co jakiegos resetowania go czy coś, po prostu nadpisuje. Można zrobić, że np po 2000 linii kasuje ale to nigdy ich tam nawet pewnie tyle nie bedzie.
