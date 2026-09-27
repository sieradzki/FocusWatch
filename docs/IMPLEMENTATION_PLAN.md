# Plan realizacji FocusWatch

Stan: 27.09.2026. Plan dalszej pracy, **nie wykonana implementacja ani zatwierdzenie stosu technologicznego**. Cel i zakres opisuje [PROJECT_BRIEF.md](PROJECT_BRIEF.md), status wyborów [DECISIONS.md](architecture/DECISIONS.md), a uruchomienie pracy na innym komputerze [HANDOFF.md](HANDOFF.md). Uzasadnienia i ograniczenia pomiarów są w [badaniu architektury](research/2026-09/README.md).

## Wymagania a propozycje

| Status | Co oznacza dla wykonania |
| --- | --- |
| Wymagania produktu | Osobisty companion projektowany od początku jako produkt komercyjny; wiele urządzeń i wieloletnia historia; równoległy kontekst zamiast samego foreground; użyteczne raporty, personalizacja, ręczna korekta i kontrola użytkownika; docelowo rekomendacje, plany i blokowanie. Pomiar ma być użyteczny bez LLM i bez deklarowania kierunku życiowego |
| Kolejność proponowana przez badanie | Najpierw lokalny agent i raporty na Windows oraz Arch/X11, potem pełna synchronizacja, kolejne platformy i inteligentniejsze interwencje. Aplikacja webowa nie jest warunkiem rozpoczęcia |
| Rekomendacje inżynierskie, wymagające rozstrzygnięcia w rejestrze decyzji | Nowa implementacja w tym samym repo; Rust, Electron/React, SQLite, Axum/PostgreSQL, GCP, OCI/OpenTofu. Dokument rekomendujący rozwiązanie nie oznacza jego akceptacji przez użytkownika. Nie ma obowiązku zachowania starego UI, schematu ani feature parity |
| Proponowane budżety, nie wymagania użytkownika | p95 dostarczenia zmiany lokalnym regułom <1 s oraz drugiemu aktywnemu urządzeniu <5 s. Wymagają określenia sprzętu, sieci i granic pomiaru. Próba 10 mln obserwacji to punkt odniesienia, nie limit produktu; badanie nie ustanawia zaakceptowanego limitu RAM UI |

Decyzję techniczną zapisujemy wraz ze statusem i przesłankami zgodnie z zakresem udzielonej autonomii. Nie przekształcamy samodzielnie rekomendacji badania w wymagania produktu. Poniższe etapy określają zależności; prace niezależne mogą toczyć się równolegle.

## 0. Zweryfikować środowisko i wybrać pierwszy przekrój

Przeczytać trzy dokumenty wskazane na początku; sprawdzić bieżący commit, branch, lokalne zmiany i dostępne systemy testowe. Ustalić docelowy proces uruchamiania, wersje narzędzi i sposób odtwarzania zależności. Artefakty `build/research` są lokalne i ignorowane przez Git; nie zakładać, że istnieją na drugim komputerze. Nie powtarzać całego badania tylko po to, aby rozpocząć implementację.

**Odbiór:** świeży checkout pozwala odtworzyć minimalny build i uruchomić test bez prywatnych danych, poświadczeń ani chmury; instrukcja zawiera komendy dla wybranego stosu. W rejestrze decyzji zapisano wybory potrzebne dla pierwszego przekroju i to, co pozostaje otwarte. Dostępność Windows/X11 jest jawna — brak testu na jednym z nich nie jest oznaczany jako zaliczenie platformy. Ustalono sposób pomiaru stałego kosztu agenta oddzielnie od otwartego UI.

## 1. Utrwalić kontrakt danych i czasu

Zdefiniować obserwację, źródło, urządzenie, zakres czasu, jakość odczytu oraz pochodzenie danych. Oddzielić fakty od interpretacji, intencji, profilu, korekt i polityk działania. Określić stabilną tożsamość zdarzeń, wersjonowanie, luki, zmianę zegara, suspend/resume i kolejność zdarzeń. Zdefiniować granice prywatnych metadanych zbieranych na starcie; zakres nie obejmuje domyślnie treści ekranów ani nagrań audio. Opisać query API dla raportów oraz pierwszeństwo korekt wobec ponownego przeliczenia reguł.

