# FRAMEWORK MACRO TATTICO (FMT)
*Appendice Operativa del documento di Investment Policy Statement (IPS) della Famiglia Orsini*

---

| | |
| :--------------------- | :--------------- |
| **Versione** | 1.0              |
| **Data di Redazione** | 2026             |
| **Documento Correlato**| IPS Versione 1.0 |
| **Ambito Operativo** | Gestione dei Tilt Tattici entro le Bande di Tolleranza |

---

## Sezione 1 — Introduzione e Scopo del Documento

Il presente **Framework Macro Tattico** (di seguito «FMT») definisce la metodologia con cui il Sottoscrittore (Orsini Mario) integra l'analisi quantitativa dei regimi macroeconomici con la gestione operativa del portafoglio finanziario familiare. 

Come stabilito nella **Sezione 5.10 dell'Investment Policy Statement (IPS)**, l'asset allocation strategica (SAA) rappresenta la struttura portante e robusta di lungo periodo, progettata per essere mantenuta *through-the-cycle*. Tuttavia, l'evidenza storica e la letteratura finanziaria dimostrano che i mercati attraversano stati discreti e persistenti («regimi») in cui i premi al rischio, le volatilità e le correlazioni tra asset class deviano sensibilmente dalle medie storiche.

L'obiettivo del FMT non è il *market timing* speculativo o la previsione infallibile del futuro, bensì l'**ottimizzazione della robustezza del portafoglio nel medio termine** e la **riduzione del rischio di perdita permanente del capitale** (*Loss Mitigation*). Il framework opera in modo strettamente vincolato e subordinato all'IPS, intervenendo esclusivamente attraverso scostamenti controllati («tilt tattici») che rispettano rigorosamente le bande di tolleranza predefinite.

---

## Sezione 2 — Il Sistema di Rilevazione: Composite Regime Score (CRS)

Per eliminare la componente emotiva e il bias di ancoraggio (*anchoring*), il framework si appoggia su una metodologia quantitativa basata sul **Composite Regime Score (CRS)**, aggiornato con cadenza settimanale. 

### 2.1 Metodologia di Calcolo delle Variabili
Ogni indicatore inserito nel dashboard viene normalizzato in un punteggio analogico compreso nell'intervallo `[0, 1]` tramite **min-max rescaling** su una finestra mobile storica (lookback) di 5 o 10 anni (pari a 260 o 520 settimane):

$$	ext{Rank}(x) = rac{x_t - x_{\min}}{x_{\max} - x_{\min}}$$

Per gli indicatori in cui un valore elevato rappresenta una condizione di stress o rischio recessivo (es. spread creditizi, VIX), viene applicata la polarità inversa:

$$	ext{Rank}_{	ext{inv}}(x) = 1 - 	ext{Rank}(x)$$

La convenzione di lettura è univoca per l'intero sistema:
* **Valori prossimi a 1.0:** Segnalano condizioni di forte espansione reale, pressioni inflazionistiche crescenti o euforia/compiacenza sui mercati (*Risk-On*).
* **Valori prossimi a 0.0:** Segnalano contrazione economica, pressioni deflazionistiche, restrizione del credito o panico/avversione al rischio (*Risk-Off*).

### 2.2 Architettura dei Sub-Indici Ponderati
Il CRS viene ottenuto aggregando 4 sub-indici specifici, costruiti per isolare i vettori macroeconomici fondamentali:

1. **Growth Score ($S_G$ — Peso 30%):** Misura l'impulso dell'attività economica reale.
   * *Indicatori inclusi:* ISM Manufacturing PMI (livello e spread ordini/inventari), Conference Board Leading Economic Index ($\Delta$ a 6 mesi), Nonfarm Payrolls (media mobile a 3 mesi).
2. **Inflation Score ($S_I$ — Peso 30%):** Cattura le dinamiche di prezzo e le aspettative inflazionistiche stimate dal mercato fixed income.
   * *Indicatori inclusi:* TIP/IEF Ratio (proxy del break-even inflazionistico), Oil/Gold Ratio, M2 Money Supply YoY%, Copper/Gold Ratio.
3. **Risk Score ($S_R$ — Peso 25%):** Monitora l'appetito per il rischio espresso dai mercati azionari e dal fixed income.
   * *Indicatori inclusi:* Spread XLY/XLP (Barometro retail), Spread XLK/XLU (Growth vs Defensive), JNK/LQD Ratio (Rischio di credito puro), VIX Term Structure ($VIX3M/VIX$).
