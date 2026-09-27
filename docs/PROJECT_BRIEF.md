# FocusWatch — brief produktu

Stan przekazania: 27.09.2026. Ten dokument utrwala wymagania i intencje użytkownika; rekomendacje badawcze mają osobny [rejestr statusu](architecture/DECISIONS.md).

## Cel

Osobisty companion do rozumienia aktywności, wspierania celów i korygowania działań. Pierwszy użyteczny rezultat jest dla właściciela projektu, lecz projekt od początku ma podstawy **komercyjnego produktu B2C**. Nie jest to narzędzie nadzoru pracowników.

Docelowo system może znać plany, istotne dla użytkownika wartości, cele, preferencje i powtarzające się trudności. Ma pomagać w tworzeniu planów i dobieraniu rekomendacji. Użytkownik nie musi deklarować kierunku życiowego, żeby aplikacja była użyteczna. Sposób budowania profilu osobistego nie jest jeszcze rozstrzygnięty.

## Wymagania i kierunek

- **Cross-platform przez companiony i adaptery.** Pierwsze środowiska: Windows 11 i Arch Linux/dwm/X11. Później macOS, wybrane środowiska Wayland oraz osobne aplikacje mobilne; smart glasses są możliwością dalszego rozwoju, nie wybranym dziś SDK.
- **Historia liczona latami**, z wielu komputerów, przeglądarki i innych urządzeń. Docelowa chmura zbiera/łączy historię; jej dostęp do treści zależy od nierozstrzygniętej decyzji prywatności.
- **Równoległe źródła.** Edytor na foreground i stream w tle mogą trwać jednocześnie. Rejestrowanie obu nie oznacza podwójnego czasu osoby ani podziału uwagi 50/50. Media mogą mieć różne znaczenie zależnie od kontekstu; nie nadawaj im automatycznie negatywnej oceny.
- **Wydajne, atrakcyjne raporty** z agregacją, możliwością zejścia do szczegółów oraz korektą błędów. Podstawowa wartość powstaje przez poprawne pomiary, algorytmy i reguły, niezależnie od AI.
- **Możliwie mało ręcznej obsługi**, z manualnym override. Docelowo sugestie i plany korzystają z bieżącego kontekstu, ale zakres autonomii i uprawnienia działań są osobnymi decyzjami.
- **Dobrowolne blokowanie niepożądanych aplikacji/działań** należy do docelowego produktu. Wymaga adapterów i uprawnień systemowych; nie obiecujemy identycznych możliwości na wszystkich OS.
- **Personalizacja:** reguły, kategorie, zakres pomiaru, preferencje, interwencje i korekty. Duży zakres personalizacji nie przesądza o publicznym systemie pluginów w pierwszej wersji.
- Początkowo **metadane i jawne integracje**; screenshoty, OCR, nagrywanie audio i pełna treść stron nie należą do pierwszego zakresu.

## Założenia, których nie należy dodawać

- Nie ma wymogu zachowania starej aplikacji, jej API, schematu, feature parity ani automatycznej migracji historii. Projekt nie ma obecnie grupy zewnętrznych użytkowników. Pełne przepisanie jest równoprawną drogą, a zachowanie istniejącego kodu musi mieć konkretną wartość.
- Nie ma obowiązku budowy pełnej aplikacji webowej; desktop/mobile mogą wystarczyć. Portal konta i płatności to osobny zakres.
- Cloudflare jest przykładem, nie preferowaną chmurą. Rize i ActivityWatch są przykładami do badań, nie zamkniętą listą konkurencji.
- Większy koszt początkowej implementacji może być uzasadniony niższym kosztem utrzymania. Nie oznacza to deklaracji samodzielnej administracji VPS ani zgody na nieograniczoną złożoność.
- Rust, Electron, React, GCP i OpenTofu nie zostały narzucone przez użytkownika. Liczby 300 MiB, 1/5 s, 90 dni i 3840 obserwacji/dzień są propozycjami lub parametrami badania, nie uzgodnionym SLA.

## Otwarte kwestie

1. **Prywatność chmury:** E2EE/blind sync, dane czytelne dla serwera lub świadomie wydzielone podsumowania. Konsekwencje obejmują miejsce analityki, klucze, odzyskiwanie i koszt. Ustalić przed przesyłaniem prawdziwej historii; nie blokuje to lokalnego rdzenia.
2. **AI:** lokalne/chmurowe modele, jakość, opóźnienia i zakres autonomii. Nie zmierzono inferencji ani trafności rekomendacji; wybór powinien wynikać z oceny na wspólnych scenariuszach. Nie blokuje pomiarów, raportów i reguł.
3. **Budżety i dystrybucja:** docelowy RAM/CPU/bateria, pierwszy wspierany zakres Windows/Linux, podpisy, aktualizacje i zachowanie bez uprawnień. Badany laptop nie jest obowiązkowym profilem każdego użytkownika.
4. **Pierwszy zakres produktu:** rekomendowany jest mały przekrój pomiar → agregacja → raport → korekta. Cele, profil i blokowanie pozostają w architekturze docelowej, bez obowiązku odtworzenia Kanbana przed tym przekrojem.

## Semantyka, którą trzeba zachować w projekcie

Oddzielaj **obserwacje**, **interpretacje**, **intencje/plany**, **deklaracje i hipotezy profilu**, **korekty/feedback** oraz **politykę działań**. Hipoteza o osobowości nie jest faktem; odtwarzanie nie dowodzi uwagi; współwystępowanie nie dowodzi wpływu na produktywność lub burnout. Ręczna korekta ma jawne pierwszeństwo i nie może znikać po przeliczeniu klasyfikacji.
