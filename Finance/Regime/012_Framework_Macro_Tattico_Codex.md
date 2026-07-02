---
type: 'Page'
title: Framework Macro Tattico
aliases:
  - FMT
  - Framework di Allocazione Tattica basata su Regimi
description: Documento operativo per disciplinare tilt tattici di portafoglio in funzione del regime macroeconomico, entro le bande definite dall'IPS.
icon: null
createdAt: '2026-05-29'
lastUpdated: '2026-05-29'
tags:
  - IPS
  - asset-allocation
  - macro-regimi
  - tactical-allocation
coverImage: null
---

# Framework Macro Tattico

*Documento operativo di allocazione tattica basata su regimi macroeconomici*

---

|                        |                                |
| :--------------------- | :----------------------------- |
| **Versione**           | 1.0                            |
| **Data di redazione**  | 2026                           |
| **Documento superiore**| Investment Policy Statement    |
| **Ambito**             | Tilt tattici entro bande IPS   |
| **Prossima revisione** | I trimestre 2027               |

> *Il presente documento integra l'Investment Policy Statement e disciplina esclusivamente le inclinazioni tattiche del portafoglio in funzione del regime macroeconomico corrente. Non sostituisce l'IPS, non modifica la strategia di lungo periodo e non autorizza strumenti, rischi o pesi non già previsti dall'IPS.*

---

## Sezione 1 - Scopo del Framework Macro Tattico

Il **Framework Macro Tattico** (di seguito "FMT") definisce il processo con cui il Sottoscrittore può applicare limitate inclinazioni tattiche rispetto ai pesi strategici del portafoglio in funzione del regime macroeconomico prevalente.

L'obiettivo del FMT non è prevedere i mercati, massimizzare il rendimento di breve periodo o effettuare market timing. L'obiettivo è rendere il portafoglio più robusto rispetto ai principali ambienti macroeconomici che possono manifestarsi lungo l'orizzonte di investimento: espansione ordinata, reflazione, surriscaldamento, stagflazione e recessione/deflazione.

Il FMT traduce in regole operative tre documenti del progetto:

- l'**Investment Policy Statement**, che definisce obiettivi, vincoli, pesi strategici e bande di tolleranza;
- il documento sui **Regimi macroeconomici e mercati finanziari**, che descrive la tassonomia dei regimi e il comportamento atteso delle asset class;
- il **Framework Regime Detection**, che definisce indicatori, sub-indici e Composite Regime Score (CRS) per riconoscere il regime corrente.

Il principio guida è semplice: il portafoglio strategico resta la posizione naturale; il tilt tattico è ammesso solo quando l'evidenza di regime è sufficientemente chiara, stabile e documentata.

---

## Sezione 2 - Gerarchia delle regole

**2.1 Prevalenza dell'IPS.** In caso di conflitto tra il presente documento e l'IPS, prevale sempre l'IPS. Il FMT opera esclusivamente all'interno delle bande di tolleranza definite alla Sezione 5.8 dell'IPS.

**2.2 Nessuna nuova asset class.** Il FMT non autorizza l'introduzione di strumenti non ammessi dall'IPS. Ogni tilt tattico deve essere implementato usando gli strumenti già previsti o strumenti equivalenti ammessi dalle Sezioni 4 e 5 dell'IPS.

**2.3 Default strategico.** In assenza di segnali chiari, in presenza di dati contraddittori o quando la convinzione sul regime è bassa, il portafoglio torna automaticamente ai pesi strategici.

**2.4 Priorità comportamentale.** Il FMT è una regola di processo prima ancora che una regola di allocazione. Serve a ridurre decisioni impulsive durante fasi di volatilità, non ad aumentare la frequenza delle operazioni.

**2.5 Documentazione.** Ogni attivazione, modifica o disattivazione di tilt tattici deve essere documentata nel registro delle decisioni dell'IPS, indicando: data, regime identificato, segnali utilizzati, livello di convinzione, tilt applicato, strumenti interessati e data prevista di revisione.

---

## Sezione 3 - Allocazione strategica di partenza

Il FMT parte sempre dalla Strategic Asset Allocation definita dall'IPS.

