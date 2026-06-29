# Analisi di progetti GitHub per la gestione di un portafoglio finanziario personale

Data analisi: 2026-06-29  
Obiettivo: identificare e valutare progetti open source su GitHub focalizzati sulla gestione di portafogli finanziari personali, con attenzione a completezza funzionale e consenso della comunita di sviluppatori.

> Nota metodologica: i dati di consenso della comunita, come stelle, fork, release, issue e commit, sono stati rilevati da GitHub e dalle pagine ufficiali dei progetti al 2026-06-29. Sono metriche dinamiche e vanno rivalutate prima di una decisione implementativa definitiva.

---

## 1. Sintesi esecutiva

La ricerca evidenzia tre categorie distinte di progetti:

1. **Applicazioni mature per tracking e performance di portafoglio**
   - `portfolio-performance/portfolio`
   - `wealthfolio/wealthfolio`
   - `ghostfolio/ghostfolio`
   - `rotki/rotki`

2. **Progetti emergenti con forte copertura funzionale ma comunita piu piccola**
   - `quovibe-web/quovibe`
   - `Maermin/MAERMIN`
   - `aybruhm/folio`
   - `GiuseppeDM98/net-worth-tracker`
   - `LuoDi-Nate/financial-management`
   - `PhDFlo/foliotrack`
   - `investbrainapp/investbrain`

3. **Sistemi di contabilita personale o componenti di supporto**
   - `firefly-iii/firefly-iii`
   - `beancount/fava`
   - `hoostus/portfolio-returns`
   - `RIP-Comm/sossoldi`

La conclusione operativa e netta:

- **Miglior scelta complessiva per misurazione rigorosa delle performance di investimento**: `portfolio-performance/portfolio`.
- **Miglior scelta moderna local-first per tracking personale multi-account con TWR e MWR dichiarati**: `wealthfolio/wealthfolio`.
- **Miglior scelta self-hosted con forte comunita e interfaccia web moderna**: `ghostfolio/ghostfolio`, con caveat sulla completezza degli indicatori time/value based.
- **Miglior scelta per crypto, DeFi, accounting e privacy**: `rotki/rotki`.
- **Migliori progetti emergenti da studiare per design funzionale avanzato**: `quovibe-web/quovibe`, `Maermin/MAERMIN`, `GiuseppeDM98/net-worth-tracker`.

Per costruire un sistema informativo personale robusto, la baseline piu difendibile e:

- usare `Portfolio Performance` o `Wealthfolio` come riferimento funzionale per performance, asset allocation e multivaluta;
- studiare `Ghostfolio` per architettura web self-hosted, gestione utenti/account e UX dashboard;
- studiare `Rotki` se il portafoglio include crypto, DeFi, exchange centralizzati e necessita di accounting;
- considerare `Firefly III` o `Fava/Beancount` come layer separato per contabilita personale, budget e cash flow, non come motore principale di portfolio analytics.

---

## 2. Criteri di valutazione

I progetti sono stati valutati su due assi principali.

### 2.1 Completezza funzionale

Sono stati considerati:

- **Gestione multivaluta**: supporto a valute multiple, cambio storico, valuta base, attribuzione FX.
- **Gestione multiportafoglio / multi-account**: piu conti, broker, portafogli, famiglie o utenti.
- **Asset coverage**: azioni, ETF, obbligazioni, fondi, crypto, cash, immobili, passivita, asset alternativi.
- **Metriche di portafoglio**: asset allocation, concentrazione, benchmark, volatilita, drawdown, Sharpe, Sortino, beta, alpha, tracking error.
- **Indicatori time based**: TWR, TTWROR, rendimento indipendente dai flussi esterni.
- **Indicatori value/money based**: IRR, XIRR, MWR, rendimento dipendente da flussi, timing e capitale investito.
- **Rebalancing**: target allocation, drift, suggerimenti di ribilanciamento.
- **Dividendi e redditi**: cedole, dividendi, interessi, income tracking.
- **Import/export e integrazioni dati**: CSV, JSON, XML, broker sync, Yahoo Finance, Alpha Vantage, ECB, CoinGecko, API.
- **Privacy e deployment**: desktop locale, self-host, Docker, mobile, cloud opzionale.

### 2.2 Consenso della comunita

Sono stati considerati:

- stelle GitHub;
- fork;
- numero di release;
- frequenza di aggiornamento;
- commit e longevita;
- issue e pull request aperte;
- chiarezza documentale;
- licenza;
- presenza di community, discussioni o roadmap.

Le stelle non sono trattate come misura assoluta di qualita tecnica. Sono un proxy utile di visibilita, adozione e rischio di abbandono, ma possono sottostimare progetti nuovi o di nicchia.

---

## 3. Nota sui rendimenti: TWR, TTWROR, MWR, IRR e XIRR

Per un sistema di gestione di portafoglio personale, e essenziale distinguere tra rendimento indipendente dai flussi e rendimento effettivamente realizzato dall'investitore.

### Time Weighted Return

Il **TWR** misura il rendimento della strategia di investimento neutralizzando l'effetto dei conferimenti e prelievi esterni. E utile per:

- confrontare portafogli o strategie;
- valutare la qualita della selezione degli asset;
- confrontare il portafoglio con benchmark;
- non penalizzare o premiare il gestore per la tempistica dei flussi esterni.

Il **TTWROR** e una variante pratica usata da `Portfolio Performance`, orientata al calcolo giornaliero e alla corretta gestione dei flussi.

### Money Weighted Return

Il **MWR**, spesso calcolato tramite **IRR** o **XIRR**, misura il rendimento effettivo dell'investitore considerando importi e date dei flussi. E utile per:

- capire quanto ha realmente reso il capitale investito;
- valutare l'impatto del market timing personale;
- misurare obiettivi finanziari personali;
- confrontare rendimento di portafoglio e rendimento dell'investitore.

Un sistema informativo completo dovrebbe supportare entrambi:

- TWR/TTWROR per analisi strategica e confronto con benchmark;
- MWR/IRR/XIRR per analisi personale e decisioni patrimoniali.

---

## 4. Classifica sintetica

| Rank | Progetto | Categoria | Completezza | Consenso community | Valutazione sintetica |
|---:|---|---|---:|---:|---|
| 1 | `portfolio-performance/portfolio` | Desktop portfolio analytics | Molto alta | Alta | Miglior riferimento per performance, TWR/IRR, multivaluta e analisi rigorosa |
| 2 | `wealthfolio/wealthfolio` | Local-first wealth tracker | Molto alta | Alta | Ottimo compromesso moderno tra UX, multi-account, TWR/MWR e privacy |
| 3 | `ghostfolio/ghostfolio` | Self-hosted web portfolio tracker | Alta | Molto alta | Community forte e prodotto maturo; metriche performance meno complete rispetto ai migliori |
| 4 | `rotki/rotki` | Crypto/accounting/portfolio manager | Media-alta | Alta | Migliore per crypto, DeFi, privacy e accounting; meno centrato su TWR/MWR classici |
| 5 | `quovibe-web/quovibe` | Self-hosted portfolio tracker | Molto alta | Bassa | Funzionalita eccellenti, community ancora minima |
| 6 | `GiuseppeDM98/net-worth-tracker` | Personal finance per investitori italiani | Alta | Bassa-media | Molto interessante per contesto italiano, performance e bond; community limitata |
| 7 | `Maermin/MAERMIN` | Client-side multi-asset tracker | Molto alta | Molto bassa | Funzionalita avanzate ma consenso quasi nullo |
| 8 | `investbrainapp/investbrain` | Investment tracker self-hosted | Media-alta | Media | Buon progetto moderno, con focus AI e performance snapshot |
| 9 | `LuoDi-Nate/financial-management` | Household wealth management | Media-alta | Media-bassa | Ottimo per patrimonio familiare e XIRR/TWR; approccio snapshot e contesto cinese |
| 10 | `PhDFlo/foliotrack` | Python library/toolkit | Alta come toolkit | Molto bassa | Buono per motore di rebalancing/backtest, non app completa |
| 11 | `aybruhm/folio` | Self-hosted tracker | Alta dichiarata | Nulla | Funzioni complete ma progetto personale/immature |
| 12 | `firefly-iii/firefly-iii` | Personal finance/accounting | Bassa per portfolio | Molto alta | Eccellente per budgeting e contabilita, non motore portfolio analytics |
| 13 | `beancount/fava` | Accounting plaintext | Media come base contabile | Alta | Ottimo backend contabile per utenti tecnici; portfolio analytics non turnkey |
| 14 | `RIP-Comm/sossoldi` | Personal finance/net worth | Bassa oggi | Media | Progetto promettente, investimento ancora largamente pianificato |
| 15 | `hoostus/portfolio-returns` | Add-on Beancount returns | Bassa-media | Bassa | Utile per MWR/XIRR, TWR non implementato secondo README |

