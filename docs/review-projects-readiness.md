# PR Review: naprawy modeli i migracji Projects

> **Raport historyczny.** Opisuje moment review przed późniejszym lokalnym włączeniem zmian do `main`. Nie jest bieżącą instrukcją scalania ani oceną nowej architektury. Aktualny stan i gałąź przekazania: [HANDOFF.md](HANDOFF.md).

Data: 2026-09-27. Branch: `v0.7-projects`.

Zakres review: naprawy wykonane po pierwszym przeglądzie, względem zastanego
lokalnego stanu, oraz ich integracja ze startem aplikacji i tablicą zadań.
Nie utworzono zdalnego PR ani nie wykonano merge. Istniejąca lokalna praca
została zachowana; raport nie stanowi pełnego audytu całej tablicy Kanban.

**Blast radius: CRITICAL** — wspólny rejestr modeli, schemat SQLite,
DatabaseManager oraz TaskService. Zmiany obejmują 9 plików implementacji
i 2 nowe pliki testów.

**Security:** brak nowych ustaleń blokujących w naprawach. Wartości enumów
są parametrami SQL; interpolowane identyfikatory pochodzą ze stałych kodu.
Nie dodano zależności runtime ani nowych logów zawierających dane użytkownika.
Nie wykonywano osobnego audytu CVE istniejących zależności.

**Tests:** 68/68, w tym 34 nowe przypadki. Przed naprawami: 33/34.
Pokrycie linii całej aplikacji: 39,8% → 41,3% (+1,5 punktu procentowego).
Nowy moduł migracji: 98% linii. Pylint w trybie errors-only i `git diff --check`
przechodzą.

**Breaking changes:** zapis znanych nazw enumów jest normalizowany do wartości
używanych przez obecną wersję modelu. Stare ograniczenia czasu są naprawiane
w istniejących tabelach. Nie usuwamy rekordów ani kolumn. Migracja nie oferuje
downgrade do dawnego formatu; rollback po błędzie jest transakcyjny.

## MUST FIX — rozwiązane

1. Przywrócono zakaz ustawienia kategorii jako własnego rodzica.
2. Uzupełniono relacje `Project/Task.schedules` i wspólną rejestrację modeli.
   Import pojedynczego modelu nie zależy już od importu GUI lub serwisu;
   uruchomienie DatabaseManager tworzy również `time_schedules`.
3. Konwersja znanych enumów zachowuje starsze zadania. Nieznane wartości
   przerywają migrację, zamiast otrzymywać arbitralnie wybrany status.
4. Poprawiono priorytet operatorów w CHECK: wpis czasu ma dokładnie jednego
   właściciela — zadanie albo projekt. Naprawa obejmuje także starsze tabele.
5. Przypisanie starszych zadań do tablicy zachowuje ich status i nie tworzy
   kolizji kolejności z kartami już obecnymi w danej kolumnie.

W końcowej wersji napraw nie pozostały znane blokujące uwagi z tego zakresu.

## SHOULD FIX — osobne dalsze prace

- Globalne pokrycie jest nadal niskie. Rozbudowana lokalna tablica wymaga
  dalszych testów interakcji, zwłaszcza drag-and-drop i edycji etykiet.
- Usuwanie zadania posiadającego historię czasu jest obecnie odrzucane,
  aby zachować historię. Test potwierdza to zachowanie; docelowy produkt
  powinien mieć świadomie zaprojektowaną archiwizację takich zadań.
- Wraz z dalszymi zmianami schematu warto wprowadzić numerowane migracje
  i jawnie określoną politykę downgrade. Ta naprawa pozostaje idempotentnym
  upgradem istniejącego schematu bez nowego frameworka.

## LOOKS GOOD — dowody

- Testy używają prawdziwego SQLite, a nie mocków wykonujących SQL.
- Sprawdzono obu właścicieli wpisu czasu i oba niepoprawne warianty:
  brak właściciela oraz dwóch właścicieli.
- Test rollback obejmuje dane, ALTER TABLE i wycofanie wcześniejszej
  przebudowy `time_logs`, kiedy późniejsza migracja `time_schedules` zawiedzie.
- Zachowane są dodatkowe kolumny, indeksy oraz działające triggery;
  przebudowa korzysta ze schematu odczytanego z bazy.
- Migracja działa również przy włączonej kontroli kluczy obcych.
- Migracja kopii obecnej bazy użytkownika przeszła. Porównanie istniejących
  wierszy potwierdziło zachowanie danych, z oczekiwaną normalizacją enumów.
  Suma kontrolna oryginalnego pliku pozostała bez zmian.
- Próba konstrukcji okna, nawigacji oraz operacji na projektach i zadaniach
  przeszła w Qt offscreen. Powiązania wszystkich modeli konfigurują się poprawnie.

## Grill-me: wewnętrzna sesja /grilling

Skill `grill-me` zawiera wyłącznie instrukcję uruchomienia `/grilling`.
Zgodnie z prośbą użytkownika sesja ma formę krytycznego self-review,
z odpowiedziami opartymi na kodzie i testach.

**Czy samo przywrócenie zielonych testów rozwiązałoby problem?**
Nie. Dotychczasowe testy nie importowały wszystkich modeli ani nie sprawdzały
rzeczywistych ograniczeń SQL. Dlatego dodano testy integracyjne i niezależny
import modelu w nowym procesie.

**Dlaczego nie dopisać tylko brakujących relacji?**
To pozostawiłoby tworzenie tabel zależne od kolejności importów. Centralny
rejestr usuwa tę zależność, a jawne importy są widoczne dla PyInstallera.

**Czy zwykły create_all naprawi bazę osoby wracającej po kilku latach?**
Nie zmienia istniejących kolumn ani CHECK. Dlatego naprawa działa na istniejącym
schemacie, a testy zaczynają od starszego DDL i danych.