| Ruolo | Strumento | Peso strategico | Banda IPS |
| :--- | :--- | ---: | ---: |
| Loss Mitigation + Equity Diversifier | DBMFE - Managed Futures / Trend Following | 15% | 10%-20% |
| Loss Mitigation + Equity Diversifier | CRRY - Carry / premi di rischio alternativi | 5% | n.d. |
| Loss Mitigation | GOLD - Oro ETF | 5% | 3%-8% |
| Loss Mitigation | BOND - Governativi EUR / ladder 1-5 anni | 10% | 7%-15% |
| Equity Complement | ZPRV/ZPRX - Small Cap Value | 10% | 5%-15% |
| Equity Substitute | VWCE o equivalente globale | 55% | 45%-65% |
| **Totale** | | **100%** | |

La componente difensiva complessiva, composta da DBMFE, CRRY, GOLD e BOND, deve rimanere tra **30% e 40%** del portafoglio. La componente azionaria complessiva, composta da Equity Complement ed Equity Substitute, si muove di conseguenza tra **60% e 70%**.

---

## Sezione 4 - Regime detection: input del FMT

Il FMT utilizza i segnali definiti nel Framework Regime Detection. Il sistema non assegna il regime sulla base di una singola previsione macroeconomica, ma attraverso la combinazione di sub-indici normalizzati.

### 4.1 Sub-indici principali

| Sub-indice | Cosa misura | Lettura sintetica |
| :--- | :--- | :--- |
| **GrowthScore** | Forza del ciclo reale | Alto = espansione; basso = rallentamento/recessione |
| **InflationScore** | Pressione inflazionistica e asset reali | Alto = inflazione/reflazione; basso = disinflazione/deflazione |
| **RiskScore** | Propensione al rischio e condizioni finanziarie | Alto = risk-on; basso = stress/risk-off |
| **MonetaryScore** | Orientamento della politica monetaria e liquidità | Alto = condizioni accomodanti; basso = condizioni restrittive |
| **CRS** | Sintesi aggregata del ciclo | 0 = stress/recessione; 1 = surriscaldamento/risk-on estremo |

### 4.2 Regola di classificazione

Un regime è considerato operativo solo se soddisfa tutte le condizioni seguenti:

- la mappatura dei sub-indici è coerente con il regime per almeno **4 settimane consecutive**;
- almeno **3 sub-indici su 4** confermano la lettura del regime;
- il movimento del CRS è coerente con la narrativa del regime, oppure il CRS è stabile dentro la fascia tipica del regime;
- non esiste un evento personale o di liquidità familiare che renda inopportuno assumere rischio tattico.

Se una di queste condizioni manca, il regime viene classificato come **incerto** e il portafoglio resta o torna ai pesi strategici.

### 4.3 Livello di convinzione

Il FMT usa tre livelli di convinzione.

| Livello | Condizioni | Azione consentita |
| :--- | :--- | :--- |
| **Bassa** | Segnali misti, durata inferiore a 4 settimane, sub-indici divergenti | Nessun tilt; pesi strategici |
| **Media** | 3 sub-indici coerenti, CRS stabile, regime plausibile ma non pienamente confermato | Mezzo tilt verso il target di regime |
| **Alta** | 4 sub-indici coerenti o forte conferma cross-asset, regime stabile, narrativa macro chiara | Tilt pieno verso il target di regime |

Il mezzo tilt è calcolato come punto intermedio tra peso strategico e peso tattico di regime. Esempio: se DBMFE ha peso strategico 15% e target di regime 20%, il mezzo tilt è 17,5%.

---

## Sezione 5 - Regimi operativi

Il FMT riduce la complessità dei regimi macroeconomici a cinque stati operativi. Gli stati non sono etichette narrative: sono condizioni di portafoglio, ciascuna associata a un comportamento atteso delle asset class e a un set di tilt predefiniti.

### 5.1 Espansione ordinata / Goldilocks

**Descrizione.** Crescita positiva, inflazione stabile o in calo, condizioni finanziarie favorevoli, volatilità contenuta. È il regime più favorevole agli asset rischiosi, in particolare azionario globale e fattori equity.

**Segnali tipici.**