**Odbiór:** wersjonowane przykłady i testy kontraktu obejmują VSCode oraz grający stream, dwa aktywne urządzenia, idle, brak uprawnień, lukę odczytu, zmianę strefy/czasu, duplikat i spóźnione zdarzenie. Czas osoby jako unia przedziałów i czas poszczególnych źródeł dają celowo różne wyniki. Żaden przykład nie utożsamia foreground z uwagą ani współwystępowania z wpływem przyczynowym. Korekta użytkownika zachowuje pochodzenie i nie znika po przebudowie projekcji.

## 2. Zbudować lokalnego agenta i źródła

Wydzielić proces sesji użytkownika, adapter OS, źródło przeglądarkowe oraz trwały zapis z atomowym outbox. Zacząć od Windows i X11, jawnie opisując różnice możliwości. Źródło przeglądarkowe powinno rozróżniać aktywną kartę i dostępne metadane mediów w tle. UI komunikuje się przez ograniczone, wersjonowane IPC; zamknięcie UI lub przeglądarki nie kończy innych źródeł pomiaru. Cały agent nie wymaga uprawnień administratora z powodu przyszłych blokad.

**Odbiór:** pomiar działa bez UI i sieci, a pauza zbierania ma widoczny stan. Zapis i outbox są atomowe; restart odtwarza ostatni trwały stan bez podwójnego zaliczenia czasu. Sprawdzono awarię procesu, suspend/resume, utratę uprawnień, brak miejsca i niedostępne źródło; luki pozostają widoczne. Zmierzono CPU, pamięć i częstotliwość zapisów w zwykłym użytkowaniu. Użytkownik może wyłączyć wybrane źródło i zweryfikować zakres zbierania.

## 3. Dostarczyć użyteczne raporty i korekty

Zbudować raport dnia i okresu, widok równoległych źródeł, kategorie/reguły, ręczne korekty oraz eksport. Raport korzysta ze stronicowania, ograniczonego zakresu i odbudowywalnych projekcji; nie ładuje lat obserwacji do UI. Pokazuje pokrycie pomiarem i niepewność. Pierwsza wersja działa bez AI i konta chmurowego.

**Odbiór:** na znanych scenariuszach sumy odpowiadają kontraktowi, a szczegóły wyjaśniają agregat. Zmiana reguł ma określony zakres przeliczenia; ręczne korekty pozostają zachowane. Eksport obejmuje udokumentowane jednostki, wersję i pochodzenie. Usunięcie lokalnych danych aktualizuje projekcje. Zmierzono czas zapytania oddzielnie od renderowania, responsywność i pamięć przy długiej historii; UI obsługuje klawiaturę, skalowanie oraz stany ładowania i błędów na obu pierwszych platformach.

## 4. Przygotować dystrybucję i codzienne używanie

Od pierwszego instalowalnego wydania utrzymywać wersje schematu i protokołu, instalację/odinstalowanie, aktualizację agenta i UI oraz diagnostykę bez domyślnego wysyłania historii. Sprawdzić warunki licencji rzeczywistych zależności i dystrybucji. Przygotować procedurę obsługi uszkodzonej bazy, backupu i odtworzenia. Pierwszy użytkownik jest właścicielem projektu, ale ścieżka instalacji ma działać poza maszyną deweloperską.

**Odbiór:** test czystej instalacji, restartu systemu, aktualizacji z poprzedniej nowej wersji i przerwanej aktualizacji; brak utraty danych lub pozostawienia niezgodnych procesów. Przed dystrybucją zewnętrzną określono podpisywanie i weryfikację pakietów. Diagnostyka ujawnia błędy źródeł i wersje bez niejawnego dodawania prywatnych metadanych. Opisane są eksport, odzyskanie danych i skutki odinstalowania.

## 5. Po rozstrzygnięciu prywatności połączyć dwa urządzenia

Najpierw wybrać zakres cloud-readable lub E2EE, model kluczy i odzyskiwania, lokalizację danych oraz zasady retencji/usuwania. Dopiero na tej podstawie utrwalić protokół rzeczywistych danych i część serwerową. Historia korzysta z trwałego ACK i idempotentnego ponawiania; bieżący kontekst ma osobny kanał najnowszego stanu, wersje i TTL. Nie traktować minutowej synchronizacji historii jako realtime. Dla wielu instancji serwera zapewnić współdzielony stan i resync po utracie powiadomień.