**Czy właściwe jest przypisywanie czasu do zadania albo projektu?**
Tak dla istniejących TimeLog/TimeSchedule: taki zamiar wyrażał oryginalny CHECK.
Nie przenosimy tu projektowanego w osobnym dokumencie modelu WorkSession,
w którym projekt może być obowiązkowym kontekstem sesji zadania.

**Czy przebudowa tabel może usunąć dane, których model już nie opisuje?**
Wariant oparty wyłącznie na aktualnym modelu mógłby to zrobić. Końcowa wersja
odczytuje istniejący schemat, zachowuje dodatkowe kolumny i odtwarza indeksy
oraz triggery. Potwierdzają to testy regresji.

**Czy transakcja SQLAlchemy wystarczy do rollback ALTER TABLE w SQLite?**
Nie przy domyślnym opóźnieniu BEGIN przez sqlite3. Jawny BEGIN obejmuje również
DDL. Test błędu późniejszego kroku potwierdza wycofanie wcześniejszych zmian.

**Co zrobić z wpisem bez właściciela lub nieznanym statusem?**
Przerwać upgrade z czytelnym błędem i zachować istniejące dane. Automatyczne
usunięcie wpisu lub zgadywanie jego właściciela byłoby nieuzasadnione.

**Czy zachowanie tekstu statusu oznacza zachowanie postępu na tablicy?**
Nie. Review wykrył importowanie wszystkich starszych kart do To Do.
Naprawa wybiera standardową kolumnę według statusu i dopisuje kartę po
istniejących kartach. Dla przemianowanych/customowych kolumn bez odpowiadającej
standardowej nazwy pozostaje dotychczasowy fallback do pierwszej kolumny.

**Czy każde uruchomienie ponownie przepisuje dane?**
Nie. UPDATE dotyczy tylko znalezionych starszych nazw enumów, a przebudowa
tabel tylko rozpoznanego błędnego CHECK. Test dwukrotnego uruchomienia
potwierdza zachowanie historii oraz nowych kart, etykiet i checklist.

## Checklist review

- [x] Zakres napraw wyraźnie opisany i oddzielony od zastanej lokalnej pracy.
- [x] Powód zmian oraz zachowanie przed/po udokumentowane.
- [x] Zdalny PR i ticket: N/A — przegląd lokalnego diffu.
- [x] Brak niezwiązanych zmian w interfejsie użytkownika.
- [x] Zmiana reprezentacji danych opisana.
- [x] Sprawdzeni bezpośredni konsumenci zmienionych modeli.
- [x] Sprawdzony start DatabaseManager i bezpośrednie użycie TaskService.
- [x] Rejestracja wszystkich relacji sprawdzona.
- [x] Utworzenie kompletnego schematu sprawdzone.
- [x] Brak nowych zmiennych środowiskowych lub kluczy konfiguracji.
- [x] Brak nowych sekretów w naprawach.
- [x] Wartości SQL przekazywane jako parametry.
- [x] Dynamiczne identyfikatory SQL pochodzą ze stałych kodu.
- [x] Nieznane wartości enumów odrzucane jawnie.
- [x] Niepoprawne przypisanie wpisu czasu odrzucane przez bazę.
- [x] Brak nowych logów zawierających tytuły okien lub treść zadań.
- [x] Auth/CORS/upload/XSS: N/A — brak takich zmian.
- [x] Nowe zależności runtime/CVE nowych zależności: N/A.
- [x] Nowe zachowania publiczne pokryte testami przez rzeczywiste serwisy.
- [x] Test poprawnego zapisu i odczytu wpisu zadania.
- [x] Test poprawnego zapisu i odczytu wpisu projektu.
- [x] Test błędu dla braku właściciela.
- [x] Test błędu dla dwóch właścicieli.
- [x] Test migracji wszystkich znanych priorytetów i statusów.
- [x] Test zachowania postępu starszych zadań na tablicy.
- [x] Test zachowania kolejności nowych i starszych kart.
- [x] Test powtórnego uruchomienia upgrade.
- [x] Test nieznanego enuma i rollback.
- [x] Test starego wpisu bez właściciela i rollback DDL.
- [x] Test dodatkowych kolumn w starszej tabeli.
- [x] Test zachowania indeksu i działającego triggera.
- [x] Test migracji przy włączonych foreign keys.
- [x] Test zachowania historii przy próbie usunięcia zadania.
- [x] Istniejące testy nie zostały usunięte ani osłabione.
- [x] Brak spadku pokrycia całej aplikacji.
- [x] Brak usuwania kolumn lub istniejących rekordów.
- [x] Przebudowa tabel czasu ma wycofanie w razie błędu.
- [x] Brak nowych zapytań wykonywanych osobno dla każdej starszej karty.
- [x] Normalizacja nie wykonuje zbędnych UPDATE na poprawnych danych.
- [x] Brak nowej ciężkiej zależności dla migracji.
- [x] Błędy upgrade propagowane; nie są zamieniane w ostrzeżenie i ignorowane.
- [x] Pylint errors-only i kontrola whitespace przeszły.

## Granice weryfikacji

Testy wykonano w tymczasowych kopiach na Pythonie 3.14.7, PySide6 6.10.2,
SQLAlchemy 2.0.46 i pytest 8.3.4. GUI sprawdzano w trybie offscreen.
Nie wykonano budowania instalatorów ani pełnej próby systemowego watchera,
traya i autostartu na Linux oraz Windows. Nie sprawdzono automatycznego downgrade
schematu ani całego zastanego interfejsu tablicy. Nieobjęta testem linia
migracji dotyczy odmowy przebudowy, gdy parser nie rozpozna jednoznacznie CHECK.