- GrowthScore sopra 0,60.
- InflationScore tra 0,30 e 0,55.
- RiskScore sopra 0,65.
- MonetaryScore sopra 0,55.
- CRS tipicamente tra 0,55 e 0,70.

**Implicazione di portafoglio.** Ridurre al minimo ammesso la componente difensiva complessiva e aumentare moderatamente l'esposizione azionaria, senza eliminare gli strumenti di protezione.

### 5.2 Reflazione

**Descrizione.** Crescita in accelerazione e inflazione in aumento, spesso nelle fasi iniziali o intermedie di ripresa. Tendono a funzionare meglio asset ciclici, value, commodity e strategie legate a trend macro.

**Segnali tipici.**

- GrowthScore sopra 0,55.
- InflationScore sopra 0,60.
- RiskScore sopra 0,55.
- MonetaryScore tra 0,40 e 0,65.
- CRS tipicamente tra 0,65 e 0,82.

**Implicazione di portafoglio.** Mantenere esposizione azionaria elevata, favorire Equity Complement e GOLD, ridurre la componente obbligazionaria più sensibile ai tassi.

### 5.3 Surriscaldamento / Late cycle

**Descrizione.** Inflazione elevata, ciclo maturo, politiche monetarie restrittive o in irrigidimento, rischio crescente di inversione del ciclo. Gli asset rischiosi possono continuare a salire, ma la distribuzione dei risultati diventa asimmetrica.

**Segnali tipici.**

- InflationScore sopra 0,70.
- RiskScore ancora positivo ma in deterioramento.
- MonetaryScore sotto 0,45.
- CRS sopra 0,80 o in rapida accelerazione.
- Divergenze tra equity forte e credito in deterioramento.

**Implicazione di portafoglio.** Aumentare la protezione prima che il regime diventi apertamente recessivo, con priorità a DBMFE e GOLD. Ridurre i fattori equity più ciclici.

### 5.4 Stagflazione

**Descrizione.** Crescita debole o in contrazione con inflazione persistente. È il regime più difficile per i portafogli tradizionali, perché azioni e obbligazioni possono scendere insieme.

**Segnali tipici.**

- GrowthScore sotto 0,45.
- InflationScore sopra 0,65.
- RiskScore sotto 0,40.
- MonetaryScore sotto 0,40.
- Divergenza negativa: GrowthScore in calo e InflationScore in aumento.

**Implicazione di portafoglio.** Massimizzare la robustezza entro le bande IPS: DBMFE al limite alto, GOLD al limite alto, BOND al limite basso compatibile con il vincolo IPS, Equity Complement al limite basso.

### 5.5 Recessione / Deflazione / Bust

**Descrizione.** Crescita in contrazione, inflazione in calo o pressione deflazionistica, stress creditizio, volatilità elevata e riduzione della propensione al rischio. È il regime in cui il rischio di liquidazione forzata è massimo.

**Segnali tipici.**

- GrowthScore sotto 0,30.
- InflationScore sotto 0,35.
- RiskScore sotto 0,25.
- CRS tipicamente tra 0,05 e 0,30.
- Allargamento degli spread creditizi e deterioramento delle condizioni finanziarie.

**Implicazione di portafoglio.** Portare la componente difensiva al massimo ammesso, aumentare DBMFE e BOND, ridurre Equity Complement. Le vendite di equity vanno eseguite solo se necessarie al raggiungimento dei pesi e preferibilmente dopo conferma del regime.

---

## Sezione 6 - Matrice dei pesi tattici

La tabella seguente definisce i target tattici pieni per ciascun regime. Con convinzione media si applica solo metà dello spostamento rispetto ai pesi strategici. Con convinzione bassa non si applica alcun tilt.

| Regime | DBMFE | CRRY | GOLD | BOND | Equity Complement | Equity Substitute | Difensiva totale |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Strategico / Incerto** | 15% | 5% | 5% | 10% | 10% | 55% | 35% |
| **Espansione ordinata** | 12% | 5% | 3% | 10% | 10% | 60% | 30% |
| **Reflazione** | 13% | 7% | 6% | 7% | 12% | 55% | 33% |
| **Surriscaldamento** | 18% | 4% | 8% | 10% | 8% | 52% | 40% |
| **Stagflazione** | 20% | 5% | 8% | 7% | 5% | 55% | 40% |
| **Recessione / Deflazione** | 20% | 3% | 5% | 12% | 5% | 55% | 40% |

