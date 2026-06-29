# Framework e librerie GitHub per regime macro/market-regime applicabile a portafogli

_Data ricerca: 25 giugno 2026_

## Obiettivo

Identificare repository GitHub utili per calcolare o modellare il regime macro/finanziario corrente, con possibile impiego in portafogli regime-aware. La ricerca privilegia progetti:

- pubblici e consultabili;
- con struttura leggibile e documentazione;
- con segnali di consenso comunitario, soprattutto stelle/fork, release, uso accademico o provenienza istituzionale;
- pertinenti a regimi macro, market regime, HMM, clustering, Jump Models, asset allocation o portfolio optimization regime-switching.

> Nota: i progetti “macro regime” puri sono relativamente pochi e spesso meno popolari dei framework generali di portfolio optimization. Per questo il documento distingue tra **candidati principali** e **progetti promettenti/specialistici**.

---

## Sintesi raccomandazione

| Priorità | Progetto | Perché considerarlo |
|---:|---|---|
| 1 | `Snow-Ouyang/Market-Regime-Clustering` | È il candidato più vicino alla richiesta: regime macro-finanziario esplicito, feature macro, Jump Models, interpretazione economica, asset mapping. |
| 2 | `QuhiQuhihi/regime_model` | Più consenso community tra i progetti specifici di regime detection; HMM/GMM multi-asset ispirato a Two Sigma. |
| 3 | `braverock/PortfolioAnalytics` | Non calcola da solo il regime macro, ma è il framework più maturo per ottimizzare portafogli anche in setup regime-switching. |
| 4 | `blackswan-quants/marketregime_hmm` | Buona architettura, FRED + Yahoo Finance, HMM + DTW validation; community ancora limitata. |
| 5 | `MarketMoodRing` | Package Python dedicato a regime detection + portfolio optimizer, nato in contesto UC Berkeley MFE; meno consenso GitHub. |

---

## Candidati principali

### 1. Snow-Ouyang / Market-Regime-Clustering

- **URL:** https://github.com/Snow-Ouyang/Market-Regime-Clustering
- **Linguaggio:** Python
- **Stelle/Fork osservati:** 8 stelle, 0 fork
- **Release:** v1.0.0 “Macro Regime Clustering”, Apr 8 2026
- **Dominio:** macro-regime clustering, Jump Models, cross-asset mapping
- **Metodologia:** 4-state Jump Model con feature macro-finanziarie mensili.
- **Feature principali:**
  - `growth_pc1`: componente principale di crescita da CFNAI, GDP growth, industrial production, ISM;
  - `inflation_pc1`: componente inflazione da CPI, PPI, consumer sentiment;
  - tasso Treasury 10Y;
  - term spread 10Y-1Y;
  - credit spread BAA-AAA;
  - 4 regimi interpretabili: Late-Cycle / Inflationary Flat Curve, Low-Rate / Steep Curve, High-Rate / Resilient Growth, Macro-Financial Stress;
  - asset mapping su equity, bond, oil, gold;
  - documentazione su model selection e interpretazione finale.
- **Punti forti:**
  - molto aderente al concetto di regime macroeconomico;
  - usa dati macro pubblici;
  - separa esplicitamente lo stato di stress macro-finanziario;
  - include output riproducibili e struttura `src/`, `docs/`, `results/`, `figures/`.
- **Limiti:**
  - community ancora piccola;
  - frequenza mensile, più adatta a strategic/tactical asset allocation che a trading veloce;
  - non è un motore “live” pronto per produzione.
- **Uso consigliato:** base di ricerca per costruire un classificatore macro-regime mensile da collegare a pesi di portafoglio o capital market assumptions condizionali.

---

### 2. QuhiQuhihi / regime_model

- **URL:** https://github.com/QuhiQuhihi/regime_model
- **Linguaggio:** Jupyter Notebook / Python
- **Stelle/Fork osservati:** 119 stelle, 25 fork
- **Dominio:** market regime detection multi-asset
- **Metodologia:** Gaussian Mixture Model, Hidden Markov Model, Greedy Gaussian Segmentation.
- **Feature principali:**
  - rilevazione automatica dei cambi di regime;
  - uso di più asset class: azioni, obbligazioni, real estate, commodity;
  - ispirazione esplicita al lavoro Two Sigma su machine-learning regime modeling;
  - notebook e blog di supporto.
- **Punti forti:**
  - buon consenso relativo per la nicchia;
  - metodologie classiche e comprensibili;
  - utile per regime detection cross-asset.
- **Limiti:**
  - più orientato a “market regime” che a regime macro puro;
  - struttura più da ricerca/notebook che da libreria production-ready;
  - non sembra avere release ufficiali.