4. **Monetary Score ($S_M$ — Peso 15%):** Valuta il livello di restrittività o accomodamento della politica monetaria globale.
   * *Indicatori inclusi:* Fed Funds Rate vs Taylor Rule, Fed Funds Futures Implied Rate (12 mesi), DXY Index (polarità inversa).

Il punteggio finale viene calcolato tramite combinazione lineare:

$$	ext{CRS}_t = 0.30 \cdot S_G + 0.30 \cdot S_I + 0.25 \cdot S_R + 0.15 \cdot S_M$$

---

## Sezione 3 — Tassonomia e Mappatura dei Regimi

Il framework mappa lo spazio macroeconomico continuo identificando 5 regimi discreti. La classificazione avviene attraverso l'intersezione e la convergenza dei sub-indici quantitativi:

```
                  Crescita Elevata (S_G > 0.55)
                                │
                                │     Reflazione
             Goldilocks         │     (S_I > 0.60)
            (S_I 0.30-0.55)     │
                                │
Inflazione ─────────────────────┼───────────────────── Inflazione
In Calo                         │                     In Salita
                                │
              ZIRP / QE         │     Stagflazione
            (S_I < 0.35)        │     (S_I > 0.65)
                                │
                                │
                  Contrazione Reale (S_G < 0.45)
                  [Se S_G < 0.30 e S_R < 0.25 = BUST]
```

1. **Goldilocks (Crescita Virtuosa):** Caratterizzato da $S_G > 0.60$, $S_I$ stabile e moderato ($0.30 - 0.55$) e $S_R > 0.65$. Scenario ideale per l'accumulo di equity puro.
2. **Reflazione (Surriscaldamento Ciclico):** Caratterizzato da $S_G > 0.55$ e $S_I > 0.60$. La crescita è vigorosa ma accompagnata dall'accelerazione dei prezzi.
3. **Stagflazione (Shock di Offerta):** Il quadrante più critico per i portafogli bilanciati tradizionali. Caratterizzato da $S_G < 0.45$ e $S_I > 0.65$. Contrazione reale combinata con inflazione persistente.
4. **Deflazione / Bust (Crisi Sistemica):** Caratterizzato da $S_G < 0.30$, $S_I < 0.35$ e un crollo del Risk Score ($S_R < 0.25$). Le correlazioni convergono verso 1.0 e la liquidità si azzera.
5. **ZIRP / QE (Repressione Finanziaria):** Caratterizzato da una crescita anemica ($S_G$ tra $0.30$ e $0.55$), spinte inflazionistiche assenti ($S_I < 0.35$), ma supporto massiccio delle banche centrali ($S_M$ ai minimi, $S_R > 0.70$ guidato dalla caccia al rendimento).

---

## Sezione 4 — Matrice di Allocazione Tattica e Regole di Inclinazione (Tilt)

I tilt tattici operano sotto un vincolo geometrico assoluto: **nessun peso effettivo può violare le bande di tolleranza definite dall'IPS**. Il framework ridistribuisce il capitale tra le componenti nel rispetto dei limiti minimi e massimi di ciascun ruolo.

### 4.1 Limiti e Bande di Tolleranza Rigide (IPS 5.8)
* **Macro-Componente Azionaria Totale:** Min 45% / Target 65% / Max 75%
* **Macro-Componente Difensiva Totale:** Min 30% / Target 35% / Max 40%
* **VWCE (Equity Substitute):** Min 45% / Target 55% / Max 65%
* **DBMFE (Managed Futures):** Min 10% / Target 15% / Max 20%
* **BOND (Gov. EUR / Ladder):** Min 7% / Target 10% / Max 15%
* **GOLD (Oro fisico):** Min 3% / Target 5% / Max 8%
* **Equity Complement Fama-French (ZPRV + ZPRX):** Min 5% / Target 10% / Max 15%

### 4.2 Matrice Operativa dei Pesi Tattici per Regime

