# Piano di Sviluppo — Risk Management Framework (RMF)
*Documento di pianificazione — subordinato a IPS v1.0 e FMT v1.0*

---

| | |
|---|---|
| **Versione** | 0.1 — Pianificazione |
| **Stato** | Bozza di lavoro |
| **Documento parent** | IPS v1.0 / FMT v1.0 |
| **Prossima fase** | Sviluppo Modulo 1 |

> *Il presente documento definisce la struttura, la sequenza e gli output del Risk Management Framework (RMF). Non è ancora il framework operativo: è la mappa di ciò che verrà costruito. Ogni modulo sarà sviluppato in un documento separato o integrato nel presente documento nelle fasi successive.*

---

## Sezione 0 — Il cambio di prospettiva: da asset-first a risk-first

### 0.1 Due modi di costruire un portafoglio

Il TPA adottato nell'IPS e i tilt del FMT partono dagli **asset**: si decide cosa comprare, in quale peso, con quale inclinazione tattica. È un approccio valido e coerente con gli obiettivi di lungo periodo.

Un framework di risk management inverte la direzione di ragionamento: parte dal **rischio** che si è disposti a sopportare e determina da esso la composizione, il monitoraggio e le regole di intervento del portafoglio. Le domande di partenza cambiano:

| Approccio asset-first | Approccio risk-first |
|---|---|
| Quale peso assegno a VWCE? | Quanto rischio azionario posso sopportare senza dover liquidare? |
| Quando ribilancio? | Quale evento renderebbe il ribilanciamento impossibile? |
| Come mi posiziono in Stagflazione? | Quanto perdo nel peggior scenario di Stagflazione e quanto tempo impiego a recuperare? |
| Quanto pesa la componente difensiva? | Quanta volatilità elimina la componente difensiva e a che costo in termini di rendimento atteso? |

I due approcci sono complementari. Il RMF non sostituisce l'IPS né il FMT: si affianca a essi come strato di controllo e verifica che il portafoglio rimanga entro i limiti di rischio compatibili con i vincoli strutturali del Sottoscrittore.

### 0.2 Il rischio primario di questo portafoglio

L'IPS ha già identificato con precisione il rischio primario alla Sezione 2.5:

> *«Il rischio primario non è la volatilità bensì il rischio di liquidazione forzata in momenti di mercato avversi.»*

Questo principio è il punto di partenza dell'intero RMF. Ogni metrica, ogni strumento di monitoraggio, ogni soglia di allerta deve rispondere a una sola domanda fondamentale: **questo portafoglio è in condizioni di essere parzialmente liquidato in qualsiasi momento, indipendentemente dalle condizioni di mercato, senza compromettere la strategia di lungo periodo?**

La volatilità è rilevante non in sé, ma come proxi del rischio di timing della liquidazione: liquidare in un momento di alta volatilità e drawdown profondo è molto più costoso che liquidare in mercato calmo.

### 0.3 Posizione del RMF nell'architettura documentale

```
IPS — Investment Policy Statement (governance principale)
  │
  ├── FMT — Framework Macro Tattico (tilt tattici per regime)
  │         Risponde a: "In che regime siamo? Come incliniamo il portafoglio?"
  │
  └── RMF — Risk Management Framework (controllo del rischio)      ← questo documento
            Risponde a: "Il portafoglio sta rispettando il budget di rischio?
                         Siamo vicini a una soglia critica?
                         Cosa succede in uno scenario avverso?"
```

Il RMF è un documento operativo subordinato all'IPS. Non introduce strumenti non ammessi, non modifica i pesi target e non sostituisce la revisione annuale. Produce output di monitoraggio e trigger di azione che si raccordano con i meccanismi di governance già definiti nell'IPS (Sezione 6.7 — trigger di revisione straordinaria) e nel FMT (Sezione 4 — procedura operativa).

---

## Sezione 1 — Mappa dei moduli

Il RMF è strutturato in **sette moduli**. Ogni modulo ha un obiettivo specifico, un insieme di domande da rispondere e uno o più output tangibili.

---

### Modulo 1 — Risk Budget e Risk Appetite

**Obiettivo primario:** Tradurre il risk appetite qualitativo dell'IPS in un insieme di parametri quantitativi operativi che definiscano il "budget di rischio" del portafoglio.

**Il problema da risolvere:** L'IPS dichiara alta tolleranza alla volatilità ma identifica nella liquidazione forzata il rischio primario. Queste due affermazioni devono essere riconciliate in un numero: qual è il drawdown massimo tollerabile prima che il portafoglio non sia più in grado di soddisfare un'esigenza straordinaria di liquidità senza sacrificare la componente di crescita di lungo periodo?

