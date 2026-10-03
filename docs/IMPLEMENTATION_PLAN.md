# Plan realizacji FocusWatch

Stan: **03.10.2026**. Plan wykonania, nie ukończona implementacja i nie automatyczne zatwierdzenie stosu przez użytkownika. Kontekst: [brief](PROJECT_BRIEF.md), [decyzje](architecture/DECISIONS.md), [handoff](HANDOFF.md), [architektura referencyjna](architecture/REBUILD_BASELINE_2026-10-03.md).

## Co zostało domknięte na poziomie dokumentacji

Utrwalono płatny model produktu, wykluczono znajomość technologii przez właściciela jako kryterium, skorygowano ekonomię na koszt per płacący klient i wskazano jeden wariant referencyjny: Rust + SQLite + Electron/React/TypeScript. Prywatność i chmura mają jawne zależności, a nie pozornie zatwierdzony jeden stos.

**Nie wykonano nowego agenta, UI, syncu ani wdrożenia.** Historyczne benchmarki pozostają w [badaniu wrześniowym](research/2026-09/README.md).

## Najbliższy zakres: P0 — kontrakt i szkielet lokalnego przekroju

Przy rozpoczęciu implementacji nie wracać do porównywania całego rynku. Najpierw zweryfikować checkout, środowisko i dostępne OS; następnie zapisać wybory pierwszego przekroju zgodnie z zakresem zlecenia.

Proponowana nowa przestrzeń kodu, bez ruszania starego `focuswatch/`:

```text
crates/focuswatch-domain/       przedziały, reguły, korekty; bez OS/UI/sieci
crates/focuswatch-agent/        lifecycle, adaptery, SQLite, query API
apps/desktop/                  Electron + React/TypeScript
contracts/                     formaty, jednostki, wersje, wspólne przykłady
```

Nie tworzyć pustych usług, pluginów i mikroserwisów na każdy przyszły moduł. Rozszerzenie przeglądarki dołącza w P1; chmura w P4, po decyzji prywatności.

**Wynik P0:** odtwarzalny build z zapisanymi wersjami i lockfile, testy domeny na syntetycznych fixtures, tymczasowa baza poza katalogiem danych starego programu, minimalne wersjonowane IPC i raport z syntetycznego wejścia. P0 nie oznacza zaliczenia collectora Windows/X11.

Kontrakt obejmuje `[start,end)`, UTC i strefę raportu, jakość/pokrycie odczytu, stabilne źródło i urządzenie, generację/sekwencję, obserwacje oddzielone od interpretacji i korekt. Liczniki 64-bitowe nie przechodzą niejawnie przez JavaScript Number. Otwarty przedział po awarii nie otrzymuje zmyślonej długości.

**Odbiór P0:** scenariusze T01–T10 z [macierzy odbioru](architecture/PROTOTYPE_ACCEPTANCE.md) mają deterministyczne wejście i oczekiwane wyniki. Wykonane testy oraz brakujące platformy są odnotowane osobno. Kod nie czyta prywatnej historii, nie włącza autostartu i nie kontaktuje się z chmurą.

## P1 — rzeczywisty pomiar i trwały zapis

Agent działa w sesji użytkownika, niezależnie od GUI i przeglądarki. Adaptery: Windows 11 i Arch/dwm/X11, jawnie różne możliwości. Rozszerzenie rozdziela aktywną kartę i dostępne sygnały mediów w tle. Native messaging host nie staje się głównym daemonem. Cały agent nie wymaga administratora z powodu przyszłych blokad.

Zapis obserwacji i outbox jest atomowy. Wybrane źródła można wyłączyć, pauza ma widoczny stan, brak uprawnień lub miejsca na dysku jest błędem/luką, nie zerową aktywnością. IPC ma ograniczone metody, rozmiar, kolejki i tożsamość klienta; renderer nie dostaje bazy ani dowolnego shell.

**Odbiór:** restart/kill, suspend/resume, lock, restart źródła, utrata uprawnień i dysku; brak podwójnego zaliczania; pomiar po zamknięciu UI i bez sieci. Mierzyć agent oddzielnie od UI: CPU w jednostkach jednego rdzenia, pamięć drzewa procesów, wakeups i zapisy. Każdy OS zaliczamy tylko na podstawie jego testu. Testy T11–T15.

## P2 — jeden rzeczywisty raport i korekta

Dostarczyć raport dnia i okresu, równoległe źródła, kategorię/regułę, ręczną korektę, eksport i usuwanie. Query API zwraca ograniczone strony/agregaty, nie całe lata do UI. Projekcje są wersjonowane i odbudowywalne, korekty pozostają po przeliczeniu.

Pierwszy przekrój działa bez AI i serwera. To etap techniczny, nie decyzja o darmowym planie lub publicznym produkcie bez licencji.

**Odbiór:** filtrowanie, pan/zoom, klawiatura, skalowanie, stany błędów i ładowania na Windows oraz Arch/dwm; poprawne sumy i widoczne pokrycie/niepewność. Czas zapytania oddzielić od czasu renderowania. Zmierzyć start, pamięć, długie idle i interakcje przy ograniczonym widoku oraz historii syntetycznej. Testy T16–T18.

Electron jest implementacją referencyjną. Tauri z tym samym frontendem sprawdzać, gdy rzeczywisty koszt UI lub dystrybucja podważą wybór. Qt Quick/Avalonia wracają do oceny przy istotnej przesłance, nie jako równoległe pełne produkty. Nie używać wyniku Canvas/Xvfb jako odbioru P2.

