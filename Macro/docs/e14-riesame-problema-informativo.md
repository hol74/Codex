# E14 - Riesame del problema informativo

Data: 2026-07-14

## Sintesi

E13 non e' fallita soltanto per una formula imperfetta. L'audit E14 mostra tre
limiti distinti:

1. le feature broad-market si sovrappongono molto tra episodi finanziari e
   mesi di contrasto;
2. gli episodi finanziari osservabili appartengono a meccanismi diversi e non
   condividono una singola intensita' scalare;
3. i mesi usati come controlli non sono veri negativi finanziari confermati,
   mentre la cronologia e' troppo corta per validare detector specializzati.

Per questo non conviene generare subito un'altra famiglia di formule.

## Evidenza misurata

L'audit usa soltanto 84 date inner, da maggio 2016 ad aprile 2023. Sono
osservabili 3 episodi finanziari, 7 mesi positivi, 23 mesi di contrasto curato
e 54 mesi non etichettati esclusi dalle metriche di classe.

| Feature normalizzata | AUC direzionale positivo > contrasto | Sovrapposizione range | Lettura |
|---|---:|---:|---|
| VIX intramese | 0,292 | 95,7% | i controlli 2021-22 sono spesso piu' elevati |
| drawdown SPY | 0,478 | 78,0% | quasi nessuna separazione marginale |
| drawdown HYG | 0,404 | 53,5% | separazione debole e orientamento instabile |
| HY OAS | 0,752 | 73,3% | informazione moderata, ma range ancora sovrapposto |
| SOFR-EFFR max | 1,000 | 0% | segnale forte nel campione, ma fragile e corto |

L'AUC funding perfetta deriva da soli 7 positivi e 23 contrasti, tutti dopo
l'inizio della serie SOFR. Non dimostra generalizzazione: il repo 2019 ha
funding severity media `0,545`, mentre risk repricing 2018 e regional banking
2023 hanno rispettivamente `0,12` e `0,0125`. Una soglia funding unica non
rappresenta quindi la stessa causa economica nei tre episodi.

## Eterogeneita' degli episodi

- `risk-repricing-2018q4`: shock broad-market, drawdown SPY medio `0,420`, VIX
  `0,236`; noisy-or rileva 3/3 mesi, top-two soltanto 1/3.
- `repo-stress-2019`: shock idiosincratico di funding, con feature equity e
  credit molto basse; entrambi gli aggregatori rilevano 1/2 mesi.
- `regional-bank-stress-2023`: segnali broad-market e funding deboli;
  noisy-or rileva 1/2 mesi e top-two 0/2.

Il problema non e' risolvibile aumentando o diminuendo una soglia globale:
una soglia bassa cattura meccanismi deboli ma accende l'intero 2021-22; una
soglia alta elimina i falsi allarmi ma perde repo e banking stress.

## Problema delle label

I 23 mesi di contrasto sono tutti `inflation_shock`; 12 sono anche
`monetary_tightening`. La cronologia dichiara esplicitamente che l'assenza di
label non costituisce un vero negativo. Chiamare ogni allerta su questi mesi
un falso positivo e' quindi una scelta conservativa utile per il gate, ma non
una ground truth completa sullo stress finanziario.

Questo spiega parte del 73,91% di alert noisy-or sui contrasti: il modello
reagisce a condizioni finanziarie tese durante inflazione e tightening, che
la tassonomia corrente non classifica come `financial_stress`. Non possiamo
stabilire dal corpus attuale se siano errori del modello o ambiguita' della
label.

## Problema recessivo

Nelle finestre inner e' osservabile soltanto la recessione COVID-19. Il ramo
recessivo non ha quindi ancora prodotto evidenza sulla separabilita' delle
feature tra cicli: il blocco e' prima di tutto nella copertura temporale, non
una prova che SAHM, produzione e curva siano inutili. Usare l'outer per
recuperare episodi invaliderebbe le fasi precedenti.

## Decisione architetturale

Il prossimo sistema non deve essere un altro aggregatore globale. Prima serve
una foundation informativa con:

- label tri-state: positivo, hard negative confermato, ambiguo/non etichettato;
- episodi divisi per meccanismo: broad-market repricing, funding/liquidity,
  banking/credit e recession onset;
- almeno tre episodi osservabili per ciascun detector che si vuole validare;
- feature relative al proprio regime storico, per esempio z-score o percentile
  causale del funding spread, non soltanto normalizzazioni assolute;
- onset, intensita' e recovery valutati separatamente;
- eventuale composizione solo dopo evidenza autonoma dei detector specializzati.

## Piano raccomandato

1. E14.2 - tassonomia v3 e hard-negative audit, senza modelli.
2. E14.3 - studio di fattibilita' per estendere la foundation pre-2008 e
   verificare disponibilita' point-in-time/ALFRED e proxy compatibili.
3. E14.4 - contratto dei detector per meccanismo e requisiti minimi di episodi.
4. E14.5 - solo se i gate informativi passano, nuova generazione di candidati.

Se E14.2-E14.3 non producono abbastanza episodi e veri negativi, il risultato
corretto sara' sospendere la ricerca supervisionata storica e accumulare
evidenza shadow/prospettica, non continuare a ottimizzare sullo stesso corpus.

## Esito E14.2