- **Uso consigliato:** benchmark pratico per HMM/GMM multi-asset e prototipazione di segnali regime-aware.

---

### 3. braverock / PortfolioAnalytics

- **URL:** https://github.com/braverock/PortfolioAnalytics
- **Linguaggio:** R
- **Stelle/Fork osservati:** 103 stelle, 50 fork
- **Dominio:** portfolio optimization in R
- **Metodologia:** portfolio optimization con vincoli, obiettivi custom, rebalancing, motori global/local optimization.
- **Feature principali:**
  - ottimizzazione multi-obiettivo;
  - supporto a CVXR, ROI, DEoptim, random portfolios, GenSA, particle swarm, mco, OSQP, GLPK;
  - funzioni per momenti e obiettivi custom;
  - supporto documentato a ottimizzazione attraverso regimi di mercato;
  - molti esempi e demo.
- **Punti forti:**
  - progetto maturo rispetto agli altri candidati;
  - migliore consenso comunitario nel sottoinsieme “portfolio construction”;
  - adatto per costruire i portafogli condizionati da regimi generati da un altro modello.
- **Limiti:**
  - non è un classificatore di regime macro;
  - richiede un regime model esterno o una funzione custom che produca stati/probabilità;
  - ecosistema R.
- **Uso consigliato:** motore di ottimizzazione per trasformare regimi macro/market-regime in allocazioni operative.

---

### 4. blackswan-quants / marketregime_hmm

- **URL:** https://github.com/blackswan-quants/marketregime_hmm
- **Linguaggio:** Jupyter Notebook / Python
- **Stelle/Fork osservati:** 8 stelle, 4 fork
- **Dominio:** market regime detector con segnali macro e cross-asset
- **Metodologia:** Gaussian HMM + Dynamic Time Warping clustering per validazione.
- **Feature principali:**
  - ingestione dati da FRED + Yahoo Finance;
  - feature engineering market/credit/cross-asset;
  - test di stazionarietà ADF/KPSS;
  - filtro collinearità VIF;
  - PCA per categoria;
  - scelta numero stati con penalized BIC;
  - HMM con 50-start EM;
  - posterior probabilities per timestamp;
  - validazione via DTW hierarchical clustering con ARI/NMI.
- **Punti forti:**
  - pipeline ben descritta;
  - usa segnali macro-finanziari e cross-asset;
  - orientamento riproducibile e attenzione alla qualità del codice, inclusi pre-commit hook.
- **Limiti:**
  - community limitata;
  - progetto recente/di ricerca;
  - più “market state” risk-on/neutral/risk-off che ciclo macro classico.
- **Uso consigliato:** buon candidato Python per costruire un regime classifier interpretabile con probabilità posteriori e segnali macro/credito.

---

### 5. yvesdhondt / MarketMoodRing

- **URL:** https://github.com/yvesdhondt/MarketMoodRing
- **Linguaggio:** Python
- **Stelle/Fork osservati:** 15 stelle, 5 fork
- **Dominio:** regime-dependent portfolio optimization
- **Origine:** ricerca UC Berkeley Haas School of Business, Master of Financial Engineering 2023
- **Metodologia:** Hidden Markov Models e Wasserstein K-Means per regime detection; portfolio optimizers per test regime-aware.
- **Feature principali:**
  - package Python dedicato;
  - classi per HiddenMarkovRegimeDetection;
  - clustering Wasserstein K-Means;
  - optimizer stocastico e factor-based;
  - paper di riferimento incluso nella cartella `reference`;
  - licenza MIT.
- **Punti forti:**
  - unisce regime detection e portfolio optimization;
  - nasce da ricerca accademica applicata;
  - più “framework” rispetto ai notebook singoli.
- **Limiti:**
  - non disponibile su PyPI;
  - installazione via clone locale;
  - community contenuta.
- **Uso consigliato:** laboratorio Python per comparare metodi di regime detection e ottimizzatori regime-dependent.

---

## Progetti promettenti o specialistici

### 6. LSEG-API-Samples / MarketRegimeDetectionUsingStatisticalAndMLBasedApproaches

- **URL:** https://github.com/LSEG-API-Samples/Article.RD.Python.MarketRegimeDetectionUsingStatisticalAndMLBasedApproaches
- **Linguaggio:** Python / Notebook
- **Stelle/Fork osservati:** 61 stelle, 9 fork
- **Dominio:** esempio didattico LSEG/Refinitiv su market regime detection
- **Metodologia:** Gaussian HMM, K-Means, Gaussian Mixture Models.
- **Punti forti:**
  - provenienza istituzionale;
  - documentazione didattica;
  - discreto consenso GitHub;
  - confronta più metodi statistici/ML.