**Odbiór:** dwa rzeczywiste urządzenia poprawnie obsługują offline, retry po utracie ACK, zmianę kolejności, reconnect, restart serwera, odebranie dostępu urządzeniu i odświeżenie kontekstu. Brak dostępu między kontami. Nieaktualny stan staje się nieznany; powiadomienie nie pojawia się równocześnie na obu urządzeniach bez uzgodnionej polityki. Usuwanie propaguje się i nie jest cofane przez stary upload; skutki dla archiwów i backupów są określone. Zmierzono kompletną ścieżkę opóźnienia oraz koszt z TLS, auth, bazą i fan-out. Pojemność lokalnego relay nie zastępuje tego pomiaru.

Wdrożenie wymaga wybranego dostawcy i rozliczalnego zakresu zasobów; kontenery i IaC pozostają propozycjami do zapisania w decyzjach. Sam ten plan nie upoważnia do utworzenia płatnej infrastruktury. Mobilne źródła można dołączać do tego samego kontraktu po osobnej ocenie uprawnień i pracy w tle; nie obiecujemy im możliwości collectora desktopowego.

## 6. Dodać dobrowolne interwencje i blokowanie

Najpierw dostarczyć deterministyczne reguły sugestii, wyciszenie, limity przerwań i manualny override. Blokady implementować przez adaptery platformowe, z osobną granicą uprawnień. Zakres blokady i sposób odwołania mają być zrozumiałe przed włączeniem. System ma wspierać decyzje użytkownika; nie zakładamy kontroli nad administratorem własnego urządzenia.

**Odbiór:** scenariusze włącz/wyłącz/override, restart, utrata sieci i uprawnień oraz nieaktualna polityka nie powodują niejawnego trwałego zablokowania. Zapis wyjaśnia, jaka reguła i dane spowodowały interwencję. Sugestia modelu nie może ominąć uprawnień ani limitów. Lokalne reguły można dostarczyć przed chmurą; blokady nie zależą od powodzenia inferencji.

## 7. Oceniać AI na wiarygodnych danych

Rozszerzać opcjonalne intencje, cele i preferencje oraz potwierdzane hipotezy o wzorcach użytkownika. Porównać deterministyczny punkt odniesienia z kandydatami lokalnymi/chmurowymi na tych samych scenariuszach. Model otrzymuje kontrolowane zapytania i wybrane dane, działa w osobnym workerze oraz proponuje interpretacje lub plan w granicach polityki.

**Odbiór przed automatycznym zwiększaniem zakresu działania:** określony zbiór scenariuszy i sposób oceny, liczba nietrafionych/przerwanych sugestii, korekt użytkownika, opóźnienie, CPU/RAM oraz koszt. Użytkownik widzi i może poprawić lub usunąć profil oraz wyłączyć AI. Domysł modelu nie staje się faktem o osobowości. Brak potwierdzonej jakości oznacza pozostawienie funkcji jako propozycji, a nie zastąpienie nią reguł pomiaru lub uprawnień.

## Decyzje otwarte i ich rzeczywisty wpływ

| Otwarte zagadnienie | Co blokuje | Co można robić wcześniej |
| --- | --- | --- |
| E2EE, dostęp serwera do treści, klucze i odzyskiwanie | Docelowy sync prywatnych danych, analitykę treści w chmurze i obietnice prywatności | Kontrakt danych, lokalny zapis, raporty, reguły, syntetyczne testy transportu |
| Retencja, szczegóły lokalne a archiwum, usuwanie backupów | Ostateczne polityki magazynowania i koszt produktu | Wersjonowane dane/projekcje, lokalny eksport/usuwanie, pomiary rozmiaru |
| Stos implementacyjny i dostawca | Kod zależny od konkretnego frameworka, wydania i wdrożenie | Scenariusze kontraktu, granice procesów i API, kryteria odbioru |
| Jakość AI i wybór modeli | Obietnice trafności oraz autonomię opartą na modelu | Użyteczny pomiar, agregaty, personalizację reguł i dobrowolne interwencje |
| Zakres mobile/Wayland/przyszłych urządzeń | Deklarację wsparcia konkretnej platformy i blokad | Rozszerzalny kontrakt źródeł oraz pierwszy przekrój Windows/X11 |

Po każdym etapie aktualizować status decyzji, działające komendy i następną konkretną czynność w dokumentacji przekazania. Odbiór opierać na zachowaniu produktu i sprawdzonych ograniczeniach; same mikrobenchmarki ani kompletność tego planu nie oznaczają zakończonego etapu.