---

## 5. Matrice comparativa funzionale

Legenda:

- `++` supporto forte o dichiarato esplicitamente;
- `+` supporto parziale o indiretto;
- `~` supporto plausibile ma non centrale;
- `-` non trovato o non dichiarato;
- `?` informazione non verificata.

| Progetto | Multivaluta | Multiportafoglio/account | TWR/TTWROR | MWR/IRR/XIRR | Metriche rischio | Rebalancing | Asset coverage | Privacy/self-host |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Portfolio Performance | ++ | ++ | ++ | ++ | + | ++ | ++ | ++ |
| Wealthfolio | ++ | ++ | ++ | ++ | + | ++ | ++ | ++ |
| Ghostfolio | + | ++ | + | ~ | + | + | ++ | ++ |
| Rotki | ++ | ++ | ~ | ~ | + | ~ | ++ crypto | ++ |
| Quovibe | ++ | ++ | ++ | ++ | ++ | ++ | ++ | ++ |
| MAERMIN | ++ | ++ | ++ | ++ | ++ | ++ | ++ | ++ |
| Net Worth Tracker | ++ | + | ++ | + | ++ | ++ | ++ | ++ |
| InvestBrain | + | + | ~ | ~ | + | ? | + | ++ |
| Family Ledger | ++ | ++ family | ++ | ++ | + | + | + | ++ |
| Foliotrack | ++ | + | ++ | ? | ++ | ++ | + | ++ |
| Folio | ++ | ++ | ++ | ++ | + | + | + | ++ |
| Firefly III | ++ | + | - | - | - | - | - | ++ |
| Fava/Beancount | ++ | + | ~ | ~ | ~ | ~ | + | ++ |
| Sossoldi | + planned | + planned | - | - | - | - | planned | ++ |
| Portfolio Returns | ~ | ~ | - | ++ | - | - | + via Beancount | ++ |

---

## 6. Analisi dettagliata dei progetti

## 6.1 `portfolio-performance/portfolio`

Repository: `https://github.com/portfolio-performance/portfolio`  
Categoria: desktop application per tracking e performance di portafoglio  
Licenza: EPL-1.0  
Tecnologia principale: Java  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 3.9k |
| Fork | circa 786 |
| Commit | circa 8,151 |
| Release | circa 271 |
| Ultima release osservata | `0.84.2`, 2026-06-22 |
| Issue aperte | circa 397 |
| Pull request aperte | circa 69 |

### Funzionalita rilevanti

`Portfolio Performance` e uno dei progetti piu completi e maturi per l'analisi di portafogli personali. Il progetto dichiara esplicitamente la capacita di:

- tracciare e valutare performance di portafoglio su azioni, crypto e altri asset;
- registrare acquisti, vendite, tasse e commissioni;
- calcolare performance complessiva su tutti i conti;
- calcolare **True-Time Weighted Return**;
- calcolare **Internal Rate of Return**;
- caricare prezzi storici da fonti esterne;
- esportare dati in CSV e JSON;
- gestire file dati XML;
- supportare ribilanciamento basato su asset allocation;
- gestire conti in valuta estera e tassi di cambio BCE.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Molto forte. Supporto esplicito a conti in valuta estera e tassi BCE |
| Multiportafoglio/account | Forte. Struttura conti, depositi, asset e strumenti |
| Metriche di portafoglio | Forte. Performance, asset allocation, benchmark, classificazioni |
| Time based return | Molto forte. TTWROR e TWR sono elementi centrali |
| Value/money based return | Molto forte. IRR dichiarato |
| Rebalancing | Forte. Target allocation e analisi ribilanciamento |
| Privacy | Forte. Applicazione desktop locale |
| Community | Alta. Progetto longevo, release frequenti, molte stelle e fork |

### Punti di forza

- E probabilmente il riferimento open source piu solido per la misurazione rigorosa della performance di investimento personale.
- Supporta sia TWR/TTWROR sia IRR, quindi copre entrambi gli indicatori fondamentali.
- Ha una base utenti consolidata e release molto frequenti.
- Il modello desktop locale riduce dipendenza da cloud e problemi di privacy.
- La gestione multivaluta e sufficientemente esplicita per portafogli internazionali.

### Limiti

- Non e una web app moderna self-hosted.
- L'UX puo essere piu tecnica rispetto a soluzioni come Ghostfolio o Wealthfolio.
- L'integrazione diretta con broker puo essere meno centrale rispetto a prodotti piu recenti.

### Ruolo consigliato in un sistema informativo

`Portfolio Performance` dovrebbe essere usato come benchmark funzionale per:

- calcolo TWR/TTWROR;
- calcolo IRR;
- classificazione asset;
- gestione multivaluta;
- rendicontazione di portafoglio;
- logica di ribilanciamento.

Se l'obiettivo e costruire un sistema nuovo, questo progetto rappresenta un riferimento da imitare sul piano dei calcoli e della completezza analitica.

---

## 6.2 `wealthfolio/wealthfolio`

Repository: `https://github.com/wealthfolio/wealthfolio`  
Categoria: local-first wealth and portfolio tracker  
Tecnologie principali: TypeScript, desktop/web/mobile secondo canali dichiarati  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 7.7k |
| Fork | circa 531 |
| Commit | circa 3,112 |
| Issue aperte | circa 236 |
| Pull request aperte | circa 34 |

### Funzionalita rilevanti

`Wealthfolio` si presenta come investment tracker open source, privato e local-first. Le funzionalita dichiarate includono:

- tracciamento investimenti, net worth, spending e simulazioni;
- supporto desktop Windows, macOS, Linux;
- supporto iOS e opzione Docker/web self-hosted;
- gestione di investimenti su piu account e asset type;
- **True time-weighted returns**;
- **Money-weighted returns**;
- benchmark comparison;
- historical analysis;
- gestione attivita/import;
- goal planning;
- allocation e rebalancing;
- dati locali;
- broker sync opzionale;
- multi-currency con exchange rate management;
- device sync opzionale cifrato;
- household view.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Molto forte. Exchange rate management dichiarato |
| Multiportafoglio/account | Molto forte. Multi-account e household view |
| Metriche di portafoglio | Forte. Portfolio insights, performance dashboard, benchmark |
| Time based return | Molto forte. TWR dichiarato |
| Value/money based return | Molto forte. MWR dichiarato |
| Rebalancing | Forte. Allocation target e rebalancing |
| Privacy | Molto forte. Local-first, sync opzionale |
| Community | Alta. Numero di stelle elevato e progetto molto visibile |