- **Limiti:**
  - richiede licenza Refinitiv Data Library per eseguire i workbook;
  - focus su S&P 500 normal/growth vs crash, quindi non macro-regime completo;
  - repository dichiarato come esempio/blueprint, non package.
- **Uso consigliato:** riferimento metodologico, soprattutto se si lavora già con dati LSEG/Refinitiv.

---

### 7. gcosta151 / RS-Portfolio-Opt

- **URL:** https://github.com/gcosta151/RS-Portfolio-Opt
- **Linguaggio:** Julia
- **Stelle/Fork osservati:** 6 stelle, 3 fork
- **Dominio:** regime-switching portfolio optimization
- **Origine:** codice per esperimenti collegati a due paper: Costa & Kwon 2019 su risk parity sotto Markov regime-switching e Costa & Kwon 2020 su regime-switching factor model per mean-variance optimization.
- **Metodologia:** Markov regime-switching factor model; Baum-Welch per HMM; ottimizzazione con JuMP/Ipopt.
- **Feature principali:**
  - nominal mean-variance optimization;
  - regime-switching mean-variance optimization;
  - nominal minimum variance;
  - regime-switching minimum variance;
  - risk parity;
  - regime-switching risk parity;
  - download dati Kenneth French.
- **Punti forti:**
  - solida base accademica;
  - direttamente orientato a portafogli regime-switching;
  - approccio computazionalmente trattabile per portafogli ampi.
- **Limiti:**
  - community piccola;
  - linguaggio Julia;
  - più focalizzato su asset-return regimes/factor model che su macro-regime corrente.
- **Uso consigliato:** riferimento quantitativo per costruire ottimizzazione di portafoglio condizionata da stati HMM.

---

### 8. YuvrajChauhan-Fin / macro-liquidity-regime-strategy-v4

- **URL:** https://github.com/YuvrajChauhan-Fin/macro-liquidity-regime-strategy-v4
- **Linguaggio:** Jupyter Notebook / Python
- **Stelle/Fork osservati:** 3 stelle, 0 fork
- **Dominio:** strategia macro-liquidity regime con asset allocation
- **Metodologia:** classificazione condizioni di liquidità globale tramite espansione bilanci banche centrali, z-score, smoothing, walk-forward validation, volatility targeting.
- **Feature principali:**
  - classifica regimi Risk-On / Neutral / Risk-Off;
  - usa US M2 growth ed ECB balance-sheet growth;
  - allocazione tattica su NIFTY, SPY, GLD;
  - momentum ranking mensile;
  - inverse-vol risk budgeting;
  - volatility target 10%;
  - expanding walk-forward out-of-sample.
- **Punti forti:**
  - molto vicino al caso d’uso “macro regime → portafoglio”;
  - include controlli anti look-ahead e validazione out-of-sample;
  - architettura dichiarata come modulare e risk-aware.
- **Limiti:**
  - consenso GitHub molto basso;
  - universo asset limitato;
  - frequenza mensile;
  - backtest da verificare indipendentemente prima di uso reale.
- **Uso consigliato:** idea implementativa per costruire un segnale macro-liquidity regime e collegarlo a allocation/risk overlay.

---

### 9. prasants / QuantLite

- **URL:** https://github.com/prasants/QuantLite
- **Linguaggio:** Python
- **Stelle/Fork osservati:** 2 stelle, 0 fork
- **Pubblicazione:** package installabile via `pip install quantlite`
- **Dominio:** toolkit quant finance “fat-tail-native” con regimi, rischio, portfolio optimization, data connectors.
- **Feature principali:**
  - connector Yahoo, crypto, FRED;
  - `detect_regimes(data, n_regimes=3)`;
  - HMM regime detection con `hmmlearn` opzionale;
  - changepoint detection CUSUM e Bayesian;
  - regime-conditional risk metrics e VaR;
  - defensive tilting e filtered backtesting;
  - portfolio optimization: mean-variance, CVaR, risk parity, HRP, Black-Litterman, Kelly;
  - report/tearsheet HTML/PDF.
- **Punti forti:**
  - API integrata molto interessante: fetch → detect regimes → construct portfolio → backtest → tearsheet;
  - copertura ampia del workflow quantitativo;
  - documentazione estesa e PyPI.
- **Limiti:**
  - progetto molto giovane e con pochissimo consenso community;
  - solo 1 commit osservato al momento della ricerca, anche se con tag/release;
  - da validare con attenzione prima dell’uso.
- **Uso consigliato:** prototipo rapido o “inspiration layer” per API design di una libreria interna.