| Ruolo Funzionale / Strumento | SAA Target | Goldilocks | Reflazione | Stagflazione | Deflazione / Bust | ZIRP / QE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **VWCE** (Equity Substitute) | **55.0%** | 62.5% | 50.0% | 45.0% | 45.0% | 60.0% |
| **ZPRV** (US Small Value) | **7.5%** | 7.5% | 11.0% | 5.0% | 5.0% | 6.0% |
| **ZPRX** (EU Small Value) | **2.5%** | 2.5% | 4.0% | 2.0% | 2.0% | 2.0% |
| *Totale Componente Azionaria* | *65.0%* | *72.5%* | *65.0%* | *52.0%* | *52.0%* | *68.0%* |
| **DBMFE** (Managed Futures) | **15.0%** | 10.0% | 15.0% | 20.0% | 18.0% | 12.0% |
| **CRRY** (FX/Macro Carry) | **5.0%** | 6.5% | 7.0% | 3.0% | 3.0% | 6.0% |
| **GOLD** (Oro Fisico) | **5.0%** | 4.0% | 6.0% | 8.0% | 7.0% | 4.0% |
| **BOND** (Gov. EUR / Ladder) | **10.0%** | 7.0% | 7.0% | 17.0% | 20.0% | 10.0% |
| *Totale Componente Difensiva* | *35.0%* | *27.5%* | *35.0%* | *48.0%* | *48.0%* | *32.0%* |
| **Verifica Somma Quadrante** | **100%** | **100%** | **100%** | **100%** | **100%** | **100%** |

### 4.3 Razionale Finanziario dei Riorientamenti Tattici

#### Scenario Goldilocks (CRS: 0.45 – 0.65)
Il motore azionario viene spinto verso la banda superiore (`72.5%`). Si massimizza il beta azionario puro tramite **VWCE** (`62.5%`), riducendo la componente obbligazionaria a breve termine al minimo consentito (`7.0%`) e contraendo la protezione di **DBMFE** (`10.0%`), poiché in assenza di trend macroeconomici distruttivi il trend following subisce un costo di mantenimento latente.

#### Scenario Reflazione (CRS: 0.65 – 0.80)
L'azionario totale rimane al target strategico (`65%`), ma avviene una profonda rotazione interna. Si sottopesa il growth generalista a favore dell'**Equity Complement Fama-French (Small Cap Value)** che sale al massimo consentito (`15.0%` complessivo, suddiviso in `11.0%` ZPRV e `4.0%` ZPRX). Le Small Cap Value beneficiano strutturalmente dell'aumento dei tassi nominali, della ripresa dei margini industriali e della compressione dei multipli dei titoli growth. **CRRY** sale al `7.0%` per catturare i differenziali di tasso in espansione. I governativi lunghi e la duration vengono compressi al minimo (`7.0%`) per proteggere il capitale dall'inflazione e dalle perdite in conto capitale.

#### Scenario Stagflazione (CRS: 0.40 – 0.60 con Growth/Inflation in divergenza)
L'azionario viene ridotto al minimo difensivo consentito (`52.0%`), penalizzando fortemente l'esposizione fattoriale value che soffre la contrazione degli utili reali. Il capitale viene riallocato sui beni reali e sulle strategie anticicliche: **GOLD** sale al limite massimo del `8.0%` per fungere da riserva di valore macroeconomica; **DBMFE** viene incrementato al `20.0%` (limite massimo IPS) per sfruttare i trend direzionali estesi che tipicamente si formano sulle commodity e sui tassi d'interesse durante le crisi di offerta. La componente **BOND** sale al `17.0%` concentrandosi sulla ladder a scadenze cortissime per azzerare il rischio duration e incassare i tassi nominali elevati.

#### Scenario Deflazione / Bust (CRS: 0.05 – 0.30)
Si attiva la massima protezione patrimoniale. La componente azionaria scende al minimo assoluto (`52.0%`). Viene liquidata la strategia **CRRY** (`3.0%`), che nei momenti di shock di liquidità subisce il rischio di *deleveraging* e di correlazione asimmetrica instabile. La componente **BOND** sale al massimo storico del `20.0%` complessivo. In questo scenario, coerentemente con le opzioni previste dall'**IPS (Sezione 4.5 e 5.4)**, si privilegia l'acquisto diretto in ladder di titoli di Stato italiani (BTP) ed europei a scadenze scalari, beneficiando sia della deflazione dei tassi (capital gain su asset privi di rischio) sia della protezione normativa di esclusione dal calcolo dell'indicatore ISEE familiare.

#### Scenario ZIRP / QE (CRS: 0.45 – 0.65 con Inflation < 0.35 e Monetary < 0.30)
In un contesto di stagnazione secolare supportata da tassi a zero e acquisti straordinari delle banche centrali, il portafoglio inclina verso gli asset a duration infinita. **VWCE** viene incrementato al `60.0%` poiché beneficia direttamente del calcolo del valore attuale dei flussi di cassa scontati a tassi prossimi allo zero (espansione dei multipli azionari growth). Le strategie fattoriali value vengono parzialmente contratte a causa della debolezza strutturale del ciclo macroeconomico reale. **CRRY** viene mantenuto al `6.0%` come generatore di carry artificiale in un mondo a rendimento zero.