### Punti di forza

- Ottimo equilibrio tra completezza finanziaria e architettura moderna.
- Supporta esplicitamente TWR e MWR, requisito fondamentale per un sistema corretto.
- Approccio local-first coerente con dati finanziari personali sensibili.
- Copre investimenti, net worth, spending e simulazioni, quindi si avvicina a una visione patrimoniale completa.
- Community molto significativa.

### Limiti

- Alcune funzioni dipendono dal livello di maturita delle app e dei canali di distribuzione.
- La complessita del prodotto richiede verifica diretta della qualita dei calcoli.
- Il broker sync opzionale introduce dipendenze esterne.

### Ruolo consigliato in un sistema informativo

`Wealthfolio` e uno dei candidati migliori come base applicativa moderna per:

- dashboard personale;
- tracking multi-account;
- performance personale;
- net worth;
- pianificazione obiettivi;
- rebalancing.

Per un nuovo sistema informativo, e un riferimento molto forte per architettura local-first, UX e copertura funzionale.

---

## 6.3 `ghostfolio/ghostfolio`

Repository: `https://github.com/ghostfolio/ghostfolio`  
Categoria: self-hosted wealth management software  
Licenza: AGPL-3.0  
Tecnologie principali: TypeScript, Angular, NestJS, Prisma, PostgreSQL, Redis, Docker  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 8.9k |
| Fork | circa 1.2k |
| Commit | circa 5,052 |
| Release | circa 704 |
| Ultima release osservata | `3.18.0`, 2026-06-28 |

### Funzionalita rilevanti

`Ghostfolio` e una delle piattaforme open source piu note per il tracking del patrimonio finanziario. Le funzionalita dichiarate includono:

- gestione transazioni;
- multi account management;
- analisi performance;
- Return on Average Investment per periodi come Today, WTD, MTD, YTD, 1Y, 5Y, Max;
- chart e dashboard;
- static analysis;
- import/export;
- Progressive Web App;
- supporto a stock, ETF e crypto;
- deployment self-hosted con Docker;
- attenzione a privacy e data ownership.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Buona. Presente nella logica di prodotto, da verificare nei dettagli operativi |
| Multiportafoglio/account | Forte. Multi account management dichiarato |
| Metriche di portafoglio | Forte. Dashboard, analisi, composizione, performance |
| Time based return | Parziale. Presenza di performance periodiche, ma TWR non emerge come asse forte quanto in Portfolio Performance |
| Value/money based return | Parziale. ROAI dichiarato; MWR/IRR non risulta centrale |
| Rebalancing | Parziale. Utile per composizione e analisi, meno forte come motore di ribilanciamento |
| Privacy | Forte. Self-hosted, data ownership |
| Community | Molto alta. Una delle community piu grandi tra i progetti analizzati |

### Punti di forza

- Community molto ampia.
- Architettura web moderna e self-hosted.
- Buona copertura di asset comuni per investitori personali.
- Ottimo candidato per dashboard patrimoniale.
- Frequenza di release elevata.

### Limiti

- Per un sistema di performance accounting rigoroso, va verificata la disponibilita di TWR/MWR/IRR in senso stretto.
- Il progetto usa metriche proprie come ROAI; questo puo essere utile ma non sostituisce automaticamente TWR e MWR.
- Se l'obiettivo primario e la misurazione istituzionale della performance, `Portfolio Performance` e `Wealthfolio` risultano piu forti.

### Ruolo consigliato in un sistema informativo

`Ghostfolio` e un candidato forte per:

- dashboard web self-hosted;
- gestione utenti/account;
- import/export;
- tracking multi-asset;
- interfaccia moderna per investitore personale.

Non dovrebbe essere assunto come motore definitivo per TWR/MWR senza audit dei calcoli e test su casi con flussi complessi.

---

## 6.4 `rotki/rotki`

Repository: `https://github.com/rotki/rotki`  
Categoria: portfolio manager, accounting e analytics con focus crypto  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 3.9k |
| Fork | circa 740 |
| Commit | circa 20,346 |
| Issue aperte | circa 416 |
| Pull request aperte | circa 13 |

### Funzionalita rilevanti

`Rotki` e un portfolio manager privacy-focused con forte attenzione a crypto, DeFi, accounting e analytics. Le funzionalita rilevanti includono:

- tracking dei saldi su piattaforme, blockchain ed exchange;
- visualizzazioni storiche;
- transaction decoding per blockchain ed exchange;
- impostazioni contabili;
- PnL reports;
- personalizzazione valuta principale e lingua;
- dati locali e cifrati;
- self-hosting o esecuzione locale;
- reporting e analytics.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Forte, soprattutto per crypto e valuta principale |
| Multiportafoglio/account | Forte per exchange, wallet e account crypto |
| Metriche di portafoglio | Buona, orientata a saldi, PnL, accounting e reporting |
| Time based return | Non centrale nei dati raccolti |
| Value/money based return | Non centrale nei dati raccolti |
| Rebalancing | Non emerge come funzione centrale |
| Privacy | Molto forte |
| Community | Alta, con grande base commit e adozione nel dominio crypto |

### Punti di forza

- Uno dei migliori progetti open source per crypto portfolio accounting.
- Forte attenzione alla privacy.
- Copertura ampia di exchange, wallet e blockchain.
- Molto rilevante se il portafoglio personale include DeFi, staking, exchange centralizzati o transazioni on-chain complesse.

### Limiti

- Non e il miglior candidato per un portafoglio tradizionale azioni/ETF/obbligazioni.
- Le metriche TWR/MWR non risultano centrali dalla documentazione esaminata.
- La complessita crypto/accounting puo essere eccessiva per un investitore tradizionale.

### Ruolo consigliato in un sistema informativo

`Rotki` va considerato come modulo specializzato per:

- crypto accounting;
- DeFi transaction decoding;
- saldi e PnL crypto;
- privacy-first data management.

In un sistema integrato, puo convivere con un motore portfolio tradizionale come `Portfolio Performance` o `Wealthfolio`.

---

## 6.5 `quovibe-web/quovibe`

Repository: `https://github.com/quovibe-web/quovibe`  
Categoria: self-hosted portfolio tracker  
Licenza: AGPL-3.0  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 12 |
| Fork | circa 5 |
| Commit | circa 141 |
| Release | circa 12 |
| Ultima release osservata | `v1.6.6`, 2026-06-24 |

### Funzionalita rilevanti

`Quovibe` dichiara un insieme funzionale molto ampio:

- tracking di stocks, ETF e bond;
- TTWROR;
- IRR;
- volatilita;
- Sharpe ratio;
- max drawdown;
- benchmark alpha;
- dashboard personalizzabili con oltre 26 widget;
- piu dashboard;
- 15 tipi di transazione;
- double-entry bookkeeping;
- FIFO e moving average cost basis;
- tassonomie di asset allocation;
- target di ribilanciamento;
- dividendi e interessi;
- multi-currency con FX automatico via BCE;
- import da XML, CSV, HTML table, JSON;
- integrazione Yahoo Finance e Alpha Vantage;
- SQLite e Docker;
- privacy mode;
- supporto multilingua.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Molto forte. FX automatico via BCE |
| Multiportafoglio/account | Forte. Dashboard e bookkeeping evoluto |
| Metriche di portafoglio | Molto forte. Sharpe, volatility, max drawdown, alpha |
| Time based return | Molto forte. TTWROR dichiarato |
| Value/money based return | Molto forte. IRR dichiarato |
| Rebalancing | Forte. Target di ribilanciamento |
| Privacy | Forte. Self-hosted, SQLite, Docker, privacy mode |
| Community | Bassa. Poche stelle e fork |

