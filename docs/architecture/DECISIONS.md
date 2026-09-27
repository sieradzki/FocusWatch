# Rejestr decyzji architektonicznych

Stan: 27.09.2026. **Badanie zakończono; nowa implementacja nie powstała. Użytkownik zlecił konsolidację i przekazanie repo, nie zatwierdził automatycznie całego proponowanego stosu.**

Statusy: **wymaganie** pochodzi od użytkownika; **rekomendowane** to wybór badania do wykorzystania lub rozstrzygnięcia w implementacji; **otwarte** wymaga dalszego wyboru; **odroczone** ma świadomie późniejszy zakres. Nie podmieniaj statusu na „przyjęte” bez odnotowania podstawy. Kolejne polecenie użytkownika może upoważniać do wyborów w zleconym zakresie bez odrębnej zgody na każdy szczegół.

| ID | Status | Kierunek i uzasadnienie | Alternatywa / warunek zmiany / dowód |
| --- | --- | --- | --- |
| D01 | Wymaganie | Osobisty produkt komercyjny, wieloźródłowy, z historią lat, regułami i override | [Brief](../PROJECT_BRIEF.md); nie jest to produkt kontroli pracowników |
| D02 | Rekomendowane | Pełna nowa implementacja w tym samym repo; obecny kod jako wiedza | Refaktor/ponowne użycie tylko przy realnej oszczędności bez narzucenia starej semantyki. Brak wymogu kompatybilności i migracji. [Ocena kodu](../research/2026-09/rewrite-assessment.md) |
| D03 | Rekomendowane | Agent sesji niezależny od GUI; Rust do adapterów i lokalnego rdzenia | Niezależność procesów ma mocniejsze dowody niż język. Python/C++ wykonalne; X11 porównywało strategie w tym samym Pythonie. [Desktop](../research/2026-09/desktop-comparison.md) |
| D04 | Rekomendowane | Electron + React/TS, UI na żądanie | Qt Quick najlżejszy zmierzony, Tauri wykonalny i lżejszy od Electron. Electron przekroczył propozycję 300 MiB; decyzję może zmienić budżet prawdziwego raportu i test Windows/GPU. [Pomiary](../research/2026-09/desktop-results.md) |
| D05 | Rekomendowane | SQLite WAL, atomowy outbox, projekcje i ograniczone zapytania | 1 mln/10 mln syntetycznych obserwacji, nie gwarancja każdego obciążenia. DuckDB/Parquet do skanów i archiwum, nie zamiennik każdego małego odczytu. [Dane](../research/2026-09/data-results.md) |
| D06 | Rekomendowane | Modułowy Axum/SQLx/PostgreSQL przy Rust w rdzeniu | Go/pgx najbliższą alternatywą, Python/TS/.NET także rozpatrzone. Brak benchmarku języków HTTP; shared classifier ma mniejszą wartość przy E2EE. [Backend](../research/2026-09/backend-comparison.md) |
| D07 | Rekomendowane | Trwała historia w paczkach oraz WebSocket z najnowszym kontekstem | ACK historii osobno; reconnect, staleness i wiele instancji wymagają implementacji. Lokalny relay nie potwierdza cloud capacity. [Realtime](../research/2026-09/realtime-design.md) |
| D08 | Rekomendowane warunkowo | GCP Cloud Run + Cloud SQL + GCS, Belgia, jako pierwsze wdrożenie serwera | Scaleway konkurentem kosztowym; AWS pełną alternatywą; Cloudflare/DO możliwą optymalizacją. Model jest częściowy, nie ranking pełnego TCO. [Chmury](../research/2026-09/cloud-comparison.md) |
| D09 | Rekomendowane | OCI + deklaratywne IaC; propozycja OpenTofu | Terraform/Pulumi możliwe. Nie zmierzono przewagi narzędzia IaC; przeniesienie kontenera nie przenosi automatycznie usług i danych |
| D10 | Otwarte | E2EE kontra odczyt danych przez serwer | Potrzebne przed sync rzeczywistych danych; koszty i miejsce analityki różnią się. [Dane i prywatność](../research/2026-09/data-evaluation.md) |
| D11 | Otwarte / etap późniejszy | Model profilu, AI, lokalność inferencji, autonomia | Wartość pierwszej wersji bez LLM; późniejszy wspólny zestaw ocen jakości i feedback. Metadane nie dowodzą skuteczności sugestii |
| D12 | Wymaganie docelowe / etap późniejszy | Dobrowolne blokowanie z polityką działań i override | Osobny helper/adapter OS. Nie przejmować historycznego „not a blocker”. [Platformy](../research/2026-09/desktop-comparison.md) |
| D13 | Odroczone | Pełny web, pozostałe platformy, smart glasses; Kubernetes/Kafka/ClickHouse | Rozważyć przy konkretnej potrzebie lub pomiarze. Odroczenie nie jest wykluczeniem docelowego produktu |

## Jak aktualizować

Dla podjętego wyboru zapisz datę, status, zakres, uzasadnienie/dowód i warunek ponownego rozpatrzenia. Dla większej decyzji dodaj osobny ADR i link z tabeli. Nie ma potrzeby tworzyć nowego benchmarku dla każdej zmiany dokumentacji ani ponownie analizować całego stosu bez nowych przesłanek.

**Granice dowodów:** SQL/Parquet nie porównują języków; Xvfb nie testuje Windows/GPU; próba localhost nie dowodzi Internetu/HA; koszt referencyjnego PostgreSQL nie ustala jego pojemności. Parametry cen i wersje są datowane. Nowa implementacja potrzebuje własnych testów i pomiarów.