### 6.1 Logica dei tilt

**DBMFE.** È lo strumento tattico principale nei regimi di stress, surriscaldamento e recessione. Il peso aumenta quando cresce la probabilità di trend persistenti, crisi di liquidità o rotazioni violente tra asset class.

**CRRY.** È mantenuto più alto nei regimi reflazionistici e risk-on, ma ridotto nei regimi di stress acuto o surriscaldamento, perché le strategie carry possono soffrire durante fasi di deleveraging rapido.

**GOLD.** Sale nei regimi di inflazione persistente, stagflazione e surriscaldamento. Resta presente anche in recessione, ma non viene massimizzato quando il segnale dominante è deflazionistico.

**BOND.** Aumenta nei regimi recessivi/deflazionistici e resta contenuto nei regimi reflazionistici o stagflazionistici, dove il rischio tassi e inflazione può penalizzare le obbligazioni.

**Equity Complement.** Aumenta in reflazione, quando small value e ciclici tendono a beneficiare della ripresa nominale. Si riduce in recessione, stagflazione e surriscaldamento, dove il fattore small/value può amplificare il rischio.

**Equity Substitute.** È il motore strutturale del rendimento e non viene azzerato in nessun regime. Il FMT può modularlo, ma la permanenza dell'esposizione azionaria globale è coerente con l'orizzonte di lungo periodo dell'IPS.

---

## Sezione 7 - Regole di attivazione e disattivazione

**7.1 Finestra di osservazione.** Il regime viene valutato settimanalmente tramite il sistema di regime detection, ma le decisioni di allocazione sono prese al massimo con cadenza mensile, salvo transizioni di stress eccezionale.

**7.2 Conferma minima.** Un nuovo regime richiede almeno 4 settimane di conferma prima di attivare un tilt. La conferma può essere abbreviata a 2 settimane solo in presenza di stress sistemico evidente: forte allargamento degli spread, VIX sopra soglie di crisi, crollo del RiskScore e deterioramento simultaneo del GrowthScore.

**7.3 Una sola direzione alla volta.** Il portafoglio non può passare direttamente da un tilt pieno di espansione a un tilt pieno di recessione nella stessa finestra decisionale. In caso di transizione rapida, il primo passo è tornare ai pesi strategici; il tilt del nuovo regime viene applicato solo dopo conferma.

**7.4 Cooling-off.** Ogni modifica tattica che richiede vendite deve essere annotata nel registro delle decisioni e confermata dopo almeno 48 ore, in coerenza con il processo decisionale dell'IPS. Gli acquisti tramite versamenti periodici possono essere orientati immediatamente verso i pesi target tattici, purché il regime sia già confermato.

**7.5 Disattivazione.** Un tilt tattico viene disattivato quando:

- il regime perde conferma per 4 settimane consecutive;
- il CRS attraversa una soglia critica in direzione opposta;
- meno di 3 sub-indici su 4 confermano il regime;
- emerge un'esigenza familiare di liquidità che rende preferibile ridurre complessità e turnover;
- il Sottoscrittore non è in grado di documentare razionalmente la motivazione del tilt.

---

## Sezione 8 - Modalità di esecuzione

**8.1 Priorità ai versamenti.** Il primo strumento di implementazione dei tilt tattici sono i versamenti mensili. Prima di vendere strumenti in portafoglio, i nuovi acquisti vengono indirizzati verso le componenti sottopesate rispetto al target tattico.

**8.2 Vendite limitate.** Le vendite sono ammesse solo quando il tilt non può essere raggiunto con versamenti entro un tempo ragionevole o quando una componente supera la propria banda IPS. In ogni caso si tiene conto dell'impatto fiscale e della regola di rotazione delle tranche prevista dall'IPS.

**8.3 Dimensione minima dell'intervento.** Non si effettuano operazioni tattiche per correggere scostamenti inferiori a 1 punto percentuale del portafoglio complessivo. Scostamenti piccoli vengono lasciati assorbire dai versamenti successivi.

