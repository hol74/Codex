# Piano Macro-Regime Engine

## Obiettivo

Costruire un Macro-Regime Engine professionale per supportare la strategia di portafoglio personale. Il motore non deve essere un singolo modello predittivo, ma una pipeline governata, auditabile ed estendibile che separa dati, feature, classificazione del regime, proposta allocativa, controlli di rischio e decisione umana.

## Principi guida

- Il regime e' probabilistico, non una singola etichetta deterministica.
- Macro regime, market regime e portfolio regime restano separati.
- Lo stato `Incerto/Transizione` e' obbligatorio quando i segnali divergono.
- Le decisioni allocative sono subordinate a IPS, bande strategiche, turnover, costi e fiscalita'.
- Ogni calcolo deve essere ricostruibile as-of date, con fonte, osservazione, pubblicazione e versione del modello.
- La baseline rule-based viene implementata prima dei modelli avanzati.
- HMM, clustering e jump model entrano inizialmente come challenger, non come motore primario.

## Architettura funzionale

1. Data foundation
   - Serie macro, serie mercato, fonti dati, calendario rilasci, vintage.
   - Supporto futuro a FRED, ALFRED, FRED-MD/FRED-QD, market data e import manuale.

2. Macro feature store
   - Feature normalizzate per growth, inflation, risk, monetary, credit/liquidity e sentiment.
   - Rank rolling, z-score, momentum 4/8/13 settimane, variazioni YoY/MoM.
   - Versionamento di formule, pesi, polarita' e finestre.

3. Rule-based regime detector
   - Sub-indici: GrowthScore, InflationScore, RiskScore, MonetaryScore, opzionale SentimentScore.
   - Composite Regime Score configurabile.
   - Persistenza minima, soglie fuzzy, segnale di velocita' e consenso tra dimensioni.

4. Regime state machine
   - Candidate regime, confirmed regime, transition state e cooldown.
   - Evita oscillazioni operative e registra ogni cambio di regime con motivazione.

5. Reporting regime-aware
   - Probabilita' per regime, driver, segnali contrari, variazione rispetto al mese precedente.
   - Collegamento a portafoglio: asset class favorite/sfavorite, tilt suggerito, costo stimato e decisione.

6. Research lab avanzato
   - Modulo separato per HMM, Markov switching, clustering, jump model e ottimizzazione soglie.
   - Walk-forward obbligatorio e benchmark contro CRS baseline.

## Fase 6 - Implementazione applicativa

### 6A. Data Foundation

Entita':
- `MacroDataSource`
- `MacroSeries`
- `MacroObservation`
- `DataVintage`

Requisiti:
- Salvare fonte, frequenza, unita', polarita' e categoria economica della serie.
- Salvare data osservazione e data pubblicazione.
- Predisporre il campo vintage/revisione anche se il primo seed e' demo.

### 6B. Feature Store

Entita':
- `MacroFeatureDefinition`
- `MacroFeatureValue`
- `MacroFeatureSetVersion`

Requisiti:
- Ogni feature deve avere formula descrittiva, dimensione, peso, lookback, polarita' e versione.
- Ogni valore calcolato deve conservare raw value, normalized value, z-score, momentum e interpretation.

### 6C. Baseline Rule-Based

Entita':
- `RegimeModel`
- `RegimeModelVersion`
- `RegimeRun`
- `RegimeProbability`
- `RegimeExplanation`

Requisiti:
- Calcolare un primo snapshot demo da feature seed.
- Produrre probabilita' per almeno quattro regimi.
- Esplicitare driver e segnali contrari.
- Usare `UncertainTransition` se la confidence resta bassa.

### 6D. UI e Report

Viste:
- Dashboard Macro Regime.
- Tabella feature correnti.
- Probabilita' regimi.
- Driver e audit trail.

Requisiti:
- UI sobria, coerente con dashboard/performance esistenti.
- Nessun testo marketing; solo dati, stato, driver e azioni.
- Collegamento nel layout principale.

## Fase 7 - Strategia avanzata

### 7A. Research Lab

- Cartella consigliata: `research/regime-eval/`.
- Python per HMM, Markov switching, clustering, Optuna e notebook.
- C# rimane runtime applicativo.

### 7B. Walk-Forward Backtesting

- Train 10 anni, test 2 anni, avanzamento 1 anno.
- Report separato in-sample / out-of-sample.
- No selezione iperparametri sul test.

### 7C. Metriche composite

- Regime accuracy contro NBER e crisi curate.
- Asset alignment sui rendimenti successivi 4-13 settimane.
- Tilt simulation contro baseline strategica.
- Penalita' asimmetrica per falsi negativi in Stagflazione e Deflation/Bust.

### 7D. Ottimizzazione vincolata

- Bande IPS e policy di portafoglio.
- Turnover massimo.
- Costi e fiscalita'.
- Penalita' per portafogli estremi.
- Shrinkage su expected return.

### 7E. Stress Test

- Scenari storici: 1973-74, 2000-02, 2008-09, 2020, 2022.
- Scenari fattoriali: tassi +300bp, HY spread +500bp, USD +20%, equity -35%, correlazioni a 1.
- Reverse stress test sul rischio primario: liquidazione forzata in momento avverso.

## Definition of Done iniziale

- Piano salvato e versionabile.
- Entita' EF Core della Fase 6 presenti.
- Seed demo con serie macro, feature e run regime.
- Servizio applicativo per leggere dashboard Macro-Regime.
- Controller e vista MVC raggiungibili dal menu.
- Build e test automatici verdi.