### Punti di forza

- Funzionalita sorprendentemente complete.
- Copertura esplicita di TWR/TTWROR, IRR, rischio e benchmark.
- Buona architettura self-hosted leggera.
- Ottimo riferimento progettuale per una dashboard di portfolio analytics.

### Limiti

- Community molto piccola.
- Necessario audit diretto dei calcoli.
- Rischio di manutenzione e bus factor elevato.

### Ruolo consigliato in un sistema informativo

`Quovibe` e un progetto da studiare attentamente come prototipo di sistema completo. Tuttavia, per un uso patrimoniale reale, va validato con test numerici indipendenti prima di affidargli calcoli decisionali.

---

## 6.6 `Maermin/MAERMIN`

Repository: `https://github.com/Maermin/MAERMIN`  
Categoria: client-side multi-asset portfolio tracker  
Licenza: MIT  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 1 |
| Fork | 0 |
| Commit | circa 329 |

### Funzionalita rilevanti

`MAERMIN` si presenta come portfolio tracker professionale multi-asset, interamente client-side. Le funzionalita dichiarate includono:

- esecuzione in browser e localStorage;
- vault cifrato AES-256-GCM/PBKDF2 o Argon2id;
- passkey opzionale;
- offline PWA;
- nessun account, server, pubblicita o telemetry;
- asset crypto, stocks, ETF, CS2 skins, commodities;
- multi-portfolio;
- net worth con cash, real estate, loans, property, deposits;
- options;
- dividendi, YOC e simulazione DRIP;
- **money-weighted XIRR**;
- **time-weighted return**;
- benchmark overlay;
- alpha, beta, tracking error, information ratio, R2;
- FX attribution, distinguendo ritorno locale e effetto cambio;
- rebalancing;
- DCA plans;
- fee analyzer;
- Monte Carlo;
- stress test;
- VaR e CVaR;
- Sharpe e Sortino;
- Fama-French;
- FIRE e pianificazione.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Molto forte sulla carta, inclusa attribuzione FX |
| Multiportafoglio/account | Molto forte. Multi-portfolio dichiarato |
| Metriche di portafoglio | Molto forte. Rischio, benchmark, factor model |
| Time based return | Forte. TWR dichiarato |
| Value/money based return | Forte. XIRR dichiarato |
| Rebalancing | Forte |
| Privacy | Molto forte. Client-side, cifratura, offline |
| Community | Molto bassa |

### Punti di forza

- Copertura funzionale estremamente ampia.
- Approccio privacy-first radicale.
- Include metriche avanzate che molti progetti piu popolari non dichiarano.
- Ottimo oggetto di studio per modellazione funzionale.

### Limiti

- Consenso community quasi nullo.
- Rischio alto di progetto individuale.
- Necessario audit molto rigoroso prima di uso reale.
- La ricchezza funzionale dichiarata puo superare la maturita effettiva.

### Ruolo consigliato in un sistema informativo

`MAERMIN` e utile come fonte di idee per:

- FX attribution;
- benchmark analytics;
- risk metrics;
- privacy local-first;
- factor/risk analytics.

Non e consigliabile come base primaria senza verifica estesa e test indipendenti.

---

## 6.7 `GiuseppeDM98/net-worth-tracker`

Repository: `https://github.com/GiuseppeDM98/net-worth-tracker`  
Categoria: personal finance e net worth tracker per investitori italiani  
Licenza: AGPL-3.0  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 67 |
| Fork | circa 14 |
| Commit | circa 882 |
| Issue aperte | 0 |

### Funzionalita rilevanti

Il progetto e orientato a investitori italiani e include:

- asset multipli: stocks, ETF, bonds, crypto, real estate, commodities, cash;
- multi-currency USD, GBP, CHF verso EUR;
- cambio tramite Frankfurter;
- normalizzazione GBp;
- prezzi Yahoo e Borsa Italiana;
- gestione obbligazioni italiane e BTP con coupon schedule;
- costo medio/PMC su piu broker;
- target allocation;
- piano di ribilanciamento senza vendita tramite nuovi contributi;
- TWR;
- Sharpe;
- net cash flow;
- YOC netto;
- selettore periodi YTD, 1Y, 3Y, 5Y, all, custom;
- yield corrente;
- heatmap;
- underwater drawdown;
- rolling CAGR e Sharpe;
- benchmark comparison;
- metriche come volatilita, Sortino, Calmar, max drawdown;
- badge per TWR, IRR, Sharpe e YOC;
- funzioni cash flow e AI.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Forte, con base EUR e valute estere |
| Multiportafoglio/account | Buona, soprattutto su broker e PMC |
| Metriche di portafoglio | Molto forte per un progetto piccolo |
| Time based return | Forte. TWR dichiarato |
| Value/money based return | Buona. IRR menzionato nelle metriche |
| Rebalancing | Forte. Piano di contributi senza vendita |
| Privacy | Forte se self-hosted/local |
| Community | Bassa-media |

### Punti di forza

- Molto rilevante per investitori italiani.
- Gestione dettagliata di BTP, cedole e prezzi italiani.
- Buona copertura di metriche rischio/rendimento.
- Focus pratico su PMC, contribuzioni e ribilanciamento.

### Limiti

- Community limitata.
- Probabile maggiore dipendenza da casi d'uso italiani.
- Serve audit sui calcoli prima di uso produttivo.

### Ruolo consigliato in un sistema informativo

Progetto molto utile se il sistema informativo deve servire un investitore italiano con:

- ETF UCITS;
- BTP e obbligazioni italiane;
- base valutaria EUR;
- attenzione a fiscalita, cedole e PMC.

---

## 6.8 `investbrainapp/investbrain`

Repository: `https://github.com/investbrainapp/investbrain`  
Categoria: self-hosted investment tracker  
Tecnologie principali: Laravel/PHP  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 861 |
| Fork | circa 60 |
| Commit | circa 744 |
| Issue aperte | circa 21 |
| Pull request aperte | circa 2 |
| Release | circa 36 |
| Ultima release osservata | `v1.3.0`, 2026-06-26 |

### Funzionalita rilevanti

`InvestBrain` e uno smart open-source investment tracker self-hosted. Le funzioni rilevanti includono:

- consolidamento e monitoraggio della performance su diversi broker;
- interfaccia provider dati di mercato estensibile;
- integrazione con vari market data provider;
- funzionalita AI con OpenAI/Ollama per interagire con gli holdings;
- i18n, accessibility e dark mode;
- deployment Docker Compose;
- daily currency exchange rate refresh;
- daily portfolio performance snapshots;
- sincronizzazione performance holdings con transazioni;
- dividendi e realized gains;
- cost basis utility.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Buona. Daily currency exchange rate refresh |
| Multiportafoglio/account | Buona. Diversi broker/brokerages |
| Metriche di portafoglio | Buona. Snapshot e performance holdings |
| Time based return | Non chiaramente dichiarato |
| Value/money based return | Non chiaramente dichiarato |
| Rebalancing | Non verificato |
| Privacy | Forte. Self-hosted |
| Community | Media |

