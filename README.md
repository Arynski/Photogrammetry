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
Są w pliku **options.yaml** w katalogu work. Domyslnie są tam trzy, te ktore opisalem wyzej, ale potem moznaby zrobić że użytkowik z GUI może niektóre opcje ustawić sobie i np jako kolejny tam wpis. Informacje o opcjach pmvsa mam [stąd](https://www.di.ens.fr/pmvs/documentation.html).
Z tego co sobie zanotowałem to ogolnie to sie zachowuje tak, że:
1. max_features, im mniej tym szybciej, ale ma mniej cech wiec mniej dokladnie
2. num_nearest_neighbors, nie do konca wiem, ale chyba jak malo to gorzej i szybciej
3. num_checks, podobnie???
4. ba_global_max_num_iterations, on tam co jakis czas robi sobie te bundlowanie globalsuw i tutaj po prostu im mniej tym mu to mniej zajmuje i tez mniej dokladniejszy potem jest wynik, moga sie pojawic jakies szumy albo wiele rekonstrukcji czy cos
5. level, im wieksze tym szybciej i bardziej sparse, minimalnie 0, zalecane 1.
6. threshold, ogolnie to chyba im wieksze tym bardziej rygorystyczine dopasowuje -- moze zmiejszac szumy. Chyba zbyt nie wplywa na szybkosc.
7.  useVisData, colmap je daje wiec 1
8.  sequence, jesli obrazy sa sekwencyjnie to tu mozna podac jakas liczbe i to bedzie bralo tyle ile sie poda (no chyba ze -1 to wtedy nie) obrazow do tylu i do przodu do dopasowywania. Powinno zalezec od tego jak szybko sie krecimy dookola obiektu, bo bardzo szybko to nie moze byc za duze, ale jak jest duzo zdjec to tak. Pewnie by spowalniało jak duzo choc nie wiem.
9.  quad, zwiekszanie pozwala na bardziej zaszumione z jakiegos powodu
10. maxAngle, w stopniach maksymalny kąt miedzy dopasowanymi zdjeciami (ich kamer pewnie), im wieksze tym bardziej zaszumione i pozwala na rekonstrukcje rzeczy dalekooooooooo dalekoo
11. csize, to generalnie dziala przez rozpatrywanie takich bloczkow pixeli (zreszta cos nawet o Bayerze tam pisza ze inacze to bez sensu). Te bloczki sa wlasnie csize x csize. Domyślnie 2, ale mozna dac wiecej to bedzie oczywiście szybciej i mniej dokladnie.

## Logi
Plik z logami jest w **work/log**. Zapisuje tam pare rzeczy razem z godzinami -- mozna dodać, można odjąć. Nie zrobiłem póki co jakiegos resetowania go czy coś, po prostu nadpisuje. Można zrobić, że np po 2000 linii kasuje ale to nigdy ich tam nawet pewnie tyle nie bedzie.