**Domande operative:**
- Qual è il drawdown massimo che non richiede liquidazione della componente azionaria (VWCE)?
- Qual è il drawdown oltre il quale anche la componente difensiva non è sufficiente come "cuscinetto"?
- Qual è la volatilità annualizzata compatibile con la psicologia e i vincoli strutturali del Sottoscrittore?
- Come si distribuisce il budget di rischio tra le sette componenti del portafoglio?
- Qual è il Contribution to Portfolio Volatility (CPV) implicito nel portafoglio strategico corrente? È coerente con i ruoli funzionali assegnati dal TPA?

**Concetti e strumenti da sviluppare:**
- *Volatility target:* deviazione standard annualizzata obiettivo del portafoglio complessivo
- *Drawdown limit:* soglia massima di drawdown compatibile con il vincolo di liquidità (calibrata sull'entità delle esigenze straordinarie storiche e prospettiche del nucleo familiare)
- *Risk budgeting:* distribuzione del budget di rischio tra componenti, espressa sia come contributo alla volatilità assoluta sia come percentuale del rischio totale
- *Equal Risk Contribution (ERC):* allocazione alternativa "di riferimento" in cui ogni componente contribuisce ugualmente al rischio totale — da confrontare con l'allocazione corrente per identificare concentrazioni di rischio nascoste
- *Marginal Contribution to Risk (MCR):* variazione del rischio totale del portafoglio per una variazione unitaria del peso di ogni componente — strumento per ottimizzare i tilt del FMT in ottica risk-adjusted

**Output attesi:**
1. Risk Appetite Statement formalizzato (3-5 paragrafi quantitativi)
2. Tabella del risk budget per componente (peso nominale vs. contributo al rischio vs. CPV)
3. Confronto ERC vs. allocazione strategica corrente: dove sono le concentrazioni di rischio implicite?
4. Definizione operativa dei tre livelli di drawdown rilevanti per il portafoglio:
   - Livello 1 — Monitoraggio attivo (drawdown X%): nessuna azione, registrazione nel registro delle decisioni
   - Livello 2 — Allerta (drawdown Y%): attivazione KRI, verifica liquidità disponibile
   - Livello 3 — Revisione straordinaria (drawdown 30%): trigger già previsto dall'IPS Sezione 6.7

**Dipendenze:** IPS Sezioni 2.5, 3.5, 5.8, 6.7

---

### Modulo 2 — Risk Decomposition

**Obiettivo primario:** Decomporre il rischio del portafoglio nelle sue componenti fondamentali per strumento, per fattore sistematico e per regime macroeconomico.

**Il problema da risolvere:** Il portafoglio è costruito con sette strumenti con ruoli funzionali diversi. Ma quanto rischio "reale" porta ogni strumento? È possibile che VWCE (55% del peso nominale) contribuisca al 75% o più del rischio totale? E come cambia questa decomposizione quando il regime cambia e le correlazioni si modificano?

**Domande operative:**
- Qual è la matrice di covarianza tra le componenti del portafoglio in condizioni normali?
- Come cambia la matrice di covarianza nelle fasi di stress (correlation breakdown)?
- Qual è l'esposizione implicita del portafoglio ai fattori sistematici principali (mercato/beta, size, value, momentum, carry, trend)?
- Esiste diversificazione "vera" tra le componenti, o alcune correlazioni sono più alte di quanto il TPA assuma?
- Come si modifica la decomposizione del rischio per regime (Goldilocks, Stagflazione, Deflazione)?

**Concetti e strumenti da sviluppare:**
- *Matrice di correlazione storica:* correlazioni rolling tra le componenti su finestre multiple (3 anni, 5 anni, 10 anni)
- *Matrice di correlazione condizionata per regime:* le correlazioni negli ultimi X mesi di ogni regime storico identificato — la correlazione tra DBMFE e VWCE in regime di Deflazione è diversa da quella in regime Goldilocks
- *Factor exposure analysis:* posizione del portafoglio lungo i principali fattori sistematici tramite regressione dei rendimenti storici degli ETF sulle serie fattoriali (Fama-French, AQR, ecc.)
- *Diversification ratio:* rapporto tra la media ponderata delle volatilità individuali e la volatilità del portafoglio — misura sintetica del beneficio della diversificazione
- *Correlation stress analysis:* cosa succede al rischio del portafoglio se tutte le correlazioni convergono a 1 (scenario di crisi liquidity-driven)?

**Output attesi:**
1. Matrice di correlazione storica a diversi orizzonti temporali (tabella 7×7)
2. Matrice di correlazione condizionata per i sei regimi del FMT (6 tabelle 7×7)
3. Tabella di factor exposure: esposizione del portafoglio aggregato ai fattori sistematici principali
4. Diversification ratio storico del portafoglio (serie temporale)
5. Analisi "correlation stress": contributo al rischio di ogni componente quando le correlazioni saltano

**Dipendenze:** Modulo 1, FMT Sezione 2

---

### Modulo 3 — Drawdown Management

**Obiettivo primario:** Modellare il comportamento del portafoglio nelle fasi di ribasso, con focus sul drawdown come metrica di rischio primaria, coerentemente con il vincolo di liquidità dell'IPS.

**Il problema da risolvere:** La volatilità è simmetrica (cattura sia i rialzi che i ribassi), ma il rischio di liquidazione forzata è asimmetrico: riguarda solo i ribassi e solo nei momenti peggiori. Il drawdown — la riduzione percentuale dal massimo precedente — è la metrica più rilevante per questo specifico investitore. Il modulo deve rispondere alla domanda: quante volte, per quanto tempo e con quale profondità il portafoglio scenderà sotto il suo massimo storico nel corso dei 15 anni di accumulo?

**Domande operative:**
- Qual è la distribuzione storica del drawdown per un portafoglio con questa composizione su orizzonti di 1, 3, 5 anni?
- Qual è il tempo medio di recupero da un drawdown del 20%? Del 30%?
- In quale regime macroeconomico il drawdown è stato storicamente più profondo e più lungo?
- Esiste un livello di drawdown "critico" — specifico per questo portafoglio e per questa situazione familiare — oltre il quale la liquidazione dell'azionario diventerebbe obbligatoria anche in assenza di esigenze straordinarie?
- Come si confronta il drawdown del portafoglio corrente con quello del benchmark 60/40 e con quello di un portafoglio VWCE 100%?

**Concetti e strumenti da sviluppare:**
- *Maximum Drawdown (MDD):* drawdown massimo su un orizzonte dato, calcolato sia storicamente che tramite simulazione
- *Conditional Drawdown at Risk (CDaR):* il drawdown medio del peggior X% degli scenari — analogo del CVaR applicato ai drawdown
- *Underwater period analysis:* per quanto tempo il portafoglio ha storicamente trascorso sotto il suo massimo precedente
- *Recovery analysis:* tempo medio e mediano per recuperare da drawdown di diversa entità
- *Pain Index / Ulcer Index:* metriche di "disagio psicologico" — catturano sia la profondità che la durata del drawdown
- *Drawdown per regime:* contributo di ogni regime macroeconomico al drawdown storico del portafoglio
- *Liquidity-adjusted drawdown:* il drawdown "effettivo" che si realizza se l'investitore è costretto a liquidare in corso di ribasso (l'impatto non è solo il drawdown corrente ma anche il mancato recupero)

