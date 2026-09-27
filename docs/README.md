# Dokumentacja FocusWatch

**Zacznij od [HANDOFF.md](HANDOFF.md).** Zawiera kontekst potrzebny do kontynuacji na innym komputerze bez historii rozmowy.

| Dokument | Rola i status |
| --- | --- |
| [PROJECT_BRIEF.md](PROJECT_BRIEF.md) | Aktualny cel produktu, wymagania użytkownika i jawne niewiadome |
| [architecture/DECISIONS.md](architecture/DECISIONS.md) | Status wyborów architektonicznych; rekomendacja nie oznacza zatwierdzenia |
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | Etapy nowej implementacji i kryteria odbioru; prace jeszcze nie rozpoczęte |
| [HANDOFF.md](HANDOFF.md) | Operacyjny stan przekazania i pierwsze kroki na nowej maszynie |
| [research/2026-09/README.md](research/2026-09/README.md) | Skonsolidowany raport badań: repo, konkurencja, technologie, dane, platformy i chmury |
| [Instrukcja eksperymentów](../scripts/research/README.md) | Zależności i odtwarzanie pomiarów; opcjonalne, poza poznaniem kontekstu |

## Jak rozstrzygać rozbieżności

Polecenie użytkownika i aktualny brief określają cel. Rejestr decyzji określa status wyboru. Plan określa kolejność i kryteria pracy. Raporty są datowanymi dowodami i rekomendacjami, a nie samodzielnym zatwierdzeniem architektury. Jeśli nowe dane zmieniają decyzję, zapisz zmianę i uzasadnienie; nie przepisuj dawnych pomiarów na nowe wyniki.

## Dokumenty historyczne

- [feature-task-scheduling.md](feature-task-scheduling.md): wcześniejszy projekt sesji i zadań dla starego FocusWatch. Ograniczenie do jednej sesji, obowiązkowe migracje i wykluczenie blokowania nie są wymaganiami nowej wersji.
- [review-projects-readiness.md](review-projects-readiness.md): review napraw starego modelu i migracji. Wynik 68/68 dotyczy tamtego zakresu i środowiska; nie dowodzi gotowości nowej aplikacji.
- [Główne README](../README.md): poniżej informacji o restarcie pozostaje opis i instrukcja uruchamiania starej aplikacji.