---

### 10. JackDamato / macro-regime-allocation

- **URL:** https://github.com/JackDamato/macro-regime-allocation
- **Linguaggio:** Jupyter Notebook
- **Stelle/Fork osservati:** 3 stelle, 0 fork
- **Dominio:** inflation regime forecasting per sector allocation
- **Metodologia:** 3-state Gaussian HMM su macro e market features.
- **Feature principali:**
  - dati macro FRED: CPI, Fed Funds, GDP ecc.;
  - dati Yahoo Finance: SPY e sector ETFs;
  - z-score input;
  - analisi performance settoriale per regime;
  - pesi dinamici basati su Sharpe-like scores regime-specifici.
- **Punti forti:**
  - aderente al tema macro-regime e allocazione settoriale;
  - facile da leggere come notebook didattico.
- **Limiti:**
  - progetto piccolo;
  - notebook-only;
  - non adatto a produzione senza refactoring.
- **Uso consigliato:** esempio didattico per inflation regime + sector allocation.

---

## Valutazione comparativa

| Progetto | Aderenza macro | Aderenza portfolio | Maturità struttura | Consenso community | Prontezza produzione | Nota sintetica |
|---|---:|---:|---:|---:|---:|---|
| Snow-Ouyang/Market-Regime-Clustering | Alta | Media | Alta | Bassa-media | Media | Miglior candidato per macro-regime research. |
| QuhiQuhihi/regime_model | Media | Media | Media | Alta per la nicchia | Bassa-media | Ottimo benchmark HMM/GMM multi-asset. |
| braverock/PortfolioAnalytics | Bassa | Alta | Alta | Alta | Alta | Motore portfolio maturo, non classificatore macro. |
| blackswan-quants/marketregime_hmm | Media-alta | Media | Alta | Bassa-media | Media | Buona pipeline Python HMM con FRED/Yahoo. |
| MarketMoodRing | Media | Alta | Media | Media | Bassa-media | Package di ricerca regime + portfolio optimization. |
| LSEG sample | Bassa-media | Bassa-media | Media | Alta | Bassa | Buon blueprint, dipende da Refinitiv. |
| RS-Portfolio-Opt | Bassa-media | Alta | Media | Bassa | Media | Base accademica forte in Julia. |
| macro-liquidity-regime-v4 | Alta | Alta | Media | Bassa | Bassa-media | Interessante ma poco validato. |
| QuantLite | Media | Alta | Alta dichiarata | Bassa | Da verificare | API promettente, progetto giovane. |
| macro-regime-allocation | Alta | Media | Bassa-media | Bassa | Bassa | Notebook didattico su inflation regimes. |

---

## Suggerimento architetturale per un portafoglio regime-aware

Una combinazione pragmatica potrebbe essere:

1. **Regime engine macro:** partire da `Snow-Ouyang/Market-Regime-Clustering` o `blackswan-quants/marketregime_hmm`.
2. **Benchmark market-regime:** confrontare con `QuhiQuhihi/regime_model` per HMM/GMM multi-asset.
3. **Portfolio construction:** usare `PortfolioAnalytics` in R, oppure replicare in Python/Julia le logiche di `RS-Portfolio-Opt`.
4. **Validation:** walk-forward, out-of-sample, no look-ahead, transaction costs, turnover e regime-persistence checks.
5. **Output operativo:** probabilità per regime, non solo label discreta; usare soglie e smoothing per evitare eccessivo turnover.

---

## Due diligence prima dell’adozione

Prima di usare uno di questi framework in produzione:

- controllare licensing e compatibilità commerciale;
- verificare frequenza e disponibilità dei dati macro;
- ricostruire interamente il dataset per evitare look-ahead bias;
- valutare ritardi di pubblicazione dei dati macro reali;
- usare revisioni vintage, se possibile, per simulare il dato disponibile al tempo;
- validare la stabilità dei regimi su finestre rolling;
- preferire output probabilistici HMM/Jump Model rispetto a switching binari;
- separare il modulo regime dal modulo allocation;
- testare robustezza a costi, slippage, asset universe alternativo e sample period.

---

## Conclusione

Per un progetto serio di portafogli macro-regime-aware, il candidato più coerente è **Snow-Ouyang/Market-Regime-Clustering**, perché modella direttamente regimi macro-finanziari interpretabili. Per un approccio più community-tested e semplice da replicare, **QuhiQuhihi/regime_model** è il miglior benchmark di regime detection multi-asset. Per la parte di costruzione portafoglio, **PortfolioAnalytics** è il componente più maturo, da combinare con un regime classifier esterno.