**Output attesi:**
1. Distribuzione del drawdown storico simulato per orizzonte temporale (1, 3, 5, 10 anni)
2. Underwater chart: serie storica del drawdown del portafoglio simulato
3. Tabella drawdown/recovery per regime (quanto profondo e quanto lungo in ciascun regime FMT)
4. Calcolo del "punto critico di liquidità": il drawdown oltre il quale le esigenze straordinarie non possono essere soddisfatte senza intaccare VWCE in modo permanente
5. Confronto MDD: portafoglio corrente vs. benchmark 60/40 vs. VWCE 100%

**Dipendenze:** Modulo 1, Modulo 2

---

### Modulo 4 — Stress Testing e Scenario Analysis

**Obiettivo primario:** Testare il portafoglio contro eventi estremi storici e scenari ipotetici costruiti sui regimi del FMT, per verificare che la struttura del portafoglio sia effettivamente robusta agli scenari avversi per cui è stata progettata.

**Il problema da risolvere:** Il TPA è stato costruito per essere robusto a diversi scenari. Ma "robusto" è un concetto qualitativo. Lo stress testing lo rende quantitativo: in Stagflazione degli anni '70, quanto avrebbe perso questo portafoglio? In una crisi tipo 2008, DBMFE avrebbe davvero compensato il crollo di VWCE? La domanda non è solo accademica: l'investitore deve sapere se la protezione che paga sotto forma di tracking difference e underperformance in Goldilocks vale ciò che promette quando serve davvero.