### Punti di forza

- Progetto attivo e moderno.
- Buon livello di adozione per un progetto piu recente.
- Integrazione AI interessante per interrogazione del portafoglio.
- Architettura self-hosted.

### Limiti

- TWR/MWR non risultano funzioni centrali esplicite.
- Meno maturo di Ghostfolio e Wealthfolio.
- Va verificata la robustezza dei calcoli rispetto a flussi complessi.

### Ruolo consigliato in un sistema informativo

`InvestBrain` merita studio per:

- architettura self-hosted;
- integrazione provider dati;
- gestione performance snapshot;
- interfaccia AI su holdings.

Non risulta il candidato principale per performance accounting rigoroso.

---

## 6.9 `LuoDi-Nate/financial-management`

Repository: `https://github.com/LuoDi-Nate/financial-management`  
Nome funzionale: Family Ledger  
Categoria: household asset management  
Licenza: Apache-2.0  
Tecnologia principale: Java/Spring Boot  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 192 |
| Fork | circa 11 |
| Commit | circa 219 |
| Issue aperte | 0 |
| Pull request aperte | 0 |

### Funzionalita rilevanti

Il progetto e un'applicazione self-hosted per gestione patrimoniale familiare, con focus su:

- snapshot mensili e settimanali;
- sei tipi di account: cash, stocks, wealth management, real estate, liabilities, other;
- tracking per membro della famiglia;
- rendimento annualizzato reale;
- account/family XIRR;
- asset TWR escludendo income;
- net worth trend corretto per CPI purchasing power e M2;
- base valutaria CNY, USD, HKD;
- FX automatico;
- valorizzazione automatica azioni Cina/USA/HK;
- AI asset health e suggerimenti di ribilanciamento;
- obiettivi: FIRE, educazione, fondo emergenza;
- Docker Compose.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Forte. CNY/USD/HKD e FX automatico |
| Multiportafoglio/account | Forte come household/family system |
| Metriche di portafoglio | Buona, con net worth reale e metriche macro |
| Time based return | Buona. TWR dichiarato a livello asset |
| Value/money based return | Forte. XIRR dichiarato |
| Rebalancing | Buono. Suggerimenti AI |
| Privacy | Forte. Self-hosted |
| Community | Media-bassa |

### Punti di forza

- Interessante approccio a patrimonio familiare, non solo singolo portafoglio.
- Include XIRR e TWR.
- Considera potere d'acquisto, CPI e M2, aspetto raro nei portfolio tracker.
- Buono per net worth e pianificazione familiare.

### Limiti

- Contesto geografico prevalentemente cinese.
- Approccio basato su snapshot, non su ledger dettagliato di singoli strumenti.
- Meno adatto se serve controllo puntuale di ogni transazione finanziaria.

### Ruolo consigliato in un sistema informativo

Utile come riferimento per:

- household balance sheet;
- analisi net worth reale;
- integrazione di inflation adjustment;
- obiettivi patrimoniali familiari.

---

## 6.10 `PhDFlo/foliotrack`

Repository: `https://github.com/PhDFlo/foliotrack`  
Categoria: Python library/toolkit per portfolio management  
Licenza: Apache-2.0  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 2 |
| Fork | 0 |
| Commit | circa 321 |
| Issue aperte | circa 1 |

### Funzionalita rilevanti

`Foliotrack` e una libreria Python per portfolio management, optimization, rebalancing e backtesting. Le funzionalita dichiarate includono:

- tracking stocks, ETF e securities;
- persistenza JSON;
- transaction history;
- multi-currency con ECB rates;
- TWR con gestione dei cash flow esterni;
- oltre 10 metriche tra CAGR, Sharpe, Max Drawdown, Alpha, Beta;
- benchmark comparison;
- rebalancing avanzato;
- vincoli e trade interi tramite MIQP;
- integrazione yfinance, ffn e bt;
- dashboard Streamlit opzionale.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Forte. ECB rates dichiarati |
| Multiportafoglio/account | Parziale, piu toolkit che app |
| Metriche di portafoglio | Forte |
| Time based return | Forte. TWR dichiarato |
| Value/money based return | Non verificato |
| Rebalancing | Molto forte |
| Privacy | Forte, essendo codice locale |
| Community | Molto bassa |

### Punti di forza

- Molto interessante come motore quantitativo.
- Rebalancing avanzato con vincoli realistici.
- Integrazione Python utile per ricerca e prototipazione.
- Buona copertura di metriche classiche.

### Limiti

- Non e una applicazione completa per utente finale.
- Community minima.
- Richiede competenza tecnica.

### Ruolo consigliato in un sistema informativo

`Foliotrack` e da considerare come componente o fonte di design per:

- motore di ribilanciamento;
- simulazioni;
- backtest;
- calcolo metriche;
- integrazione in pipeline Python.

---

## 6.11 `aybruhm/folio`

Repository: `https://github.com/aybruhm/folio`  
Categoria: self-hosted investment tracking platform  
Licenza: GPL-2.0  
Tecnologie principali: SvelteKit, TypeScript, FastAPI, SQLAlchemy, PostgreSQL, Valkey, Docker  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | 0 |
| Fork | 0 |
| Commit | circa 382 |
| Release | circa 44 |
| Ultima release osservata | `v1.23.0`, 2026-06-26 |

### Funzionalita rilevanti

Il progetto dichiara:

- autenticazione;
- multi-portfolio;
- trade history con buy, sell, dividend, fee;
- holdings con yfinance;
- asset class stocks, ETF, crypto, cash;
- CSV import;
- multi-currency con FX automatico;
- TWR;
- MWR;
- asset allocation per asset class e sector;
- performance history;
- contribution charts;
- financial goals;
- FIRE tracking.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Forte sulla carta |
| Multiportafoglio/account | Forte sulla carta |
| Metriche di portafoglio | Buona |
| Time based return | Forte. TWR dichiarato |
| Value/money based return | Forte. MWR dichiarato |
| Rebalancing | Parziale |
| Privacy | Forte. Self-hosted |
| Community | Nulla |

### Punti di forza

- Copertura funzionale molto vicina ai requisiti richiesti.
- Stack moderno.
- Include sia TWR sia MWR.
- Progetto attivo nelle release.

### Limiti

- Zero consenso community al momento della rilevazione.
- Il README segnala che e un progetto personale/vibe-coded e che e previsto un refactor.
- Non consigliabile come base senza audit tecnico completo.

### Ruolo consigliato in un sistema informativo

Da considerare solo come:

- fonte di idee;
- prototipo da studiare;
- possibile base sperimentale non critica.

Non e consigliabile come core produttivo senza revisione.

---

## 6.12 `firefly-iii/firefly-iii`

Repository: `https://github.com/firefly-iii/firefly-iii`  
Categoria: personal finance manager / budgeting / accounting  
Licenza: AGPL-3.0  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 23.9k |
| Fork | circa 2.2k |
| Commit | circa 23,199 |
| Release | circa 328 |
| Ultima release osservata | `v6.6.3`, 2026-05-21 |
| Issue aperte | circa 159 |

### Funzionalita rilevanti

`Firefly III` e un personal finance manager self-hosted molto popolare. Include:

- budget;
- categorie e tag;
- transazioni ricorrenti;
- regole automatiche;
- contabilita in partita doppia;
- obiettivi e salvadanai;
- report entrate/uscite;
- 2FA;
- supporto a qualsiasi valuta;
- Docker;
- REST API.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Forte |
| Multiportafoglio/account | Buona per conti personali |
| Metriche di portafoglio | Debole |
| Time based return | Assente come funzione centrale |
| Value/money based return | Assente come funzione centrale |
| Rebalancing | Assente |
| Privacy | Forte. Self-hosted |
| Community | Molto alta |

### Punti di forza

- Community molto ampia.
- Maturo, self-hosted e ben documentato.
- Ottimo per cash flow, budget, transazioni, categorie e controllo spese.
- API utile per integrazione.

### Limiti

- Non e un portfolio analytics system.
- Non gestisce in modo nativo TWR/MWR, benchmark o ribilanciamento.
- Non e il motore corretto per performance di investimento.

### Ruolo consigliato in un sistema informativo

`Firefly III` e un ottimo componente complementare per:

- contabilita personale;
- budget;
- cash flow;
- spese;
- entrate/uscite;
- integrazione via API.

Non deve essere usato come motore primario di portfolio analytics.

---

## 6.13 `beancount/fava`

Repository: `https://github.com/beancount/fava`  
Categoria: web interface per Beancount plaintext accounting  
Licenza: MIT  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 2.5k |
| Fork | circa 387 |
| Commit | circa 3,455 |
| Tag | circa 69 |
| Issue aperte | circa 96 |
| Pull request aperte | circa 23 |

### Funzionalita rilevanti

`Fava` e l'interfaccia web per `Beancount`, sistema di contabilita in partita doppia basato su file di testo. E rilevante per:

- contabilita personale avanzata;
- ledger plaintext;
- multi-currency tramite Beancount;
- report contabili;
- navigazione web del ledger;
- workflow tecnico e verificabile.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Forte via Beancount |
| Multiportafoglio/account | Buona via struttura contabile |
| Metriche di portafoglio | Parziale |
| Time based return | Non turnkey |
| Value/money based return | Non turnkey |
| Rebalancing | Non turnkey |
| Privacy | Forte. File locali |
| Community | Alta |

### Punti di forza

- Ottima base contabile per utenti tecnici.
- Ledger testuale, versionabile e auditabile.
- Community solida.
- Eccellente come fonte dati strutturata.

### Limiti

- Non e un prodotto portfolio tracker pronto per investitore non tecnico.
- Le metriche TWR/MWR richiedono componenti aggiuntivi o calcoli custom.
- Richiede disciplina contabile.

### Ruolo consigliato in un sistema informativo

`Fava/Beancount` e utile come:

- layer contabile verificabile;
- sorgente dati canonica;
- base per automazioni custom;
- soluzione per utenti tecnici che vogliono pieno controllo.

Non sostituisce direttamente un motore portfolio analytics.

---

## 6.14 `hoostus/portfolio-returns`

Repository: `https://github.com/hoostus/portfolio-returns`  
Categoria: calcolo rendimenti per Beancount  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 42 |
| Fork | circa 6 |
| Commit | circa 33 |
| Issue aperte | circa 1 |

### Funzionalita rilevanti

Il progetto si propone di calcolare rendimenti per portafogli gestiti in Beancount. Elementi rilevanti:

- calcolo money-weighted return;
- calcolo XIRR;
- discussione di time-weighted return;
- uso come componente per ledger Beancount.

Tuttavia, la documentazione contiene una limitazione importante: il TWR risulta non implementato in una sezione del README, nonostante il progetto discuta il tema.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Parziale, con criticita note |
| Multiportafoglio/account | Dipende da Beancount |
| Metriche di portafoglio | Limitate |
| Time based return | Non implementato secondo README |
| Value/money based return | Forte per XIRR/MWR |
| Rebalancing | Assente |
| Privacy | Forte. Locale |
| Community | Bassa |

### Punti di forza

- Utile per capire come calcolare MWR/XIRR da ledger contabile.
- Complementare a Beancount.
- Progetto semplice da studiare.

### Limiti

- Non e una app completa.
- TWR non implementato secondo la documentazione letta.
- Community piccola.

### Ruolo consigliato in un sistema informativo

Da usare come riferimento limitato per:

- calcolo XIRR;
- integrazione con Beancount;
- gestione flussi nel calcolo MWR.

Non e sufficiente come modulo completo di portfolio performance.

---

## 6.15 `RIP-Comm/sossoldi`

Repository: `https://github.com/RIP-Comm/sossoldi`  
Categoria: personal finance / net worth tracker  
Tecnologia principale: Flutter  

### Metriche community

| Metrica | Valore rilevato |
|---|---:|
| Stelle | circa 1.4k |
| Fork | circa 207 |
| Commit | circa 828 |
| Issue aperte | circa 27 |
| Pull request aperte | circa 7 |

### Funzionalita rilevanti

`Sossoldi` e un'app open source per personal finance e wealth management. Il progetto mira a sostituire spreadsheet personali e supportare mobile e desktop. Le funzioni pianificate o dichiarate includono:

- tracking spese;
- conti bancari;
- grafici, statistiche e report;
- dati locali;
- investimenti: azioni, bond, crypto, private equity;
- tasse;
- net worth in valute diverse;
- import/export;
- collegamenti PSD2;
- onboarding avanzato.

La documentazione indica pero che la fase corrente e ancora focalizzata su:

- spese;
- entrate;
- saldo conto bancario;
- statistiche base;
- dati locali.

### Valutazione rispetto ai criteri

| Criterio | Valutazione |
|---|---|
| Multivaluta | Pianificata |
| Multiportafoglio/account | Parziale/pianificata |
| Metriche di portafoglio | Non centrale oggi |
| Time based return | Non trovato |
| Value/money based return | Non trovato |
| Rebalancing | Non trovato |
| Privacy | Buona. Dati locali |
| Community | Media |

### Punti di forza

- Community superiore a molti progetti emergenti.
- Progetto italiano/europeo interessante.
- Flutter consente copertura mobile e desktop.
- Buona direzione funzionale per personal finance generale.

### Limiti

- Portfolio management ancora non maturo.
- Non risultano indicatori TWR/MWR.
- Oggi e piu vicino a personal finance/spese che a portfolio analytics.

### Ruolo consigliato in un sistema informativo

Da monitorare come progetto in evoluzione per:

- personal finance mobile-first;
- gestione spese;
- net worth futuro.

Non e adatto oggi come core per gestione investimenti e performance.

---

## 7. Progetti da considerare ma non selezionati come core

Durante la ricerca sono emersi anche altri repository minori o molto immaturi. Alcuni dichiarano funzioni interessanti, come XIRR, TWR, FIRE tracking o rebalancing, ma non sono stati inclusi nella graduatoria principale per una combinazione di:

- assenza quasi totale di stelle/fork;
- documentazione incompleta;
- stato WIP esplicito;
- focus non chiaramente centrato su portafogli personali;
- mancanza di evidenza su manutenzione o accuratezza dei calcoli.

Esempi:

- progetti personali con zero stelle e README ancora sperimentale;
- dashboard finanziarie non focalizzate sulla performance di portafoglio;
- repository orientati a backtest o trading piu che a gestione patrimoniale personale.

Questi progetti possono essere utili come materiale esplorativo, ma non dovrebbero pesare in una selezione architetturale.

---

## 8. Osservazioni trasversali

## 8.1 La completezza funzionale non coincide con la maturita

Alcuni progetti piccoli dichiarano funzioni molto avanzate:

- TWR;
- XIRR;
- FX attribution;
- benchmark alpha/beta;
- VaR/CVaR;
- Monte Carlo;
- factor models.