**8.4 Frequenza massima.** Il FMT non deve generare più di una modifica tattica completa per trimestre, salvo rientro ai pesi strategici per perdita di convinzione. La regola esiste per evitare che il sistema di regime detection diventi una fonte di trading eccessivo.

**8.5 Ordine operativo.** Quando viene attivato un tilt, l'esecuzione segue questo ordine:

1. calcolo dei pesi effettivi correnti;
2. confronto con il target tattico di regime;
3. definizione degli acquisti tramite versamenti disponibili;
4. valutazione dell'eventuale necessità di vendite;
5. stima dell'impatto fiscale;
6. annotazione nel registro delle decisioni;
7. attesa di 48 ore se sono previste vendite;
8. esecuzione e archiviazione del nuovo asset mix.

---

## Sezione 9 - Controlli di rischio

**9.1 Limite di turnover.** Il turnover generato dal FMT non dovrebbe superare il 20% del valore del portafoglio su base annua, salvo ribilanciamento straordinario imposto dalle bande IPS.

**9.2 Nessuna leva.** Il FMT non autorizza leva finanziaria, derivati direzionali, ETF a leva, ETF inversi o strumenti non previsti dall'IPS.

**9.3 Nessun segnale singolo.** Nessuna operazione tattica può essere basata su un singolo dato macroeconomico, un singolo grafico, una previsione di mercato o una narrativa mediatica.

**9.4 No stop-loss di regime.** Un tilt tattico non viene chiuso perché ha prodotto una perdita di breve periodo. Viene chiuso solo se il regime che lo giustificava non è più confermato.

**9.5 Rischio personale prima del rischio di mercato.** Se aumenta la probabilità di prelievi straordinari familiari, il FMT viene sospeso e il portafoglio torna alla configurazione più semplice compatibile con l'IPS.

**9.6 Review obbligatoria.** Se il FMT produce sottoperformance rispetto ai pesi strategici per più di 300 punti base su una finestra rolling di 12 mesi, non viene automaticamente abbandonato, ma attiva una revisione formale del processo: qualità dei segnali, costi, timing, disciplina esecutiva e coerenza con l'IPS.

---

## Sezione 10 - Procedura mensile di regime allocation

La procedura ordinaria viene eseguita una volta al mese, preferibilmente nella prima settimana del mese dopo la pubblicazione dei principali dati macro.

### 10.1 Checklist

| Passo | Domanda | Output |
| :--- | :--- | :--- |
| 1 | Quali sono GrowthScore, InflationScore, RiskScore, MonetaryScore e CRS? | Tabella dei valori |
| 2 | Quale regime risulta dalla mappatura dei sub-indici? | Regime candidato |
| 3 | Il regime è confermato da almeno 4 settimane? | Sì / No |
| 4 | Quanti sub-indici confermano il regime? | 0-4 |
| 5 | Il CRS ha momentum coerente? | Delta 4w, 8w, 13w |
| 6 | La convinzione è bassa, media o alta? | Livello di convinzione |
| 7 | Quale target tattico corrisponde al regime? | Peso target |
| 8 | Gli scostamenti sono abbastanza grandi da operare? | Operare / attendere |
| 9 | L'operazione può essere fatta con i versamenti? | Piano acquisti |
| 10 | Serve una vendita con impatto fiscale? | Piano vendite o rinvio |

### 10.2 Template di decisione

Ogni decisione tattica deve essere registrata in forma sintetica usando il seguente schema.

```text
Data:
Valore portafoglio:
Regime candidato:
Regime precedente:
GrowthScore:
InflationScore:
RiskScore:
MonetaryScore:
CRS:
Delta CRS 4w / 8w / 13w:
Sub-indici coerenti:
Livello di convinzione:
Target tattico applicato:
Operazioni previste:
Fonte dei fondi: versamenti / vendite / entrambe
Impatto fiscale stimato:
Motivazione:
Data di conferma dopo cooling-off:
Data prossima revisione:
```

---

## Sezione 11 - Esempi applicativi

### 11.1 Segnale di reflazione con convinzione alta

Il GrowthScore sale sopra 0,60, l'InflationScore supera 0,65, il RiskScore resta sopra 0,60 e il CRS attraversa 0,65 con momentum positivo per 4 settimane. Il regime operativo è Reflazione.