**Domande operative:**
- Come si comporterebbe questo portafoglio nei principali eventi storici di stress (1973-74, 2000-02, 2008-09, 2020, 2022)?
- Per ogni scenario storico: quale componente ha protetto, quale ha sofferto, quale si è comportata diversamente dalle aspettative?
- Qual è lo scenario ipotetico "peggiore" per questo specifico portafoglio?
- Il reverse stress test: quali condizioni renderebbero il portafoglio incapace di soddisfare un'esigenza di liquidità di €20.000 senza liquidare VWCE in perdita?
- Gli stress test confermano o contraddicono le assunzioni del TPA (es. correlazione negativa DBMFE/VWCE in crisi)?

**Concetti e strumenti da sviluppare:**
- *Historical scenario analysis:* applicazione dei rendimenti storici degli asset proxy ai componenti del portafoglio per i principali eventi di stress
- *Hypothetical scenario analysis:* costruzione di scenari ipotetici calibrati sui sei regimi del FMT — scenari "ibridi" non ancora osservati storicamente (es. stagflazione con tassi reali elevati in Europa)
- *Reverse stress testing:* partire dall'outcome indesiderato (impossibilità di liquidare senza perdita permanente) e identificare a ritroso le condizioni di mercato che lo produrrebbero
- *P&L attribution per scenario:* per ogni scenario, attribuire il rendimento/perdita del portafoglio a ciascuna componente — verifica della "causalità funzionale" del TPA
- *Factor stress:* cosa succede se un singolo fattore si muove in modo estremo (dollaro +20%, tassi +300bp, spread HY +500bp, oro +50%)?

**Scenario library da costruire:**

| # | Scenario | Periodo di riferimento | Regime FMT |
|---|---|---|---|
| S01 | Crisi petrolifera e stagflazione | 1973–1974 | Stagflazione |
| S02 | Crash azionario e recessione | 1973–1975 | Deflazione/Bust |
| S03 | Shock Volcker (rialzo tassi estremo) | 1980–1982 | Stagflazione → Bust |
| S04 | Burst della bolla dot-com | 2000–2002 | Deflazione/Bust |
| S05 | Grande Crisi Finanziaria | 2008–2009 | Deflazione/Bust |
| S06 | Taper Tantrum | 2013 | Transizione ZIRP → Goldilocks |
| S07 | COVID crash e ripresa | 2020 | Bust → ZIRP/QE |
| S08 | Grande Inasprimento | 2022 | Reflazione → Stagflazione |
| S09 | Stagflazione europea ipotetica | Ipotetico | Stagflazione |
| S10 | Crisi del debito sovrano eurozona 2.0 | Ipotetico | Deflazione/Bust |

**Output attesi:**
1. Scheda standardizzata per ogni scenario (rendimento totale, rendimento per componente, drawdown massimo, recovery time, commento funzionale)
2. Heat map degli scenari × componenti (chi protegge dove)
3. Reverse stress test: matrice delle condizioni che violano il vincolo di liquidità
4. Verifica dell'efficacia del TPA: la componente difensiva ha funzionato come atteso in ogni scenario?
5. Ranking degli scenari per impatto sul portafoglio (dal meno al più distruttivo)

**Dipendenze:** Modulo 2, Modulo 3, FMT Sezione 2

---

### Modulo 5 — Liquidity Risk Management

**Obiettivo primario:** Costruire un protocollo operativo per la gestione delle esigenze di liquidità straordinarie, che minimizzi l'impatto sulla strategia di lungo periodo indipendentemente dal momento di mercato in cui si verifica la necessità.

**Il problema da risolvere:** Questo è il modulo più direttamente collegato al rischio primario identificato nell'IPS. Il portafoglio deve poter essere "parzialmente liquidato in qualsiasi momento" — ma non tutte le componenti hanno lo stesso costo di liquidazione, e non tutti i momenti sono equivalenti. Un prelievo di €15.000 durante un regime Goldilocks ha un impatto completamente diverso da un prelievo identico durante un regime di Deflazione/Bust. Il modulo deve trasformare questo vincolo qualitativo in un protocollo operativo preciso.

**Domande operative:**
- Quale sequenza di liquidazione minimizza l'impatto permanente sulla strategia di lungo periodo (liquidation waterfall)?
- Quanto "costa" (in termini di obiettivo di capitale 2040-2043) liquidare €X in un momento di drawdown del 20%? Del 30%?
- Esiste un livello di prelievo straordinario che può essere sempre soddisfatto senza mai toccare VWCE?
- Come si modificano le risposte precedenti al variare del momento nel ciclo di accumulo (liquidare nel 2027 vs nel 2038 ha impatti molto diversi per il compounding)?
- Qual è il tempo massimo di liquidazione per ciascuna componente? Il vincolo dei 5 giorni lavorativi dell'IPS è rispettato da tutti gli strumenti?

