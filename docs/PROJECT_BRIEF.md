# FocusWatch — brief produktu

Stan: **03.10.2026**. Dokument utrwala wymagania i intencje użytkownika. Wybory techniczne mają osobny [rejestr statusu](architecture/DECISIONS.md). Nowa implementacja nie powstała.

## Cel

Osobisty companion do rozumienia aktywności, wspierania celów i korygowania działań. Pierwszy użyteczny rezultat jest dla właściciela projektu, ale projekt od początku jest **płatnym produktem B2C**, nie narzędziem nadzoru pracowników.

Docelowo system może znać plany, istotne wartości, cele, preferencje i powtarzające się trudności. Ma pomagać w planowaniu i dobieraniu rekomendacji. Użytkownik nie musi deklarować kierunku życiowego, żeby aplikacja była użyteczna. Sposób budowania profilu pozostaje do rozstrzygnięcia.

## Doprecyzowania użytkownika z 03.10.2026

- Produkt ma być z założenia płatny i rozsądnie wyceniony. Nie przyjmujemy freemium ani modelu, w którym mała grupa płacących utrzymuje dużą darmową populację, jako bazowego scenariusza. Cena, sposób płatności, okres próbny i limity urządzeń nie zostały ustalone.
- Znajomość języka lub wcześniejsze doświadczenie właściciela **nie są kryterium wyboru technologii**. Rozwój ma uwzględniać pracę agentów AI. Nadal oceniamy faktyczny koszt weryfikacji, integracji, wydań i utrzymania produktu.
- W kosztorysach należy pokazywać koszt całkowity i koszt na płacącego klienta, wraz z zakresem. Rachunek za R2 nie jest pełnym kosztem usługi. Niewielka oszczędność infrastruktury nie uzasadnia automatycznie większej złożoności lub gorszej niezawodności.

Te doprecyzowania nie oznaczają akceptacji E2EE, Cloudflare, subskrypcji ani całego rekomendowanego stosu.

## Wymagania i kierunek

- **Cross-platform przez companiony i adaptery.** Pierwsze środowiska: Windows 11 i Arch Linux/dwm/X11. Później macOS, wybrane środowiska Wayland i osobne aplikacje mobilne. Smart glasses pozostają możliwością dalszego rozwoju, nie wybranym SDK.
- **Historia liczona latami**, z wielu komputerów, przeglądarki i innych urządzeń. Chmura docelowo łączy historię; jej dostęp do treści zależy od decyzji prywatności.
- **Równoległe źródła.** Edytor na foreground i stream w tle mogą trwać jednocześnie. Nie oznacza to podwójnego czasu człowieka ani uwagi 50/50. Media nie otrzymują automatycznie negatywnej oceny.
- **Raporty i korekty.** Wydajne, atrakcyjne raporty, agregacja, zejście do szczegółów, reguły i manualny override. Podstawowa wartość nie zależy od LLM.
- **Mało ręcznej obsługi.** Sugestie i plany docelowo korzystają z kontekstu, ale autonomia i uprawnienia działań są osobnymi decyzjami.
- **Dobrowolne blokowanie** należy do docelowego produktu. Wymaga adapterów i uprawnień; nie obiecujemy identycznych możliwości na każdym OS.
- **Personalizacja** obejmuje reguły, kategorie, zakres pomiaru, preferencje, interwencje i korekty. Nie wymusza publicznych pluginów w pierwszej wersji.
- Początkowo zbieramy **metadane i dane jawnych integracji**. Screenshoty, OCR, audio i pełna treść stron nie należą do pierwszego zakresu.
- Lokalny pomiar i raporty są projektowane do pracy bez sieci. Nie wynika z tego darmowość ani brak potrzeby późniejszego zaprojektowania licencji offline.

## Założenia, których nie należy dodawać

Nie ma wymogu zachowania starego UI, API, schematu, feature parity, Kanbana ani automatycznej migracji historii. Nie ma obecnie grupy zewnętrznych użytkowników. Pełny rewrite jest dopuszczalny; to nie zgoda na usunięcie danych.

Pełna aplikacja webowa nie jest wymagana. Portal konta i płatności to oddzielny zakres. Cloudflare nie jest preferowaną chmurą użytkownika, a Rize i ActivityWatch nie są zamkniętą listą konkurencji.

Wyższy koszt początkowy może mieć uzasadnienie utrzymaniowe, ale nie oznacza zgody na samodzielną administrację VPS lub nieograniczoną złożoność. Rust, Electron, React, GCP, Cloudflare i OpenTofu nie są narzuconymi wymaganiami.

Liczby 300 MiB, 1/5 s, 90 dni i 3840 obserwacji/dzień są historycznymi propozycjami lub parametrami badań, nie zaakceptowanym SLA. Przykładowe ceny i budżety z rozmowy również nie są cennikiem produktu.

## Otwarte kwestie i ich zależności

1. **Prywatność:** E2EE, dane czytelne dla serwera lub wydzielone podsumowania; klucze, odzyskiwanie, retencja, lokalizacja. Rozstrzygnąć przed sync prawdziwej historii, nie przed syntetycznymi testami lokalnego rdzenia.
2. **AI:** miejsce inferencji, jakość, koszt, opóźnienia i autonomia. Nie zmierzono skuteczności rekomendacji. Nie blokuje pomiarów, raportów i reguł.
3. **Dystrybucja:** docelowe budżety CPU/RAM/baterii, dokładny zakres wsparcia OS, podpisy, aktualizacje i zachowanie bez uprawnień.
4. **Sprzedaż:** cena, model rozliczeń, okres próbny, urządzenia i zasady działania po wygaśnięciu uprawnienia. Rozdzielić stan konta, prawo używania produktu i dostęp do własnych danych.

## Semantyka

Oddzielaj obserwacje, interpretacje, intencje/plany, deklaracje i hipotezy profilu, korekty/feedback oraz politykę działań. Hipoteza o osobowości nie jest faktem; odtwarzanie nie dowodzi uwagi; współwystępowanie nie dowodzi przyczynowości. Korekta ma jawne pierwszeństwo i nie znika po przeliczeniu reguł.

**Unia wszystkich obserwacji mierzy pokrycie obserwacjami, nie automatycznie aktywność człowieka.** Miary obecności wymagają określenia źródeł i reguł, a nieznany okres nie jest zerową aktywnością.