Questo e interessante ma rischioso. Le metriche finanziarie sono facili da nominare e difficili da implementare correttamente. Prima di usare un progetto per decisioni reali, servono:

- test su casi semplici noti;
- test con conferimenti e prelievi;
- test con dividendi e cedole;
- test con cambi valuta;
- test con split, corporate action e cost basis;
- confronto con `Portfolio Performance` o calcoli indipendenti.

## 8.2 TWR e MWR devono convivere

Molti tracker personali privilegiano una sola metrica, oppure usano metriche proprietarie come return on average investment.

Un sistema robusto deve invece avere almeno:

- TWR/TTWROR per performance della strategia;
- MWR/IRR/XIRR per esperienza reale dell'investitore;
- rendimento per asset, conto, valuta, asset class e portafoglio aggregato;
- decomposizione tra performance asset e effetto cambio;
- benchmark comparabili nella stessa valuta.

## 8.3 Multivaluta e un problema strutturale, non cosmetico

La gestione multivaluta non puo limitarsi a mostrare importi convertiti. Serve:

- valuta di transazione;
- valuta dello strumento;
- valuta del conto;
- valuta base del portafoglio;
- storico FX alla data della transazione;
- storico FX per valorizzazione;
- distinzione tra rendimento locale e rendimento da cambio;
- gestione di dividendi e cedole in valuta estera.

Tra i progetti analizzati, i piu forti su questo punto sono:

- `Portfolio Performance`;
- `Wealthfolio`;
- `Quovibe`;
- `MAERMIN`;
- `LuoDi-Nate/financial-management`;
- `GiuseppeDM98/net-worth-tracker`, soprattutto in ottica EUR.

## 8.4 Multiportafoglio significa almeno tre cose diverse

I progetti usano "multi-account" o "multi-portfolio" in modi diversi:

1. piu broker o conti titoli;
2. piu portafogli logici, ad esempio pensione, emergenza, figli, trading;
3. piu persone o household.

Per un sistema informativo personale e utile modellare tutti e tre:

- `Account`: broker, banca, wallet, conto deposito;
- `Portfolio`: obiettivo o strategia;
- `Owner`: persona, nucleo familiare, entita.

## 8.5 Il consenso community riduce il rischio, ma non garantisce accuratezza

`Firefly III` ha la community piu ampia, ma non e un motore di performance di investimento.  
`Ghostfolio` ha una community molto forte, ma va verificato sul piano TWR/MWR.  
`Quovibe` e `MAERMIN` sono funzionalmente ricchissimi, ma la community e troppo piccola per considerarli scelte mature.

La scelta corretta dipende dal ruolo:

- per core analytics: preferire accuratezza, TWR/MWR e test;
- per UI/self-host/community: preferire Ghostfolio/Wealthfolio;
- per accounting personale: Firefly III/Fava;
- per crypto: Rotki.

---

## 9. Raccomandazioni operative per costruire un sistema informativo

## 9.1 Architettura logica consigliata

Un sistema informativo personale dovrebbe essere diviso in moduli:

1. **Data ingestion**
   - import CSV broker;
   - import XML/JSON;
   - import manuale;
   - API broker opzionali;
   - market data provider;
   - FX provider.

2. **Canonical ledger**
   - transazioni normalizzate;
   - cash flow esterni;
   - corporate actions;
   - dividendi, cedole, interessi;
   - fees e tasse;
   - cost basis;
   - multi-currency nativo.

3. **Portfolio model**
   - owner;
   - account;
   - portfolio;
   - strategy;
   - asset;
   - asset class;
   - target allocation;
   - benchmark.

4. **Valuation engine**
   - prezzi storici;
   - tassi FX storici;
   - valorizzazione giornaliera;
   - saldi cash;
   - posizione per strumento, conto e valuta.

5. **Performance engine**
   - TWR/TTWROR;
   - MWR/IRR/XIRR;
   - total return;
   - income return;
   - price return;
   - FX return;
   - contribution analysis;
   - attribution per asset class e valuta.

6. **Risk and analytics engine**
   - volatilita;
   - drawdown;
   - Sharpe;
   - Sortino;
   - beta;
   - alpha;
   - tracking error;
   - information ratio;
   - rolling returns;
   - stress test;
   - scenario analysis.

7. **Rebalancing engine**
   - target allocation;
   - drift;
   - nuovi contributi;
   - soglie;
   - vincoli fiscali;
   - min trade size;
   - cash buffer;
   - no-sell rebalancing.

8. **Reporting/UI**
   - dashboard;
   - net worth;
   - portafogli;
   - performance;
   - rischi;
   - cash flow;
   - income;
   - obiettivi;
   - export.

## 9.2 Modello dati minimo

Entita minime:

- `Owner`
- `Portfolio`
- `Account`
- `Instrument`
- `AssetClass`
- `Currency`
- `Transaction`
- `CorporateAction`
- `Price`
- `FxRate`
- `HoldingSnapshot`
- `CashFlow`
- `Benchmark`
- `TargetAllocation`
- `PerformanceSeries`

Campi minimi per transazione:

- data trade;
- data settlement;
- tipo transazione;
- strumento;
- quantita;
- prezzo;
- valuta prezzo;
- importo lordo;
- commissioni;
- tasse;
- conto cash;
- conto titoli;
- FX applicato;
- note/import source;
- identificativo broker.

## 9.3 Regole operative sui rendimenti

Il sistema deve implementare almeno:

- TWR giornaliero;
- TTWROR o variante equivalente;
- XIRR per portafoglio e account;
- rendimento per periodo selezionabile;
- rendimento annualizzato;
- rendimento cumulato;
- rendimento money-weighted per obiettivo personale;
- benchmark nella stessa valuta base;
- decomposizione per flussi, prezzo, income e FX.

Regole pratiche:

- usare TWR per confrontare strategia e benchmark;
- usare MWR/XIRR per valutare esperienza dell'investitore;
- separare flussi esterni da operazioni interne;
- trattare dividendi e cedole in modo coerente;
- calcolare performance su base giornaliera quando possibile;
- salvare snapshot giornalieri per riproducibilita;
- non mescolare rendimento pre-tax e after-tax senza etichetta esplicita.

## 9.4 Regole operative sulla multivaluta

Il sistema deve:

- salvare ogni transazione nella valuta originale;
- salvare il cambio storico usato;
- distinguere valuta strumento, valuta conto e valuta base;
- calcolare performance in valuta locale e valuta base;
- separare effetto cambio da effetto prezzo;
- gestire cash residuale in ogni valuta;
- usare fonti FX tracciabili e versionate.

## 9.5 Regole operative sulla qualita dati

Prima di calcolare performance:

- riconciliare quantita strumenti;
- riconciliare saldo cash;
- controllare prezzi mancanti;
- controllare tassi FX mancanti;
- identificare transazioni duplicate;
- verificare corporate action;
- gestire strumenti delistati o illiquidi;
- salvare provenance dei dati.

## 9.6 Regole operative su sicurezza e privacy

Per dati patrimoniali personali:

- preferire local-first o self-hosted;
- cifrare backup;
- evitare invio non necessario a servizi esterni;
- separare credenziali broker dal database applicativo;
- usare token read-only;
- loggare gli accessi;
- consentire export completo;
- documentare retention e cancellazione dati.

---

## 10. Raccomandazione finale per scenari d'uso

## 10.1 Utente che vuole uno strumento pronto e rigoroso

Scelta consigliata:

1. `Portfolio Performance`
2. `Wealthfolio`

Motivo:

- supporto forte a performance;
- TWR/IRR o TWR/MWR;
- multivaluta;
- community significativa;
- adatti a investimenti personali reali.

## 10.2 Utente che vuole una web app self-hosted moderna

Scelta consigliata:

1. `Ghostfolio`
2. `Wealthfolio`
3. `Quovibe`, se si accetta rischio community

Motivo:

- interfacce moderne;
- deployment self-hosted;
- buone dashboard;
- forte attenzione a privacy e data ownership.

## 10.3 Utente con portafoglio crypto/DeFi

Scelta consigliata:

1. `Rotki`
2. integrazione con `Portfolio Performance` o `Wealthfolio` per patrimonio tradizionale

Motivo:

- Rotki e specializzato in accounting crypto e on-chain;
- i portfolio tracker tradizionali non coprono bene transazioni DeFi complesse.

## 10.4 Utente italiano con ETF, BTP e base EUR

Scelta consigliata:

1. `Portfolio Performance`
2. `GiuseppeDM98/net-worth-tracker`
3. `Wealthfolio`

Motivo:

- Portfolio Performance e maturo;
- Net Worth Tracker ha funzioni molto pertinenti per Italia, EUR, BTP e PMC;
- Wealthfolio e una soluzione moderna generalista.

## 10.5 Utente tecnico che vuole un ledger auditabile

Scelta consigliata:

1. `Beancount/Fava`
2. `hoostus/portfolio-returns` o modulo custom per XIRR
3. eventuale motore Python custom ispirato a `Foliotrack`

Motivo:

- massimo controllo e auditabilita;
- adatto a versionamento;
- richiede pero sviluppo custom per portfolio analytics completo.

## 10.6 Team che vuole costruire un nuovo sistema

Riferimenti consigliati:

- `Portfolio Performance` per correttezza del dominio finanziario;
- `Wealthfolio` per local-first e UX moderna;
- `Ghostfolio` per architettura web self-hosted e community;
- `Quovibe` per ampiezza analytics;
- `Rotki` per accounting crypto;
- `Foliotrack` per motore quantitativo/rebalancing;
- `Firefly III` per gestione budget/cash flow.

---

## 11. Due diligence tecnica consigliata prima dell'adozione

Prima di scegliere un progetto come base, eseguire una due diligence con casi numerici controllati.

### 11.1 Test minimi sui rendimenti

Creare dataset sintetici con:

- acquisto singolo senza flussi;
- acquisto con conferimento intermedio;
- prelievo intermedio;
- dividendo reinvestito;
- dividendo non reinvestito;
- vendita parziale;
- commissioni;
- tasse;
- asset in valuta estera;
- cambio favorevole e sfavorevole;
- benchmark in valuta diversa.

Verificare:

- TWR;
- IRR/XIRR;
- rendimento cumulato;
- rendimento annualizzato;
- valorizzazione cash;
- performance in valuta locale;
- performance in valuta base;
- attribution FX.

### 11.2 Test minimi su dati reali

Usare almeno:

- un ETF in EUR;
- un ETF in USD;
- un'obbligazione con cedola;
- un dividendo;
- una posizione cash;
- una crypto, se rilevante;
- due broker;
- un cambio valuta.

### 11.3 Test di manutenzione

Valutare:

- frequenza release;
- qualita issue;
- tempo di risposta;
- presenza test automatici;
- migrazioni database;
- export dati;
- backup/restore;
- licenza;
- bus factor;
- qualita documentazione.

---

## 12. Ranking finale operativo

### Tier A: candidati principali

1. `portfolio-performance/portfolio`
   - Migliore per accuratezza e maturita di performance accounting.

2. `wealthfolio/wealthfolio`
   - Migliore soluzione moderna local-first con copertura molto completa.

3. `ghostfolio/ghostfolio`
   - Migliore community e web app self-hosted, da integrare/auditare sul lato performance.

4. `rotki/rotki`
   - Migliore specialista per crypto/accounting.

### Tier B: progetti emergenti molto interessanti

5. `quovibe-web/quovibe`
   - Molto completo, ma community piccola.

6. `GiuseppeDM98/net-worth-tracker`
   - Ottimo per contesto italiano ed EUR.

7. `Maermin/MAERMIN`
   - Molto avanzato sulla carta, ma senza consenso community.

8. `investbrainapp/investbrain`
   - Buon investimento da monitorare, soprattutto per self-hosting e AI.

9. `LuoDi-Nate/financial-management`
   - Interessante per patrimonio familiare e rendimenti reali.

10. `PhDFlo/foliotrack`
   - Utile come motore Python, non come app finale.

### Tier C: complementi o progetti non core

11. `firefly-iii/firefly-iii`
   - Ottimo personal finance, non portfolio analytics.

12. `beancount/fava`
   - Ottimo ledger tecnico, richiede motore analytics aggiuntivo.

13. `hoostus/portfolio-returns`
   - Utile per XIRR/Beancount, incompleto su TWR.

14. `RIP-Comm/sossoldi`
   - Promettente ma non ancora maturo per investimenti.

15. `aybruhm/folio`
   - Funzioni interessanti, ma consenso nullo e maturita dichiaratamente limitata.

---

## 13. Fonti analizzate

### Repository principali

- `https://github.com/portfolio-performance/portfolio`
- `https://github.com/wealthfolio/wealthfolio`
- `https://github.com/ghostfolio/ghostfolio`
- `https://github.com/rotki/rotki`
- `https://github.com/quovibe-web/quovibe`
- `https://github.com/Maermin/MAERMIN`
- `https://github.com/GiuseppeDM98/net-worth-tracker`
- `https://github.com/investbrainapp/investbrain`
- `https://github.com/LuoDi-Nate/financial-management`
- `https://github.com/PhDFlo/foliotrack`
- `https://github.com/aybruhm/folio`
- `https://github.com/firefly-iii/firefly-iii`
- `https://github.com/beancount/fava`
- `https://github.com/hoostus/portfolio-returns`
- `https://github.com/RIP-Comm/sossoldi`

### Siti e documentazione ufficiale

- `https://www.portfolio-performance.info`
- `https://wealthfolio.app`
- documentazione e README ufficiali dei repository GitHub elencati.

---

## 14. Conclusione

Il panorama open source per la gestione di portafogli personali e maturo ma frammentato.

Per un sistema informativo serio, il punto critico non e solo registrare posizioni e mostrare grafici, ma implementare correttamente:

- multivaluta;
- multi-account;
- ledger transazionale;
- TWR/TTWROR;
- MWR/IRR/XIRR;
- benchmark coerenti;
- rischio;
- ribilanciamento;
- privacy;
- esportabilita dei dati.

La scelta piu robusta per un investitore personale resta `Portfolio Performance`, soprattutto se la priorita e la correttezza dei calcoli. `Wealthfolio` e il candidato piu interessante per una soluzione moderna local-first. `Ghostfolio` domina per community e architettura self-hosted. `Rotki` e indispensabile per portafogli crypto complessi.

Per costruire un nuovo sistema, la raccomandazione e non copiare un solo progetto, ma comporre le lezioni migliori:

- dominio finanziario da `Portfolio Performance`;
- UX e local-first da `Wealthfolio`;
- architettura web/community da `Ghostfolio`;
- crypto accounting da `Rotki`;
- analytics avanzata da `Quovibe` e `MAERMIN`;
- contabilita personale da `Firefly III` o `Beancount/Fava`.