**Concetti e strumenti da sviluppare:**
- *Liquidation waterfall:* ordine ottimale di liquidazione delle componenti, basato su (a) impatto sulla funzione di risk mitigation; (b) capital gain incorporato (costo fiscale); (c) recovery potential (non liquidare ciò che sta per rimbalzare)
- *Liquidation cost matrix:* per ogni combinazione di importo × scenario di mercato × momento del ciclo di accumulo, stima dell'impatto sul portafoglio atteso al 2040-2043
- *Bid-ask spread e market impact:* verifica della liquidità effettiva di ciascun ETF (volume medio giornaliero, spread denaro-lettera, profondità del book) — il vincolo dei 5 giorni dell'IPS è plausibile ma va verificato su strumenti meno liquidi come DBMFE
- *Cash flow buffer sizing:* dimensionamento del buffer ottimale da mantenere nei due conti correnti esterni per assorbire esigenze straordinarie senza ricorrere al portafoglio — collegamento con i €12.000 descritti nell'IPS Sezione 2.2
- *Opportunity cost analysis:* confronto tra il costo di tenere un buffer di liquidità nei conti correnti (rendimento zero o basso) vs. il costo di liquidare il portafoglio in un momento sfavorevole

**Output attesi:**
1. Liquidation waterfall ufficiale: ordine di liquidazione raccomandato con motivazione per ogni step
2. Liquidation cost matrix: tabella importo × scenario → impatto sull'obiettivo 2040-2043
3. Verifica della liquidità effettiva di ciascun ETF (ADV, spread, T+2 garantito)
4. Cash flow buffer sizing: stima dell'importo ottimale da mantenere nei conti correnti per coprire 3/6/12 mesi di esigenze straordinarie potenziali
5. Protocollo operativo di liquidazione in 5 punti (cosa fare quando si ha bisogno di liquidare)

**Dipendenze:** Modulo 3, Modulo 4, IPS Sezioni 2.2, 4.1

---

### Modulo 6 — KRI e Risk Dashboard

**Obiettivo primario:** Costruire un sistema di Key Risk Indicators (KRI) che monitori in modo continuo il profilo di rischio del portafoglio, generi alert precoce prima che le soglie critiche vengano raggiunte e si raccordi con il CRS del FMT in un unico sistema integrato di sorveglianza.

**Il problema da risolvere:** Il FMT monitora il regime macroeconomico esterno al portafoglio. Il RMF deve monitorare il rischio interno al portafoglio. Questi due livelli di sorveglianza devono essere integrati: un deterioramento del CRS del FMT dovrebbe automaticamente alzare l'attenzione sui KRI del RMF, e un deterioramento dei KRI del RMF dovrebbe retroalimentare la lettura di regime del FMT.

**Domande operative:**
- Quali indicatori segnalano con anticipo un deterioramento del profilo di rischio del portafoglio?
- Come si raccordano i KRI del RMF con il CRS del FMT (evitare ridondanza e garantire coerenza)?
- Con quale frequenza monitorare ogni KRI?
- Quali soglie definiscono i tre semafori (verde/giallo/rosso) per ogni KRI?
- Cosa deve fare il Sottoscrittore quando uno o più KRI entrano in zona rossa?

**KRI candidati da valutare:**

| KRI | Frequenza | Soglia allerta | Soglia critica | Collegamento FMT |
|---|---|---|---|---|
| Drawdown corrente | Mensile | –15% | –25% | RiskScore < 0.40 |
| Volatilità realizzata 30gg (annualizzata) | Mensile | +30% vs. target | +50% vs. target | VIX rank > 0.70 |
| Contributo di rischio di VWCE | Trimestrale | > 80% CPV | > 85% CPV | GrowthScore < 0.40 |
| Correlazione DBMFE / VWCE (rolling 6m) | Trimestrale | > +0.20 | > +0.35 | RiskScore < 0.40 |
| Deviazione dall'allocazione target | Mensile | > 3% su singola componente | > 5% | — |
| Tracking difference vs. atteso (ETF) | Annuale | > +0.30% vs. storico | > +0.50% | — |
| Sharpe ratio rolling 12 mesi | Trimestrale | < 0.20 | < 0 | GrowthScore |
| Ulcer Index | Trimestrale | > soglia storica 75° percentile | > 90° percentile | RiskScore |
| Progresso vs. obiettivo 2040-2043 | Annuale | –15% vs. proiezione | –25% vs. proiezione | — |
| Liquidità buffer (conti correnti) | Mensile | < 3 mesi di spesa | < 1 mese | — |