Il target pieno diventa: DBMFE 13%, CRRY 7%, GOLD 6%, BOND 7%, Equity Complement 12%, Equity Substitute 55%. I versamenti mensili vengono indirizzati prioritariamente verso CRRY, GOLD ed Equity Complement, evitando vendite se gli scostamenti sono modesti.

### 11.2 Segnale di stagflazione con convinzione media

Il GrowthScore scende sotto 0,45 mentre l'InflationScore resta sopra 0,65. RiskScore e MonetaryScore peggiorano, ma non tutti i segnali cross-asset confermano. La convinzione è media.

Si applica metà tilt tra strategico e Stagflazione. Per DBMFE il peso target operativo diventa 17,5% invece di 20%; GOLD diventa 6,5% invece di 8%; Equity Complement diventa 7,5% invece di 5%. Il portafoglio non si sposta immediatamente al massimo difensivo.

### 11.3 Segnale contraddittorio

Il CRS è in area Goldilocks, ma gli spread creditizi si stanno allargando e il RiskScore cala rapidamente. GrowthScore resta positivo, InflationScore è neutrale. Il regime non è sufficientemente chiaro.

Nessun tilt viene attivato. Il portafoglio resta ai pesi strategici e il mese successivo viene aggiornata la valutazione. Il FMT considera l'assenza di operazione una decisione valida.

---

## Sezione 12 - Criteri di revisione del FMT

Il FMT è rivisto almeno una volta l'anno insieme all'IPS. Una revisione straordinaria è attivata se si verifica uno dei seguenti eventi:

- modifica delle bande di tolleranza dell'IPS;
- introduzione o rimozione di strumenti strategici dal portafoglio;
- deterioramento significativo della qualità o disponibilità dei dati usati dal Framework Regime Detection;
- sottoperformance del FMT superiore a 300 punti base rispetto alla configurazione strategica su 12 mesi;
- più di due falsi segnali consecutivi che generano turnover non compensato da miglioramento della robustezza;
- cambiamento significativo della situazione familiare, reddituale o di liquidità.

La revisione annuale deve rispondere a quattro domande:

1. Il FMT ha ridotto il rischio nei regimi avversi?
2. Il FMT ha aumentato eccessivamente turnover, fiscalità o complessità?
3. I segnali di regime sono stati documentati in modo coerente?
4. Il Sottoscrittore ha rispettato la disciplina del processo, inclusi default strategico e cooling-off?

---

## Sezione 13 - Sintesi operativa

Il Framework Macro Tattico può essere riassunto in cinque regole.

1. **Il portafoglio strategico è il default.** Il tilt è l'eccezione disciplinata.
2. **Il regime deve essere confermato.** Nessun singolo dato giustifica una modifica.
3. **Le bande IPS sono inviolabili.** Il FMT modula il portafoglio, non lo reinventa.
4. **I versamenti vengono prima delle vendite.** La fiscalità e il turnover sono parte del rendimento.
5. **La robustezza conta più dell'alpha.** Il successo del FMT si misura nella qualità del comportamento durante i cambi di regime, non nella precisione di ogni singolo segnale.

Il FMT non pretende di sapere quale regime verrà dopo. Serve a fare una cosa più realistica e più utile: preparare in anticipo il portafoglio e il processo decisionale a scenari diversi, evitando che le decisioni più importanti vengano prese nel momento emotivamente peggiore.

---

## Appendice A - Bande IPS richiamate dal FMT

| Componente | Banda minima | Peso strategico | Banda massima |
| :--- | ---: | ---: | ---: |
| Componente difensiva totale | 30% | 35% | 40% |
| DBMFE | 10% | 15% | 20% |
| GOLD | 3% | 5% | 8% |
| BOND | 7% | 10% | 15% |
| Equity Complement totale | 5% | 10% | 15% |
| Equity Substitute | 45% | 55% | 65% |

---

## Appendice B - Storico delle revisioni

| Versione | Data | Natura della modifica | Firmato |
| :--- | :--- | :--- | :--- |
| 1.0 | 2026 | Prima stesura del Framework Macro Tattico | |