La tassonomia `us-financial-stress-v3` riclassifica soltanto evidenza gia'
versionata: 6 episodi positivi, 2 ambigui e zero hard negative confermati. Non
deduce negativi dall'assenza di label. Sulle 84 date inner risultano 7 mesi
positivi, 23 ambigui e 54 unlabeled; nessun mese e' un hard negative.

Il label audit richiede almeno 3 episodi positivi full e inner e 2 hard
negative per meccanismo. I gap residui sono:

| Meccanismo | Positivi full | Positivi inner | Hard negative | Ulteriori full | Ulteriori inner | Ulteriori negativi |
|---|---:|---:|---:|---:|---:|---:|
| broad-market repricing | 4 | 1 | 0 | 0 | 2 | 2 |
| funding/liquidity | 2 | 2 | 0 | 1 | 1 | 2 |
| banking/credit | 2 | 1 | 0 | 1 | 2 | 2 |
| cross-border/growth | 2 | 0 | 0 | 1 | 3 | 2 |

Il risultato e' `NOT_READY_FOR_CANDIDATE_GENERATION`. E14.3 deve ora
verificare se fonti storiche point-in-time e proxy semanticamente compatibili
possono colmare questi gap; fino a quel go/no-go non si aprono nuovi modelli.

## Esito E14.3

Il catalogo di fattibilita' distingue quattro classi as-of: vintage API,
osservazioni esistenti al tempo dell'evento, release ufficiali archiviate e
storie correnti ricostruite. Solo le prime tre possono entrare in un pilot, e
le osservazioni di mercato richiedono comunque snapshot immutabile, hash e
audit delle correzioni.

Le principali evidenze ufficiali sono:

- ALFRED espone le date in cui una serie e' stata pubblicata o revisionata:
  `https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html`;
- Cboe pubblica VIX giornaliero dal 1990:
  `https://www.cboe.com/tradable_products/vix/vix_historical_data`;
- BAA10Y e TEDRATE offrono proxy creditizi/funding dal 1986, ma TED termina
  con LIBOR nel 2022 e non puo' essere unito automaticamente a SOFR;
- NFCI copre dal 1971, ma la Chicago Fed dichiara che storia e pesi possono
  cambiare a ogni aggiornamento; resta quindi diagnostico;
- OFR FSI e STLFSI sono benchmark compositi utili, ma versioni, componenti e
  storia ricostruita impediscono di considerarli feature point-in-time;
- FDIC offre fallimenti dal 1934 e dati finanziari trimestrali dal 1984, utili
  per dossier banking con date di pubblicazione preservate.

Cinque ipotesi non etichettate (`Continental Illinois 1984`, market break
1987, Messico/bond turbulence 1994, crisi asiatica 1997 e Russia/LTCM 1998)
portano la copertura positiva proiettata sopra il minimo di tre per tutti i
meccanismi. Non sono ground truth: ciascuna richiede un dossier autonomo.

| Meccanismo | Positivi proiettati | Ipotesi hard negative | Hard negative mancanti |
|---|---:|---:|---:|
| broad-market repricing | 7 | 0 | 2 |
| funding/liquidity | 3 | 0 | 2 |
| banking/credit | 3 | 0 | 2 |
| cross-border/growth | 5 | 0 | 2 |

La decisione e' `GO_FOR_EPISODE_DOSSIERS_ONLY`: no-go alla popolazione del
corpus, go limitato alla curation. E14.4 deve congelare il contratto dei
detector e la prova affermativa richiesta per dichiarare un hard negative a
livello di singolo meccanismo.

## Esito E14.4a

Il sistema viene separato in quattro detector autonomi. Nessun punteggio
cross-mechanism e' ammesso prima che ciascun ramo abbia evidenza propria:

| Detector | Feature proposte | Benchmark solo diagnostici |
|---|---|---|
| broad-market repricing | VIX, BAA10Y | NFCI, STLFSI4, OFR FSI |
| funding/liquidity | TED spread nel solo regime LIBOR | NFCI, STLFSI4, OFR FSI |
| banking/credit | FDIC quarterly financials, BAA10Y | NFCI, STLFSI4, OFR FSI |
| cross-border/growth | broad dollar index nel proprio regime | OFR FSI |

Le feature sono ancora proposte, non popolate. Ogni trasformazione dovra'
usare soltanto storia precedente e corrente, mantenere almeno 60 mesi di
warm-up e lasciare missing i periodi non applicabili. TED/SOFR e le diverse
metodologie del dollar index non possono essere unite implicitamente.

Il modello di fase distingue `calm`, `onset`, `active` e `recovery`. Le soglie
non sono state scelte: potranno essere stimate soltanto nell'inner LOEO, con
entry ed exit distinte e recovery confermata su due mesi.

Lo schema dei dossier richiede almeno due evidenze indipendenti, hash del
contenuto, counterevidence, confini motivati e doppio reviewer per
l'accettazione. Per un hard negative `affirmativeOrderlyEvidence` deve essere
vero: assenza di label, interventi o alert non e' mai sufficiente.

Il contract audit termina `READY_FOR_DOSSIER_CURATION`. E14.4b puo' costruire
e giudicare dossier, ma non puo' ancora modificare la ground truth o popolare
il corpus; tali azioni richiederanno un successivo label-foundation gate.