**Output attesi:**
1. KRI set definitivo (8-12 indicatori) con formula di calcolo, fonte dati, frequenza e soglie semaforo
2. Template di risk dashboard mensile (1 pagina) e trimestrale (2-3 pagine)
3. Protocollo di escalation: matrice "n KRI in zona rossa → azione X"
4. Schema di integrazione KRI/CRS: come i due sistemi si alimentano reciprocamente
5. Collegamento esplicito con i trigger di revisione straordinaria dell'IPS (Sezione 6.7)

**Dipendenze:** Modulo 2, Modulo 3, Modulo 5, FMT Sezione 6, IPS Sezione 6.7

---

### Modulo 7 — Risk Governance

**Obiettivo primario:** Integrare il RMF nell'architettura di governance dell'IPS, definendo responsabilità, frequenze di monitoraggio, documentazione e collegamento con le procedure di revisione già previste.

**Contenuto da definire:**

**7.1 Frequenza di monitoraggio per KRI**

| Frequenza | Attività |
|---|---|
| Mensile | Calcolo drawdown corrente, verifica liquidità buffer, deviazione dall'allocazione target |
| Trimestrale | Aggiornamento risk dashboard completo, verifica KRI, calcolo CPV per componente |
| Annuale | Revisione stress test library, calibrazione soglie KRI, confronto ERC vs. allocazione corrente, integrazione con revisione IPS |
| Straordinaria | Attivata da: 3+ KRI in zona rossa, drawdown > 25%, variazione CRS > 0.15 in 4 settimane, evento di stress sistemico |

**7.2 Integrazione con la revisione annuale dell'IPS**

La revisione annuale dell'IPS (Sezione 6.4) deve includere una sezione di risk review con agenda minima:
1. Lettura dei KRI dell'anno precedente: quante volte in zona gialla? Quante in zona rossa?
2. Verifica delle correlazioni realizzate vs. attese (Modulo 2)
3. Aggiornamento dello stress test più rilevante per il regime attuale (Modulo 4)
4. Verifica della liquidation waterfall: è ancora ottimale? Il cash flow buffer è adeguato? (Modulo 5)
5. Ricalibrazione delle soglie KRI se i parametri di mercato sono cambiati significativamente

**7.3 Registro delle valutazioni di rischio**

Distinto dal registro delle decisioni dell'IPS, il Risk Register documenta:
- Data della valutazione
- Valori dei KRI e classificazione semaforo
- Eventuali KRI in zona gialla o rossa con commento
- Azioni intraprese o pianificate
- Lettura del regime FMT corrente (collegamento)

**Output attesi:**
1. Calendario di risk monitoring integrato con l'agenda dell'IPS
2. Template del Risk Register (format di compilazione)
3. Matrice di escalation definitiva (chi fa cosa quando un KRI scatta)
4. Agenda di risk review per la revisione annuale dell'IPS

**Dipendenze:** tutti i moduli precedenti, IPS Sezione 6

---

## Sezione 2 — Sequenza di sviluppo e dipendenze

### 2.1 Diagramma delle dipendenze

```
Modulo 1: Risk Budget          ← PUNTO DI PARTENZA (nessuna dipendenza interna)
    │
    ├──► Modulo 2: Risk Decomposition
    │         │
    │         └──► Modulo 3: Drawdown Management
    │                   │
    │                   └──► Modulo 4: Stress Testing
    │                               │
    │                               └──► Modulo 5: Liquidity Risk
    │                                         │
    └─────────────────────────────────────────┴──► Modulo 6: KRI Dashboard
                                                         │
                                                         └──► Modulo 7: Risk Governance
```

### 2.2 Fasi di sviluppo

**Fase 1 — Fondamenta (Modulo 1)**
*Prerequisito per tutto il resto. Deve produrre numeri concreti: il volatility target e il drawdown limit che guidano tutti i moduli successivi.*

**Fase 2 — Analisi del rischio strutturale (Moduli 2 e 3)**
*Fotografia del rischio come "sta" oggi. I Moduli 2 e 3 possono essere sviluppati in parallelo una volta completato il Modulo 1.*

**Fase 3 — Test di robustezza (Modulo 4)**
*Verifica che la struttura tenga sotto stress. Richiede la matrice di covarianza del Modulo 2 e il framework di drawdown del Modulo 3.*

**Fase 4 — Operatività (Moduli 5 e 6)**
*Traduzione del framework analitico in strumenti operativi quotidiani. Il Modulo 5 richiede il Modulo 4; il Modulo 6 richiede tutti i precedenti.*

**Fase 5 — Governance (Modulo 7)**
*Integrazione nell'architettura documentale. Non può essere sviluppato senza avere definito cosa monitorare (Modulo 6).*

---

## Sezione 3 — Output finale del RMF