## P3 — instalacja, aktualizacje i płatny produkt offline

Od pierwszego instalowalnego wydania wersjonować schemat, IPC oraz zgodność agent/UI/rozszerzenie. Sprawdzić czystą instalację, restart systemu, aktualizację z poprzedniej nowej wersji, przerwanie aktualizacji, bezpieczny backup i odtworzenie. Nie kopiować samej aktywnej bazy z pominięciem WAL. Przed dystrybucją zewnętrzną rozstrzygnąć podpisy i licencje rzeczywistych zależności.

Dodać model konta, urządzenia i uprawnienia do produktu oddzielny od danych obserwacyjnych i kluczy historii. Przy płatnościach cyklicznych lub licencji odnawianej online rozważyć podpisane, czasowe uprawnienie offline; okres ważności nie jest ustalony. Błąd sieci lub webhook płatniczy nie może po cichu usuwać historii. Zasady dalszego zbierania po wygaśnięciu wymagają osobnej decyzji produktu.

**Odbiór:** bez utraty danych i niezgodnych procesów po przerwanej aktualizacji; brak prywatnych tytułów/URL w domyślnych logach; eksport/odzyskanie opisane. Testy stanów licencji: poprawna, wygasła, offline, duplikat i spóźniony webhook. Wybrać konkretnego operatora płatności przed integracją, nie przed testami lokalnego rdzenia. T19–T20.

## P4 — po decyzji prywatności dwa urządzenia i chmura

Przed uploadem prawdziwej historii wybrać granicę odczytu przez serwer, klucze i odzyskiwanie, region, retencję/usuwanie, oczekiwany czas odtworzenia oraz utratę jeszcze niewysłanych danych. Wariant referencyjny E2EE: TypeScript/Workers + R2 + DO. Wariant czytelny: serwis OCI + PostgreSQL + obiekty. Dostawca nie jest bezwarunkowo przyjęty.

Historia: trwały ACK dopiero po zapisie i odnajdywalnym zarejestrowaniu paczki; idempotentne retry. Edycje: rewizje i jawne konflikty. Kontekst: aktualny snapshot, wersja, TTL i reconnect, a nie kolejka nieaktualnych interwencji. Limity i deduplikacja powiadomień między urządzeniami należą do polityki.

Zacząć od prostego uploadu bez dodatkowego trwałego bufora tylko dla oszczędności. Parametr uploadu porównać w 60/300 s, oddzielnie od checkpointu i realtime; nie jest to ustalone SLA. Przed wzrostem archiwum zaprojektować łączenie paczek, manifesty, tombstones, odzyskanie i usuwanie. E2EE nie pozwala kompresować ciphertextu tak jak jawnych danych.

**Odbiór:** dwa rzeczywiste urządzenia, offline, retry po utracie ACK, kolejność, odwołanie urządzenia, izolacja kont, restart serwera, wolny odbiorca, odtworzenie nowego urządzenia, stare urządzenie nie przywraca usuniętej historii; zgodność różnych wersji klienta. T21–T24.

**Koszt:** osobno konta płacące, trial i konta przechowujące archiwum; skale 10/100/1000/10000; normalne i intensywne użycie; koszt całkowity, per konto, API/realtime/storage/odczyty/auth/backup/logi/AI. Opłaty sprzedażowe i obsługa są osobne. Miesięczne scenariusze nie ustanawiają subskrypcji. Brakujące składniki oznaczać jako niepoliczone, nie zero. Sam plan nie upoważnia do płatnego wdrożenia.

## P5 — interwencje i blokowanie

Najpierw deterministyczne sugestie, limity przerwań, wyciszenie i manualny override. Blokady przez adaptery z minimalnymi uprawnieniami, nie uprzywilejowane całe GUI. Nie zakładać kontroli nad administratorem jego urządzenia.

**Odbiór:** włączenie, wyłączenie, override, restart, offline, utrata uprawnień i przeterminowana polityka; brak niejawnej trwałej blokady. Użytkownik widzi przyczynę interwencji. AI nie przyznaje sobie uprawnień. Lokalne reguły mogą powstać przed chmurą; kolejność etapów określa zależności, nie zabrania niezależnej pracy.

## P6 — profil i AI

Budować widoczne, poprawialne i usuwalne deklaracje oraz hipotezy. Ocenić deterministyczny baseline i modele lokalne/chmurowe na tych samych scenariuszach. Model otrzymuje kontrolowane narzędzia i wybrane dane; tytuły okien/treści integracji nie są instrukcjami systemowymi.

**Odbiór:** trafność i liczba odrzuconych sugestii, koszt przerwania, opóźnienie, CPU/RAM/bateria i koszt per konto; brak niejawnego rozszerzania autonomii. Użytkownik może wyłączyć AI i usunąć profil. Brak wykazanej jakości oznacza funkcję opcjonalną, nie zastąpienie pomiaru domysłem.

## Co nie blokuje P0

Cena detaliczna, ostateczny LLM, mobile, Wayland i smart glasses nie blokują kontraktu i syntetycznego lokalnego przekroju. Prywatność blokuje prawdziwy sync i obietnice chmurowe, ale nie P0/P1/P2. Dostawca chmury nie musi być wybrany, aby sprawdzić niezależny agent i UI.

Po każdym etapie aktualizować HANDOFF i statusy. Test niewykonany oznacza `not_run`, nie zaliczenie. Nie uznawać skompletowania planu za zakończenie etapu produktu.
