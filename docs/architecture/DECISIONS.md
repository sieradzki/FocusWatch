# Rejestr decyzji architektonicznych

Stan: **03.10.2026**. Aktualizacja dokumentacyjna po badaniu i doprecyzowaniu modelu płatnego. **Nowa implementacja nie powstała; rekomendacje nie są automatycznie zatwierdzonym przez użytkownika stosem.**

Statusy: **wymaganie** pochodzi od użytkownika; **rekomendowane** oznacza wybór inżynierski do pierwszego przekroju; **warunkowe** zależy od wskazanej decyzji; **otwarte** wymaga rozstrzygnięcia; **odroczone** ma późniejszy zakres. Nie przypisuj użytkownikowi wyboru technologii bez podstawy.

Bieżące uzasadnienie: [architektura referencyjna](REBUILD_BASELINE_2026-10-03.md). Wyniki z `2026-09` pozostają historycznymi dowodami, nie nowymi pomiarami.

| ID | Status | Aktualny kierunek | Dowód, ograniczenie lub warunek zmiany |
| --- | --- | --- | --- |
| D01 | Wymaganie | Osobisty produkt B2C, wiele źródeł i urządzeń, wieloletnia historia, reguły i override | [Brief](../PROJECT_BRIEF.md); nie nadzór pracowników |
| D02 | Rekomendowane | Nowa implementacja w tym samym repo, stary kod jako wiedza | Brak obowiązku kompatybilności i migracji. [Ocena rewrite](../research/2026-09/rewrite-assessment.md) |
| D03 | Rekomendowane | Niezależny agent sesji w Rust, mały czysty rdzeń i adaptery OS | Niezależność procesu ma mocniejsze dowody niż wybór języka. Nie używamy znajomości autora jako argumentu. [Desktop](../research/2026-09/desktop-comparison.md) |
| D04 | Rekomendowane do prototypu | Electron + React/TypeScript, UI na żądanie, bez kolekcji w rendererze | Tauri to najbliższy challenger dla tego samego frontendu; Qt Quick przy twardym priorytecie zasobów. Nie ma nowego testu Windows/GPU. [Odbiór](PROTOTYPE_ACCEPTANCE.md) |
| D05 | Rekomendowane | SQLite WAL, kontrolowany writer, atomowy outbox, wersjonowane projekcje; rusqlite jako domyślny dostęp Rust | Testy 1 mln/10 mln nie gwarantują każdego obciążenia. DuckDB/Parquet tylko do konkretnej potrzeby. [Wyniki](../research/2026-09/data-results.md) |
| D06 | Warunkowe; aktualizacja 03.10 | Przy blind-sync: TypeScript/Workers. Przy serwisie OCI: modułowy Axum/SQLx/PostgreSQL | Rust w collectorze nie wymusza Rust na serwerze. Nie wykazano benchmarkowej przewagi języka HTTP. [Uzasadnienie](REBUILD_BASELINE_2026-10-03.md) |
| D07 | Rekomendowane | Trwała historia w paczkach, edycje z rewizjami/konfliktami, nietrwały najnowszy kontekst; dwa kanały transportowe | ACK dopiero po trwałym, odnajdywalnym przyjęciu; TTL i resync. Nie dodajemy trwałego bufora tylko dla oszczędności groszy. [Realtime](../research/2026-09/realtime-design.md) |
| D08 | Warunkowe; aktualizacja 03.10 | Cloudflare Workers/R2/DO to wariant referencyjny wyłącznie dla rekomendowanego blind-sync. GCP Run/SQL/GCS pozostaje kandydatem dla historii czytelnej przez serwer | Dostawca NIE wybrany bezwarunkowo. Płatny model nie rozstrzyga prywatności. Potrzebne region, odzyskanie danych i pełny koszt. [Uzasadnienie](REBUILD_BASELINE_2026-10-03.md) |
| D09 | Rekomendowane warunkowo | Deklaratywne środowiska i wersjonowana konfiguracja; OCI dla usług kontenerowych | Nie wymuszamy OCI na Workers. OpenTofu/Wrangler i podział odpowiedzialności dobrać do wybranego wdrożenia. Przenośność wymaga eksportu danych i testu wyjścia |
| D10 | Otwarte; rekomendowane E2EE | Lokalna analityka i zaszyfrowana historia, osobne udostępnienie danych AI | To rekomendacja, nie zgoda użytkownika. Serwer bez kluczy nie analizuje sam pełnej historii, gdy urządzenia są wyłączone |
| D11 | Otwarte / etap późniejszy | Model profilu, inferencja i autonomia oceniane na wspólnych scenariuszach | Bez LLM w krytycznej ścieżce pomiaru i uprawnień; koszt per konto i jakość, nie dowolnie częste wywołania |
| D12 | Wymaganie docelowe / etap późniejszy | Dobrowolne blokowanie, polityka i override, osobny ograniczony helper | Różne uprawnienia OS; nie obiecujemy blokady niemożliwej do obejścia. [Platformy](../research/2026-09/desktop-comparison.md) |
| D13 | Odroczone | Pełny web, dalsze platformy, smart glasses, publiczne pluginy, Kubernetes/Kafka/ClickHouse | Dodawać przy wykazanej potrzebie, nie dla hipotetycznej przyszłości |
| D14 | Wymaganie; 03.10 | Produkt z założenia płatny, reasonably priced; bazowy koszt na płacącego klienta | Nie oznacza ustalonej subskrypcji, ceny, trialu ani darmowej wersji lokalnej |
| D15 | Wymaganie; 03.10 | Brak premii za wcześniejszą znajomość technologii przez właściciela; uwzględniamy rozwój agentowy | Automatyczna weryfikacja, diagnostyka, integracje i utrzymanie pozostają kryteriami; nie zakładamy bez dowodu przewagi agentów w danym języku |
| D16 | Rekomendowane | Oddzielić konto, urządzenie, uprawnienie/licencję i klucze historii | Tryb offline i bezpieczny eksport/usuwanie nie powinny zależeć od chwilowej awarii płatności. Szczegółowe zasady po wygaśnięciu pozostają otwarte |
| D17 | Rekomendowane | Następny zakres P0: kontrakt, fixtures i szkielet; potem jeden lokalny przekrój, nie równoległy rewrite sześciu stosów | [Plan](../IMPLEMENTATION_PLAN.md), [odbiór](PROTOTYPE_ACCEPTANCE.md). Brak wykonanej implementacji |

## Zasady ponownego rozpatrzenia

Nowy wybór opisujemy datą, zakresem, dowodem i warunkiem zmiany. Potwierdzone wymagania i rekomendacje pozostają rozdzielone. Nie wracamy do ogólnego researchu bez nowego problemu, dowodu lub polecenia użytkownika.

Nie podnosimy progu budżetu tylko po to, żeby wybrany framework przeszedł test. Przy niezaliczeniu poprawiamy rzeczywistą przyczynę, a następnie porównujemy najbliższego konkurenta na tym samym przekroju.

**Granice dowodów:** SQL/Parquet nie porównują języków; Xvfb nie testuje Windows/GPU; localhost nie potwierdza Internetu/HA; częściowy cennik nie jest pełnym TCO. Nie utożsamiamy utworzenia tego rejestru z testem produktu.