Al termine dello sviluppo di tutti i moduli, il RMF produrrà cinque documenti/strumenti operativi:

### Documento A — Risk Policy Statement
Equivalente "risk-side" dell'IPS. Formalizza in 2-3 pagine:
- Il risk appetite statement quantitativo (volatility target, drawdown limit, livelli di allerta)
- Il risk budget per componente
- Le soglie di intervento e i relativi protocolli

### Documento B — Risk Dashboard
Template di monitoraggio in due versioni:
- *Mensile (1 pagina):* drawdown corrente, allocazione vs. target, liquidità buffer, semaforo KRI sintetico
- *Trimestrale (3-4 pagine):* KRI completo, CPV per componente, correlazioni rolling, progresso vs. obiettivo

### Documento C — Stress Test Library
Collezione aggiornabile di scenari calibrati:
- 10 scenari storici (S01–S10 come da tabella Modulo 4)
- 6 scenari per regime FMT
- 1 reverse stress test aggiornato annualmente
- Formato standardizzato per facilitare l'aggiornamento e il confronto nel tempo

### Documento D — Liquidity Protocol
Protocollo operativo di liquidazione in 5 punti:
- Liquidation waterfall (ordine di liquidazione ottimale)
- Calcolo del costo di liquidazione per scenario
- Regole per il cash flow buffer esterno

### Documento E — Risk Register
Registro storico delle valutazioni di rischio, formato tabellare, da compilare a ogni monitoraggio periodico e ad ogni evento straordinario.

---

## Sezione 4 — Integrazione con IPS e FMT

### 4.1 Punti di raccordo con l'IPS