---

## Sezione 5 — Workflow Operativo e Regole di Transizione

Per evitare l'errore del *churning* (eccesso di operazioni con impatto commissionale e fiscale negativo), l'attivazione dei tilt tattici segue una disciplina algoritmica rigida basata sulla frequenza di monitoraggio armonizzata con l'**IPS (Sezione 7.2)**.

### 5.1 Il Protocollo in 6 Fasi (Esecuzione Lunedì Mattina)
1. **Fase 1 (Data Gathering):** Il Sottoscrittore aggiorna il dataset estraendo i dati di chiusura del venerdì precedente. Le fonti obbligatorie e gratuite sono la piattaforma FRED della Federal Reserve per le serie macroeconomiche e Yahoo Finance (`yfinance` via Python) per i prezzi degli ETF di mercato e i rapporti settoriali.
2. **Fase 2 (Ranking & Normalization):** Calcolo dei punteggi analogici individuali e determinazione dei 4 sub-indici ($S_G, S_I, S_R, S_M$).
3. **Fase 3 (Score Validation):** Verifica dei limiti formali: il CRS deve risultare rigorosamente incluso nell'intervallo `[0, 1]`. Se un indicatore tocca esattamente `0` o `1`, viene registrato un nuovo estremo storico nel file di log.
4. **Fase 4 (Momentum Analysis):** Calcolo della velocità di transizione del punteggio su orizzonte quadrisettimanale: $\Delta_{4w} = 	ext{CRS}_t - 	ext{CRS}_{t-4}$.
5. **Fase 5 (Tilt Validation):** Un cambio di regime e la conseguente transizione di allocazione tattica vengono attivati esclusivamente se si verifica uno dei due **Trigger di Transizione**:
   * *Trigger di Soglia:* Il CRS attraversa una delle barriere critiche (`0.25`, `0.45`, `0.65`, `0.80`) e permane oltre tale soglia per **4 settimane consecutive**.
   * *Trigger di Velocità:* Il momentum a breve termine registra un'accelerazione anomala pari a $|\Delta_{4w}| > 0.15$. In questo caso, la transizione si considera immediata per shock macroeconomico e i pesi vengono adeguati senza attendere la conferma quadrisettimanale.
6. **Fase 6 (Deviation Score & Implementation):** Calcolo dello scostamento tra i pesi correnti del portafoglio e i pesi target del nuovo regime identificato. L'operatività segue la **Regola di Esecuzione Fiscale** definita al punto 5.2.

### 5.2 Regola di Esecuzione Fiscale e Flussi Ingressi
In piena armonia con i guardrail comportamentali dell'**IPS (Sezione 5.8 e 7.7)**, il Sottoscrittore minimizza il realizzo di plusvalenze tassabili al 26%:
* **Fase di Accumulo Ordinaria:** Il riorientamento tattico avviene primariamente canalizzando i flussi finanziari dei risparmi mensili (€300 - €600) verso gli asset sottopesati nel nuovo regime. I portafogli non vengono riscritti tramite compravendite massive se lo scostamento tattico può essere corretto in modo inerziale entro 6 mesi tramite i versamenti periodici.
* **Iniezione di Capitali Straordinari:** Qualora si realizzino gli afflussi straordinari attesi da lasciti ereditari descritti nell'**IPS (Sezione 2.4 e 3.1)** per un totale stimato di €245.000, tali capitali non saranno allocati in un'unica soluzione sulla base del regime corrente, ma saranno inseriti attraverso un piano di accumulo frazionato tatticamente, utilizzando il CRS settimanale come indicatore di convenienza (*Value-Averaging* macroeconomico).
* **Compravendita Diretta:** Le operazioni di vendita per ribilanciamento tattico straordinario sono autorizzate soltanto se il *Deviation Score* di una singola componente supera la banda di tolleranza assoluta del `5%` rispetto al target di regime e i flussi in ingresso mensili risultano matematicamente insufficienti a colmare il gap.

---

## Sezione 6 — Registro delle Decisioni Tattiche (Log Operativo)

Ogni modifica tattica dell'allocazione, ogni lettura formale dei sub-indici e l'attivazione dei trigger di transizione devono essere registrate in forma scritta nel Log Operativo, costituendo memoria storica del portafoglio per il Sottoscrittore e per la **Persona Designata di Emergenza (IPS Sezione 6.3)**.

