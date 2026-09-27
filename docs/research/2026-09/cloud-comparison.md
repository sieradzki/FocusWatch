# FocusWatch: porównanie chmur i odtwarzalny model kosztów

Stan publicznych cenników: **27.09.2026**. Bez wdrażania zasobów, logowania do kont i odczytywania kluczy. Liczby poniżej to **częściowe koszty infrastruktury**, nie oferta dostawcy ani potwierdzenie przepustowości. Źródła cen, parametry i regionalne SKU AWS są zamrożone w [cloud-cost-inputs.json](cloud-cost-inputs.json); pełne rozbicie i sensitivities w [cloud-cost-results.json](cloud-cost-results.json).

## Rekomendacja

**Dla pełnego celu FocusWatch rekomenduję warunkowo GCP: Cloud Run w Belgii, Cloud SQL PostgreSQL i GCS, z natywnym backendem w OCI oraz deklaratywnym IaC.** Pierwszy prywatny prototyp może używać małej pojedynczej bazy; przed płatnym wdrożeniem osobno wybieramy HA i wymagany czas odzyskania. Cloud Run ma udokumentowane WebSockety, a regionalny Cloud SQL automatycznie przełącza bazę między AZ. To zmniejsza liczbę nierozstrzygniętych granic dla planowanego kontekstu między urządzeniami. **Nie jest to twierdzenie, że GCP zawsze kosztuje najmniej.** [Cloud Run WebSockets](https://docs.cloud.google.com/run/docs/triggering/websockets), [Cloud SQL HA](https://cloud.google.com/sql/docs/postgres/high-availability).

**Scaleway Paris jest główną alternatywą kosztową**: wygrywa w tabeli krótkich żądań i może wygrać również przy niedrogim kanale RT. Jego PostgreSQL HA pozostaje jednak w jednym DC, w dwóch szafach; replika między AZ nie promuje się automatycznie. Limit Containers 80 jednoczesnych żądań na instancję jest istotny dla otwartych strumieni. Decyzję odwracamy na Scaleway, jeżeli test rzeczywistej synchronizacji potwierdzi przewagę po uwzględnieniu połączeń, a taka granica HA odpowiada produktowi. [Scaleway PG FAQ](https://www.scaleway.com/en/docs/managed-databases-for-postgresql-and-mysql/faq/), [limity Containers](https://www.scaleway.com/en/docs/serverless-containers/reference-content/containers-limitations/).

Workers nie mają dziś wykazanej przewagi dla **całego** backendu: z tym samym zewnętrznym PostgreSQL koszt zależy od CPU i czasu oczekiwania. Natywny Rust/Axum w OCI daje prostsze przenoszenie. Cloudflare z hibernującymi Durable Objects pozostaje kandydatem na relay RT, ale wymaga osobnego rachunku i testu; dodatkowego dostawcy nie dodajemy na podstawie samej obietnicy niższych kosztów. AWS to technicznie pełna alternatywa, lecz Fargate + ALB podnoszą koszt początkowy. Hetzner pozostaje referencją samodzielnej administracji, której użytkownik nie zadeklarował.

## Wspólne obciążenie i granice modelu

- 3 zarejestrowane urządzenia; 2 aktywne ekwiwalenty po 8 godzin dziennie; 2 źródła na urządzenie; średni scalony segment 30 sekund. Wynik: **3840 obserwacji/użytkownika/dzień**. To jawny scenariusz syntetyczny. Niewielka próbka starej aplikacji nie ustala przyszłej średniej.
- Synchronizacja co 60 sekund na aktywne urządzenie: **28 800 paczek miesięcznie na użytkownika**. Dodatkowo zakładamy po 2 oddzielne żądania API pobrania każdej paczki przez pozostałe urządzenia, a także 20 raportów dziennie: razem **87 000 żądań/miesiąc**. Sensitivity ratio pobrań 0/1/2 oddziela piggyback lub bezpośrednie odczyty obiektów od osobnych wywołań API. Paczka zawiera przeciętnie 4 obserwacje. Retries, dodatkowe heartbeat i puste odpytywanie zwiększą tę liczbę.
- Miesiąc obliczeniowy ma 30 dni / 720 godzin. Retencja to 5 × 365 dni. Tabela pokazuje **miesięczny koszt po zgromadzeniu pięciu lat historii** dla stałej liczby użytkowników, nie sumę pięcioletnich rachunków ani pierwszy miesiąc. Stawki magazynowe miesięczne są publikowanym przybliżeniem dostawcy; rzeczywisty kalendarz może zmienić je o ok. 1–3%.
- Pierwotne 350 B dotyczy logicznego payloadu. W modelu wire to **500 B/zdarzenie**, zaokrąglone z niezależnego syntetycznego pomiaru JSON z metadanymi. Gorący PostgreSQL to na razie **700 B/zdarzenie z indeksami jako założenie kosztowe z zapasem**. Osobny lokalny test 1 mln syntetycznych rekordów PG zmierzył 563,72 B/zdarzenie (tabela + 4 indeksy), bez replik, backupu i bloat; nie jest to pomiar wymaganej mocy chmurowej bazy. Przydział dysku dodatkowo zawiera 30% zapasu. [Wynik pomiaru PG](postgres-results.json). Backup zajmuje umownie 2× fizyczny zbiór: jest to budżet objętości, nie gwarancja określonej retencji PITR.
- Starsze dane: **100 B/zdarzenie w paczkach dziennych**, z analizą wrażliwości 52/100/350 B. Osobny benchmark 10 mln syntetycznych rekordów osiągnął ok. 52 B w Parquet/ZSTD; nie dowodzi to kompresji prawdziwej historii. Nie używamy najtańszego zamrożonego archiwum: historia ma pozostać dostępna do raportów.
- W wariancie odczytywalnym przez serwer ostatnie 90 dni trafia do PG, reszta do obiektów. Przy 1000 użytkowników: 115,2 mln obserwacji/miesiąc, 345,6 mln w gorącym zbiorze, **241,92 GB fizycznego PG**, 666,24 GB archiwum oraz 7,008 mld obserwacji w pięcioletniej historii.
- Pobrania: nowe dane na 2 pozostałe urządzenia, odpowiedź raportu 100 kB, ACK 500 B, eksport równowartości 1% archiwum/miesiąc. To około **196 GB ruchu wychodzącego/miesiąc przy 1000 użytkowników**. Odczyt całej historii przez każdy raport nie jest założony.
- **10 ms CPU oraz 100 ms czasu obsługi żądania są parametrami, nie wynikami benchmarku.** Przy ruchu współbieżnym model zakłada nakładanie 4 żądań na instancję, przy jednym użytkowniku 100 ms izolowanego rozliczanego czasu. Sensitivity obejmuje CPU 1/10/100 ms, czas 100/1000 ms, batch 5/30/60/300 s. **Minutowy sync historii nie spełnia sam z siebie wymagań kontekstu real time**; osobny wariant poniżej wycenia otwarte połączenia. Nie wyprowadzamy z tego p95 ani wydajności konkretnego języka.

GB dziesiętne i GiB są rozróżnione: GCP/AWS używają tu GiB; Scaleway/R2 są liczone według oznaczenia GB jako 10^9 B, co wymaga potwierdzenia jednostki rozliczeniowej storage i może dawać różnicę do 7,4%. RAM Scaleway Containers liczymy zgodnie z przykładem dostawcy 128 MB = 0,125 GB, czyli jak rozmiary binarne. [AWS potwierdza binarne GB](https://aws.amazon.com/s3/pricing/). Darmowe pule są przypisane wyłącznie FocusWatch, bez czasowych kredytów powitalnych.

## Co kupujemy za cenę bazową

| Dostawca / region | Jednowęzłowy wariant developerski | Wariant komercyjny odniesienia | Istotna różnica |
| --- | --- | --- | --- |
| GCP / Belgia | db-f1-micro, współdzielone 0,6 GiB | Enterprise 2 vCPU / 8 GiB + regionalny standby | Dev nie ma SLA Cloud SQL; automatyczne HA między AZ w drugim wariancie |
| Scaleway / Paryż | DB-DEV-S, 2 vCPU / 2 GB | DB-PRO2-XXS, 2 vCPU / 8 GB + standby | HA w tym samym DC; **nie równoważne multi-AZ** |
| AWS / Irlandia | db.t4g.micro + 1 task Fargate | db.m6g.large, 2 vCPU / 8 GiB Multi-AZ + co najmniej 2 tasks | ALB, IPv4 i taski działające przez cały miesiąc; koszty CPU burst dev mogą dojść |
| Cloudflare | Workers lub Containers + zewnętrzny DB-DEV-S | Workers lub Containers + ten sam Scaleway PG ze standby | PG nadal płatny; HA i sieć zależą od zewnętrznego dostawcy |
| Hetzner / Niemcy/Finlandia | CX23 + baza na własnym VM | referencja 2× CCX13 | Brak zarządzanej bazy w wycenie; 2 VM same nie tworzą HA |

Stałe 2 vCPU / 8 GB bazy to **wspólny koszyk cenowy**, nie dobrany rozmiar dla każdej populacji. W szczególności **nie twierdzimy, że taka baza obsłuży 10 000 użytkowników / 3,456 mld gorących rekordów**. Trzeba zmierzyć ingest, deduplikację, pruning, indeksy, raporty, VACUUM i odzyskiwanie. Tabela nie jest prognozą kosztu gotowej produkcji dla tych skal.

## Ceny wejściowe — bez podatku, bez zobowiązań

| Składnik | Zweryfikowana stawka i region |
| --- | --- |
| Cloud Run | Belgia: 0,000024 USD/vCPU-s; 0,0000025 USD/GiB-s; 0,40 USD/mln żądań. Stałe pule: 180 tys. vCPU-s, 360 tys. GiB-s, 2 mln żądań. |
| Cloud SQL Enterprise | Belgia: 0,0413 USD/vCPU-h + 0,007 USD/GiB-h; HA 2×. SSD 0,17 USD/GiB-mies., HA 0,34; backup 0,08. Mikro dev 0,0105 USD/h. |
| GCS Standard | Belgia: 0,02 USD/GiB-mies.; PUT 0,005 USD/1000, GET 0,0004 USD/1000. **Nie stosujemy amerykańskiej darmowej puli GCS.** |
| Scaleway Containers | Paryż: 0,00001 EUR/vCPU-s + 0,000002 EUR/GB-s; 200 tys. vCPU-s i 400 tys. GB-s w puli. |
| Scaleway PG | Paryż: dev 0,0156 EUR/h; PRO2-XXS primary 0,11 + standby 0,0583 EUR/h; dysk 0,0993 EUR/GB-mies.; backup 0,03. |
| Scaleway Object Storage | Paryż Standard Multi-AZ 0,01606 EUR/GB-mies.; operacje w cenie; egress 75 GB gratis, dalej 0,01 EUR/GB. |
| AWS Fargate i ALB | Irlandia Linux x86: 0,04048 USD/vCPU-h + 0,004445 USD/GiB-h. ALB 0,0252 USD/h + 0,008 USD/LCU-h; IPv4 0,005 USD/h. |
| RDS PostgreSQL | Irlandia: t4g.micro 0,017 USD/h; m6g.large Multi-AZ 0,352 USD/h; gp3 0,127 / HA 0,254 USD/GiB-mies.; dodatkowy backup 0,095. |
| S3 Standard | Irlandia: 0,023 USD/GiB-mies. do 50 TiB; PUT 0,005 USD/1000, GET 0,0004 USD/1000. |
| Workers i R2 | 5 USD/mies.; 10 mln żądań i 30 mln CPU-ms, dalej 0,30 USD/mln żądań i 0,02 USD/mln CPU-ms. R2 Standard 0,015 USD/GB-mies.; PUT 4,50 USD/mln, GET 0,36 USD/mln; darmowe pule i zaokrąglenia w kalkulatorze. |
| Cloudflare Containers | CPU 0,000020 USD/s aktywnego CPU; pamięć 0,0000025 USD/GiB-s; provisioned disk 0,00000007 USD/GB-s; Europa egress 0,025 USD/GB po 1 TB. Dodatkowo Worker i Durable Object. |
| Hetzner reference | CX23 5,49 EUR/mies.; CCX13 42,99 EUR/mies. dla nowych zamówień po 15.06.2026; IPv4 0,50 EUR/mies. Object Storage 6,49 EUR bazowo, nadmiar 0,0087 EUR/TB-h. |

Źródła tabeli: [Cloud Run](https://cloud.google.com/run/pricing), [Cloud SQL](https://cloud.google.com/sql/pricing), [GCS](https://cloud.google.com/storage/pricing); [Scaleway compute](https://www.scaleway.com/en/pricing/serverless/), [PG](https://www.scaleway.com/en/pricing/managed-databases/), [storage](https://www.scaleway.com/en/pricing/storage/); regionalne oficjalne listy [AWS ECS](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonECS/current/eu-west-1/index.json), [RDS](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRDS/current/eu-west-1/index.json), [S3](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonS3/current/eu-west-1/index.json), [ALB](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSELB/current/eu-west-1/index.json), [IPv4](https://aws.amazon.com/vpc/pricing/); [Workers](https://developers.cloudflare.com/workers/platform/pricing/), [R2](https://developers.cloudflare.com/r2/pricing/), [Containers](https://developers.cloudflare.com/containers/platform/pricing/), [Durable Objects](https://developers.cloudflare.com/durable-objects/platform/pricing/); [Hetzner nowe ceny VM](https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/), [Object Storage](https://www.hetzner.com/storage/object-storage/) i [publiczny feed ceny dodatkowej pojemności](https://website-price-api.hetzner.com/api/v1/products/CLOUD_85).

Ceny Google zostały odczytane z danych tabeli **Belgium (europe-west1)** osadzonych w publicznym HTML, nie z domyślnie widocznej tabeli Iowa. Listy AWS pochodzą z `eu-west-1` i zawierają publikacje z 11–26.09.2026. Domena endpointu AWS `pricing.us-east-1.amazonaws.com` jest adresem katalogu — **region produktu w tych plikach to Irlandia**.

## Wyniki miesięczne: scenariusz z odczytem danych przez serwer

Wszystkie liczby tabeli to EUR po jawnej konwersji **1 EUR = 1,1403 USD, ECB 25.09.2026**. Ceny źródłowe USD/EUR i koszty zewnętrznego PG pozostają osobnymi polami JSON. To nie prognoza kursu. [ECB](https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml).

**Jednowęzłowy koszyk developerski — szczególnie małe bazy nie są równoważne sprzętowo.** Kolumny dużych populacji pokazują mechaniczne skutki wolumenu; nie są rekomendacją użycia mikroinstancji.

| Wariant | 1 użytkownik | 100 | 1000 | 10 000 |
| --- | ---: | ---: | ---: | ---: |
| GCP: Cloud Run + Cloud SQL + GCS | 8.18 | 20.44 | 185.71 | 1837.75 |
| Scaleway: Containers + PostgreSQL + Object Storage | 11.76 | 17.11 | 88.86 | 812.14 |
| AWS: Fargate + RDS + S3 | 69.54 | 73.84 | 150.75 | 1075.92 |
| Cloudflare Workers + zewnętrzny PG + R2 | 16.13 | 22.00 | 105.04 | 938.91 |
| Cloudflare Containers + zewnętrzny PG + R2 | 18.04 | 25.09 | 145.22 | 1369.96 |

**Koszyk ze standby: GCP/AWS multi-AZ; Scaleway/Cloudflare+Scaleway tylko HA w jednym DC.** Żaden wiersz nie jest kompletnym TCO.

| Wariant | 1 użytkownik | 100 | 1000 | 10 000 |
| --- | ---: | ---: | ---: | ---: |
| GCP: Cloud Run + Cloud SQL + GCS | 178.07 | 193.31 | 397.79 | 2442.81 |
| Scaleway: Containers + PostgreSQL + Object Storage | 122.20 | 130.23 | 230.09 | 1234.38 |
| AWS: Fargate + RDS + S3 | 317.62 | 323.04 | 417.80 | 1636.54 |
| Cloudflare Workers + zewnętrzny PG + R2 | 126.57 | 135.12 | 246.27 | 1361.15 |
| Cloudflare Containers + zewnętrzny PG + R2 | 130.63 | 140.36 | 286.49 | 1792.24 |

Hetzner osobno: **110,67 / 110,67 / 111,61 / 176,44 EUR** dla 1/100/1000/10 000 w referencji 2× CCX13. To celowo nie trafiło do rankingu: nie wyceniono dodatkowego dysku danych, load balancera, quorum i obsługi failover. Wariant jednego CX23 dla 1 użytkownika wynosi 13,58 EUR z IPv4, 20% backupu VM i minimalną opłatą za obiekty. [Zasady rozliczeń backupu](https://docs.hetzner.com/cloud/billing/faq/). Ta suma nie uzasadnia twierdzenia, że Hetzner obsłuży produkt komercyjny za kilkanaście euro.

Przy 1000 użytkowników w odczytywalnym wariancie Scaleway około 198 EUR przypada na PG, dysk i backupy, około 11 EUR na starszą historię, a około 21 EUR na API. Wariant Workers korzystający z **tej samej bazy** ma dodatkowo około 55 USD za Workers i R2; Hyperdrive nie finansuje bazy danych. Różnica około 16 EUR między tymi wariantami jest niewielka wobec niepewności czasu wykonania i dodatkowej sieci do PG. [Hyperdrive pricing](https://developers.cloudflare.com/hyperdrive/platform/pricing/).

## Osobny rachunek real time: połączenia zmieniają ranking

Wariant minimalny: **2 połączenia na użytkownika, przez 8 h dziennie**, 1 vCPU i 0,5 GiB na instancję. Liczba instancji to `ceil(2 × użytkownicy / połączenia_na_instancję)`. Scenariusz zakłada wspólne okno aktywności, bez kosztu czasu wygaszania. GCP używa tu rozliczania **instance-based** (Belgia: 0,000018 USD/vCPU-s i 0,000002 USD/GiB-s; pule 240 tys. CPU-s i 450 tys. GiB-s), bez dodatkowej opłaty per request. API i połączenia współdzielą obliczenia i jedną darmową pulę; nie dodajemy drugi raz kosztu API z tabeli powyżej. [Cloud Run pricing](https://cloud.google.com/run/pricing).

| Koszyk komercyjny z połączeniami — częściowy koszt EUR/mies. | 1 użytkownik | 100 | 1000 | 10 000 |
| --- | ---: | ---: | ---: | ---: |
| GCP, założone 100 połączeń/instancję | 187.92 | 214.39 | 607.74 | 4535.96 |
| GCP, założone 250 połączeń/instancję | 187.92 | 200.02 | 434.98 | 2808.41 |
| GCP, teoretyczny limit 1000/instancję | 187.92 | 200.02 | 356.05 | 2019.12 |
| Scaleway, limit 80/instancję | 128.90 | 155.77 | 443.76 | 3371.13 † |

**To optymistyczna dolna granica rozliczeń, nie dowód pojemności 512 MiB.** 100/250 połączeń to parametry testu; 1000 dla GCP i 80 dla Scaleway są limitami konfiguracji. Zajęcie wszystkich slotów pozostawia brak zapasu dla krótkich żądań API; trzeba zmierzyć RAM, fanout, CPU, p95 i potrzebny margines. Cloud Run dokumentuje WebSockety do 60 minut i do 1000 połączeń na instancję. Scaleway dokumentuje HTTP/1.1/2 i limit czasu 60 minut, ale nie potwierdzono tu obsługi WebSocket upgrade; jego rachunek to hipotetyczny otwarty strumień HTTP wymagający testu protokołu. † Przy 10 000 użytkowników potrzeba minimum 250 instancji Scaleway, ponad limit 200 pojedynczego zasobu — liczba nie jest ofertą wykonalnego wdrożenia bez podziału usług. [Cloud Run WebSockets](https://docs.cloud.google.com/run/docs/triggering/websockets), [Scaleway limity](https://www.scaleway.com/en/docs/serverless-containers/reference-content/containers-limitations/).

Przy 1000 użytkowników GCP przy założonych 250 połączeniach na instancję osiąga podobny częściowy koszt jak Scaleway; przy 100 połączeniach jest droższy. To konkretny próg do sprawdzenia, zamiast zakładać, że każdy serwer zmieści 1000 klientów. Dochodzą reconnecty, buforowanie, koordynacja między instancjami i transmisja komunikatów RT; nie zostały wycenione. E2EE nie usuwa kosztu transportu, choć usuwa analizę treści na serwerze.

Alternatywna sensitivity `batch_seconds=5` daje przy 1000 użytkowników **491 EUR Scaleway / 1273 EUR GCP / 663 EUR Workers+PG** w bazowym modelu krótkich żądań. To świadomie prosty wariant: 5-sekundowy upload i dwa pobrania każdej paczki, również pustej, czyli ok. 1,037 mln wywołań miesięcznie na użytkownika. Nie jest optymalnym pollingiem ani gwarancją opóźnienia poniżej 5 sekund. Wysyłanie istotnych zmian kontekstu po zdarzeniu, oddzielone od trwałej historii, może zmienić ten rachunek; patrz [projekt RT](realtime-design.md). Koszt dedykowanego relay Cloudflare/Durable Objects nie jest jeszcze kompletnie policzony, dlatego nie ogłaszamy zwycięzcy pełnego systemu na podstawie samych tych tabel.

## Wariant E2EE / blind sync: decyzja produktowa pozostaje otwarta

Powyższy wariant **nie przesądza zgody na odczytywanie logów przez chmurę**. Przy E2EE chmura może przechowywać zaszyfrowane paczki, małe dane sterujące i manifesty, a raporty i interpretacja działają lokalnie. Serwer nie może wykonywać SQL po zawartości ciphertextu. Dane trzeba kompresować przed szyfrowaniem po stronie klienta; model nie zakłada kompresji ani deduplikacji między użytkownikami.

Dwa przykładowe sposoby składowania pokazują, dlaczego sam wolumen bajtów nie wystarcza:

| Wariant przy 1000 użytkowników, koszyk komercyjny | GCP | Scaleway | AWS | Workers + PG + R2 |
| --- | ---: | ---: | ---: | ---: |
| Ciphertext jako osobny obiekt co minutę, potem dzienna kompakcja | 429.02 | 154.63 | 491.02 | 296.36 |
| Opaque staging w PG przez 1 dzień, potem dzienne obiekty | 282.88 | 154.77 | 344.53 | 170.86 |

W pierwszym wariancie przy 1000 użytkowników powstaje 28,8 mln minutowych PUT i 57,6 mln dodatkowych GET miesięcznie. W R2 znacznie zwiększa to opłaty operacyjne; Scaleway ma operacje w cenie. W drugim PG przechowuje jedynie krótkotrwałe szyfrowane dane i zakładane 1 MB metadanych/użytkownika. **To porównanie topologii kosztowej, nie ostateczny schemat synchronizacji.** Docelowe ACK, klucze, offline, kompakcja i odzyskanie urządzenia wymagają osobnego projektu i testu.

## Wrażliwość, utrzymanie i progi zmiany decyzji

- Dla 1000 użytkowników zmiana fizycznego PG z 350 do 1400 B/obserwację daje około **192–307 EUR Scaleway** i **338–517 EUR GCP**. Dlatego pomiar PG/indexów jest ważniejszy niż wybór najtańszej ceny pojedynczego requestu.
- Zmiana skompresowanego archiwum z 52 do 350 B daje około **225–257 EUR Scaleway**. Trzymanie wszystkich pięciu lat w PG i skanowanie ich przy każdym raporcie zmieniłoby rachunek znacznie mocniej.
- Przy czasie obsługi 1000 ms i 4 nakładających się żądaniach koszyk dla 1000 użytkowników rośnie do ok. **445 EUR Scaleway / 831 EUR GCP**; Workers przy tym samym CPU pozostają około 246 EUR. To scenariusz, w którym Workers warto ponownie zmierzyć. Nie ustala przepustowości ani wymaganego RAM przy większej współbieżności.
- Dodatkowa niepotwierdzona opłata sieciowa 0 / 0,01 / 0,09 EUR za GB zmieniałaby koszt przy 1000 użytkowników o ok. **0 / 1,96 / 17,66 EUR**. Scaleway Containers ma ingress/egress bez dodatkowej opłaty według oficjalnego FAQ; ta sensitivity dotyczy wyłącznie ewentualnej niewycenionej ścieżki sieciowej, np. zewnętrznego PG. Nie jest dopłatą do API Scaleway. [FAQ rozliczeń](https://www.scaleway.com/en/docs/serverless-containers/faq/).
- **Utrzymanie**: 0 / 2 / 8 / 20 godzin miesięcznie × ilustracyjne 50 EUR/h oznacza +0 / +100 / +400 / +1000 EUR. To sensitivity, nie przewidywanie liczby godzin dla konkretnego dostawcy. Ta sama macierz jest w JSON dla każdego wariantu. Różnica GCP–Scaleway przy 1000 użytkowników wynosi około 168 EUR, czyli 3,4 h przy tej stawce; jedna taka różnica w pracy operacyjnej potrafi odwrócić ranking.
- Przed przejściem z pierwszego użytkownika do płatnego wdrożenia ustalamy wymagany czas odzyskania. **Wymóg automatycznego failover po utracie AZ wyklucza tańszy koszyk Scaleway jako równoważny**, bez oczekiwania na próg liczby użytkowników.
- **Workers wybieramy zamiast OCI dopiero po teście** tych samych paczek, transakcji PG i raportów, jeśli roczna oszczędność po doliczeniu drugiego dostawcy oraz kosztu adaptacji Wasm przekracza koszt tej adaptacji i akceptujemy granicę regionalności. Próg finansowy zapisujemy jako `12 × miesięczna oszczędność > godziny zmiany × 50 EUR + dodatkowe utrzymanie`, nie arbitralną liczbę użytkowników.
- **Zmiana rozmiaru PG / architektury danych** następuje po pomiarze limitu czasu zapisu, raportów, utrzymania indeksów lub odzyskiwania; cennik sam nie ustala tego progu. Przed 10 000 użytkowników konieczne jest ponowne wycenienie faktycznie dobranej bazy i IOPS.

## Operacyjność i przenośność

Początek: **OCI + deklaratywne IaC (np. OpenTofu), jeden API/backend i niezależnie uruchamiane zadania porcjowe**, PostgreSQL oraz obiekty. Nie potrzeba klastra Kubernetes do rozdzielenia API i zadań. K8s rozważamy dopiero, kiedy konkretne wymaganie schedulera, sieci lub koszt stałych usług pokryje koszt utrzymania klastra. Repozytorium powinno zawierać plan odtworzenia z backupu i ograniczenia kosztów, a nie wyłącznie skrypt wdrożenia.

Cloud Run/Scaleway skalują obsługę HTTP; długotrwałe procesy muszą mieć jawny model restartu i checkpointów. Stały worker lub otwarte połączenia czasu rzeczywistego mogą usunąć korzyść skali do zera. Główne tabele zakładają okresowe porcje; wariant połączeń jest osobnym, nadal częściowym rachunkiem. [Cloud Run billing](https://cloud.google.com/run/docs/configuring/billing-settings), [Scaleway FAQ](https://www.scaleway.com/en/docs/serverless-containers/faq/).

Workers Rust kompiluje do Wasm; nie jest zamiennikiem uruchomienia natywnego procesu Tokio/Axum. Cloudflare Containers uruchamia OCI, ale aktualne FAQ nadal opisuje wybierane instancje i brak wbudowanego autoskalowania aplikacji stateless; dysk jest efemeryczny. Kontroler Durable Object i Worker są dodatkowo rozliczane. [Rust](https://developers.cloudflare.com/workers/languages/rust/), [Containers FAQ](https://developers.cloudflare.com/containers/faq/). Cena R2 EU nie oznacza gwarancji, że globalny Worker przetwarza dane wyłącznie w UE; tę granicę trzeba potwierdzić osobno. Sam wybór regionu nie jest deklaracją zgodności prawnej.

AWS wyceniono bez NAT: publiczne taski za ALB, prywatna baza i ograniczenia sieciowe. Jeżeli wymagamy prywatnych tasków z dostępem do internetu, NAT/PrivateLink trzeba doliczyć. Nie użyto ceny amerykańskiego NAT jako europejskiej. GCP/AWS egress jest uwzględniony według europejskiego źródła i europejskiego odbiorcy; dodatkowy cross-AZ ruch nie. [AWS transfer — Irlandia](https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/eu-west-1/index.json), [GCP sieć](https://cloud.google.com/vpc/network-pricing).

## Co pozostaje poza sumą

Żaden wariant nie jest oznaczony jako kompletny: brak opłat transakcyjnych, auth/email, płatnego wsparcia, CI/registry, telemetryki, przechowywania wersji obiektów, drugiej kopii DR oraz CPU zadań archiwizacji/przeliczeń. Nie ma LLM/GPU, embeddingów, screenshotów ani audio. RDS extra IOPS/throughput, CPU credits małej bazy, cross-zone transfer i zweryfikowany ruch PG poza Scaleway wymagają dopisania do konfiguracji wybranej po benchmarku. Backup objętościowy nie zastępuje testu odtworzenia.

## Weryfikacja i odtworzenie obliczeń

```sh
python scripts/research/cloud_costs.py
python scripts/research/cloud_costs.py --input docs/research/2026-09/cloud-cost-inputs.json --output /tmp/focuswatch-cloud-costs.json
```

Kalkulator przy każdym uruchomieniu sprawdza znane wyniki 3840 obserwacji/dzień, 28 800 uploadów/miesiąc i 345 600 obserwacji/90 dni; zgodność jednostek, sum składników, konwersji FX i nieujemność kosztów. Osobna asercja chroni przed błędem Fargate polegającym na zaliczaniu nocnego minimum instancji na poczet CPU wykonywanego w aktywnych 8 godzinach. W niezależnym review uzupełniono też dwa żądania pobrania na batch.

Kalkulator korzysta wyłącznie ze standardowej biblioteki Pythona, nie wykonuje żądań sieciowych ani nie czyta konfiguracji aplikacji. Zmiany cen/parametrów wykonuje się w kopii input JSON, a potem porównuje wyniki. Tabele w tym dokumencie są snapshotem parametrów bazowych; po zmianie wejścia trzeba je odświeżyć. Wszystkie stawki należy ponownie zweryfikować przed faktycznym zamówieniem zasobów.