| Sezione IPS | Collegamento RMF |
|---|---|
| 2.5 — Profilo di rischio | Modulo 1: Risk Budget (traduzione quantitativa del vincolo di liquidità) |
| 3.5 — Orizzonte di valutazione | Modulo 3: Drawdown Management (recovery time analysis) |
| 4.1 — Vincolo di liquidità | Modulo 5: Liquidity Risk (verifica operativa del vincolo) |
| 5.8 — Bande di tolleranza | Modulo 6: KRI (deviazione dall'allocazione come KRI) |
| 6.7 — Trigger revisione straordinaria | Modulo 6: KRI → drawdown > 30% come KRI critico |
| 7.7 — Guardrail comportamentali | Modulo 7: Risk Governance (guardrail specifici per il risk monitoring) |

### 4.2 Punti di raccordo con il FMT

| Sezione FMT | Collegamento RMF |
|---|---|
| 2.2 — CRS | Modulo 6: integrazione CRS/KRI in sistema unico |
| 2.4 — Identificazione del regime | Modulo 2: correlazioni per regime (input al FMT) |
| 3.x — Tilt per regime | Modulo 4: stress test per regime (verifica dell'efficacia dei tilt) |
| 4.4 — Soglie di azione | Modulo 6: KRI come input aggiuntivo alle soglie di azione del FMT |

### 4.3 Schema di interazione operativa settimanale/mensile

```
OGNI SETTIMANA:
  FMT → Aggiornamento CRS
    │
    └── Se CRS attraversa soglia critica → Attivazione KRI di allerta RMF

OGNI MESE:
  RMF → Calcolo KRI mensili (drawdown, liquidità, allocazione)
    │
    └── Se KRI in zona gialla → Nota nel Risk Register
    └── Se KRI in zona rossa → Attivazione protocollo escalation
                                  └── Se 3+ KRI rossi → Revisione straordinaria IPS

OGNI TRIMESTRE:
  RMF → Dashboard trimestrale completo
    │
    └── Lettura combinata KRI + CRS → Posizione integrata di rischio

OGNI ANNO:
  IPS → Revisione annuale
    │
    ├── FMT → Review qualità delle letture di regime
    └── RMF → Risk review: KRI, stress test, liquidation waterfall
```

---

## Sezione 5 — Note metodologiche e vincoli

### 5.1 Fonti dati

Il RMF è progettato per essere implementabile con strumenti gratuiti o a costo contenuto, coerentemente con lo stack tecnologico del FMT:

| Dato | Fonte | Utilizzo nel RMF |
|---|---|---|
| Rendimenti storici ETF | Yahoo Finance / yfinance | Moduli 2, 3, 4 |
| Rendimenti proxy asset class (pre-ETF) | Kenneth French Data Library, AQR | Moduli 3, 4 |
| Serie fattoriali Fama-French | Kenneth French Data Library | Modulo 2 |
| Dati macro (Treasury yields, spread) | FRED | Moduli 4, 6 |
| Informazioni su bid-ask e ADV ETF | ETF.com / JustETF | Modulo 5 |
| NAV storici ETF (per tracking difference) | KIID emittenti, ETF.com | Modulo 6 (KRI costi) |

### 5.2 Proxy storici per ETF non esistenti

Alcuni ETF del portafoglio (DBMFE, CRRY) hanno storie limitate. Per i moduli che richiedono serie storiche lunghe (Moduli 3 e 4 in particolare) è necessario identificare proxy plausibili:

- *DBMFE (Managed Futures):* indice SG Trend Index, serie storiche di fondi Winton/Man AHL, o benchmark pubblici AQR Managed Futures
- *CRRY (Carry):* indice Deutsche Bank Currency Carry, serie AQR Carry
- *ZPRV/ZPRX (Small Cap Value):* Kenneth French Small Value portfolio USA/Europe
- *VWCE:* MSCI World / MSCI ACWI Total Return

La scelta dei proxy è una decisione metodologica rilevante che deve essere documentata e giustificata.

### 5.3 Limiti riconosciuti

1. **Instabilità delle correlazioni:** Le correlazioni storiche sono instabili e cambiano per regime. Il RMF utilizza correlazioni condizionate per regime, ma non può prevedere correlazioni future con precisione. Lo stress test sulla correlazione (scenario "tutte le correlazioni a 1") è il principale guardrail.

2. **Lunghezza limitata dei dati per alcuni ETF:** Proxy storici introducono basis risk. I risultati dei Moduli 3 e 4 sono indicazioni di ordine di grandezza, non previsioni precise.

3. **Il RMF non è un sistema di market timing:** Come il FMT, il RMF è uno strumento di organizzazione dell'incertezza, non di previsione. I KRI e gli stress test migliorano il processo decisionale ma non eliminano l'incertezza sui risultati futuri.

---

## Sezione 6 — Checklist di completamento

*Da spuntare man mano che ogni modulo viene sviluppato.*

### Modulo 1 — Risk Budget
- [ ] Risk Appetite Statement redatto e approvato
- [ ] Volatility target definito (numero specifico)
- [ ] Drawdown limit definito con i tre livelli di allerta
- [ ] Tabella risk budget per componente (peso nominale vs. CPV)
- [ ] Confronto ERC vs. allocazione strategica corrente

### Modulo 2 — Risk Decomposition
- [ ] Matrice di correlazione storica calcolata (3, 5, 10 anni)
- [ ] Matrici di correlazione per regime (6 regimi FMT)
- [ ] Factor exposure analysis completata
- [ ] Diversification ratio calcolato
- [ ] Analisi correlation stress completata

### Modulo 3 — Drawdown Management
- [ ] Distribuzione del drawdown simulata per orizzonte temporale
- [ ] Underwater chart prodotta
- [ ] Recovery analysis completata per drawdown 20% e 30%
- [ ] "Punto critico di liquidità" calcolato
- [ ] Confronto vs. benchmark 60/40 e VWCE 100%

### Modulo 4 — Stress Testing
- [ ] Scenari storici S01–S10 calibrati e documentati
- [ ] Scenari per regime FMT sviluppati (6 scenari)
- [ ] Reverse stress test completato
- [ ] Heat map scenari × componenti prodotta
- [ ] Verifica efficacia TPA per ogni scenario

### Modulo 5 — Liquidity Risk
- [ ] Liquidation waterfall definita e motivata
- [ ] Liquidation cost matrix calcolata
- [ ] Verifica liquidità effettiva ETF (ADV, spread)
- [ ] Cash flow buffer sizing completato
- [ ] Protocollo operativo di liquidazione in 5 punti

### Modulo 6 — KRI Dashboard
- [ ] KRI set definitivo (8-12 indicatori) con formule e soglie
- [ ] Template dashboard mensile
- [ ] Template dashboard trimestrale
- [ ] Matrice di escalation
- [ ] Schema di integrazione KRI/CRS

### Modulo 7 — Risk Governance
- [ ] Calendario di risk monitoring
- [ ] Template Risk Register
- [ ] Matrice di escalation definitiva
- [ ] Agenda risk review per revisione annuale IPS

### Documenti finali
- [ ] Documento A — Risk Policy Statement
- [ ] Documento B — Risk Dashboard (template mensile + trimestrale)
- [ ] Documento C — Stress Test Library
- [ ] Documento D — Liquidity Protocol
- [ ] Documento E — Risk Register (template)

---

## Sezione 7 — Storico delle revisioni

| Versione | Data | Natura della modifica |
|---|---|---|
| 0.1 | 2025 | Prima stesura del piano di sviluppo |
| | | |
| | | |