### 6.1 Modello di Registrazione Obbligatorio

```
┌───────────────────────────────────────────────────────────────────────────┐
│ REGISTRO DELLE DECISIONI MACRO TATTICHE (FMT LOG)                         │
├───────────────────────────────────────────────────────────────────────────┤
│ DATA VALUTAZIONE: [DD/MM/YYYY]            VOTO CRS ATTUALE: [0.XX]        │
├───────────────────────────────────────────────────────────────────────────┤
│ VALORI SUB-INDICI:                                                        │
│ - Growth Score (S_G):    [0.XX]      - Inflation Score (S_I): [0.XX]      │
│ - Risk Score (S_R):      [0.XX]      - Monetary Score (S_M):  [0.XX]      │
├───────────────────────────────────────────────────────────────────────────┤
│ REGIME MACRO IDENTIFICATO:                                                │
│ [ ] Goldilocks  [ ] Reflazione  [ ] Stagflazione  [ ] Deflazione  [ ] ZIRP│
├───────────────────────────────────────────────────────────────────────────┤
│ TRIGGER ATTIVATO:                                                         │
│ [ ] Nessuno (Mantenimento Regime Precedente)                              │
│ [ ] Trigger di Soglia (Conferma 4 settimane consecutive)                  │
│ [ ] Trigger di Velocità (|Δ4w| > 0.15)                                    │
├───────────────────────────────────────────────────────────────────────────┤
│ NOTA DI NARRATIVA MACROECONOMICA (Descrizione del contesto reale):        │
│ _________________________________________________________________________ │
│ _________________________________________________________________________ │
├───────────────────────────────────────────────────────────────────────────┤
│ OPERAZIONI SPECIFICHE PIANIFICATE / ESEGUITE:                             │
│ Strumento  │ Peso Prec. │ Peso Target │ Delta Tattico │ Azione Richiesta │
│ ───────────┼────────────┼─────────────┼───────────────┼──────────────────│
│ VWCE       │   XX.X%    │    XX.X%    │   +/- X.X%    │ [Acquisto/Hold]  │
│ ZPRV       │   XX.X%    │    XX.X%    │   +/- X.X%    │ [Acquisto/Hold]  │
│ ZPRX       │   XX.X%    │    XX.X%    │   +/- X.X%    │ [Acquisto/Hold]  │
│ DBMFE      │   XX.X%    │    XX.X%    │   +/- X.X%    │ [Acquisto/Hold]  │
│ CRRY       │   XX.X%    │    XX.X%    │   +/- X.X%    │ [Acquisto/Hold]  │
│ GOLD       │   XX.X%    │    XX.X%    │   +/- X.X%    │ [Acquisto/Hold]  │
│ BOND       │   XX.X%    │    XX.X%    │   +/- X.X%    │ [Acquisto/Hold]  │
├───────────────────────────────────────────────────────────────────────────┤
│ DATA EFFETTIVA ESECUZIONE OPERATIVA: [DD/MM/YYYY]                         │
│ FIRMA DEL SOTTOSCRITTORE: _______________________________________________ │
└───────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Clausola di Incertezza e Ritorno alla SAA Target
Nel caso in cui i sub-indici presentino letture conflittuali, volatilità erratica o assenza di convergenza statistica chiara (es. CRS oscillante stabilmente intorno a `0.50` con sub-indici frammentati), il framework riconosce lo stato di **Incertezza Strutturale**. 

In questo scenario si applica il principio dell'**umiltà epistemica**: il Sottoscrittore ha l'obbligo di revocare qualsiasi inclinazione tattica precedentemente attiva e di **riportare immediatamente il portafoglio ai pesi target dell'Asset Allocation Strategica (SAA)** definiti nella Sezione 5.3 dell'IPS. La SAA costituisce l'unico vero ancoraggio neutrale attraverso i cicli.

---

## Sezione 7 — Firme e Validità Interdipendente

Il presente Framework Macro Tattico non sostituisce né modifica l'Investment Policy Statement (IPS). Esso ne costituisce un'estensione tecnica finalizzata a disciplinarne l'operatività dinamica. Qualsiasi violazione dei limiti imposti dal presente documento equivale a una violazione dell'IPS stesso.

Il Sottoscrittore dichiara di comprendere le regole, i vincoli matematici e i presupposti finanziari qui descritti, impegnandosi ad applicare la procedura di monitoraggio senza deroghe emotive.


Sottoscrittore (Orsini Mario): ___________________________________   Data: _______________
