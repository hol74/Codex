# Piano iniziale per reimpostare il progetto Macro-Regime

Data: 2026-07-02

## Contesto

Il progetto informativo riguarda il regime macro corrente e il modo in cui modificare l'asset allocation in funzione della probabilita' dei diversi regimi. Sono gia' presenti tre documenti di base:

- `macro_regime.md`: stato dell'arte accademico e tecnico.
- `macro_regime_github.md`: analisi di progetti GitHub coerenti con il dominio.
- `macro_regime_plan.md`: primo piano applicativo per un Macro-Regime Engine in C#.

Il primo tentativo implementativo non e' stato soddisfacente. La correzione proposta e' non ripartire subito dal codice, ma costruire prima una governance piu' solida, un piano di delivery verificabile e una sequenza di milestone che separi dominio, dati, modello, allocazione, rischio e decisione umana.

## Tesi principale

Il progetto non deve nascere come "modello che decide", ma come sistema informativo governato, auditabile ed estendibile. Il regime macro deve essere trattato come informazione probabilistica ad alta utilita' ma elevata incertezza. La funzione del sistema non e' prevedere il mercato, ma ridurre l'incoerenza fra portafoglio, ambiente macro-finanziario e capacita' dell'investitore di sopportare il rischio.

## Separazione in tre prodotti

### 1. Macro Regime Information System

Misura:

- probabilita' di regime;
- driver principali;
- segnali contrari;
- incertezza;
- transizioni;
- variazione rispetto al periodo precedente.

### 2. Allocation Policy Engine

Traduce probabilita' e scenari in:

- bande allocative;
- tilt rispetto alla policy strategica;
- budget di rischio;
- vincoli di turnover;
- vincoli di costo, fiscalita' e liquidita'.

Non deve produrre mosse estreme o all-in/all-out.

### 3. Decision and Governance Layer

Registra:

- cosa si sapeva alla data della decisione;
- quale proposta e' stata generata;
- quali vincoli l'hanno modificata o bloccata;
- quale decisione umana e' stata presa;
- quali versioni di dati, feature e modello erano attive.

## Documenti da produrre

### `macro_regime_governance.md`

Deve definire:

- principi di governo del progetto;
- ruoli e responsabilita';
- gate decisionali;
- model card;
- data card;
- audit trail;
- regole di cambio modello;
- ciclo di revisione;
- regole operative per l'esecutore Codex.

### `macro_regime_delivery_plan.md`

Deve definire:

- milestone;
- sequenza di sviluppo;
- deliverable;
- Definition of Done;
- criteri di accettazione;
- rischi;
- backlog iniziale;
- ordine con cui Codex dovra' eseguire il lavoro.

## Sequenza di sviluppo proposta

### Milestone 0: Post-mortem del primo tentativo

Obiettivo: capire cosa non ha funzionato.

Output:

- elenco difetti architetturali;
- cosa salvare;
- cosa buttare;
- decisione se rifare da zero o rifattorizzare.

### Milestone 1: Domain Core in C#

Solo dominio, niente database complesso e niente UI ricca.

Componenti:

- tipi forti per date, frequenze, regime e asset class;
- modelli immutabili dove possibile;
- servizi puri e testabili;
- calcolo demo deterministico da dati seed.

Definition of Done:

- test unitari verdi;
- nessuna dipendenza da API esterne;
- un `RegimeSnapshot` riproducibile.

### Milestone 2: Baseline Rule-Based

Il primo motore deve essere interpretabile.

Output:

- `GrowthScore`;
- `InflationScore`;
- `RiskScore`;
- `MonetaryScore`;
- probabilita' fuzzy per 4-6 regimi;
- stato `UncertainTransition`;
- spiegazione dei driver.

Questo diventa il benchmark permanente. Ogni modello avanzato dovra' batterlo prima di essere promosso.

### Milestone 3: Audit Trail e As-Of Engine

Ogni run deve sapere:

- data osservazione;
- data pubblicazione;
- data disponibilita';
- versione dati;
- versione feature;
- versione modello;
- spiegazione;
- input usati;
- output prodotti.

Senza questo, i backtest macro rischiano look-ahead bias.

### Milestone 4: Allocation Proposal

Prima una policy engine prudente, non un portfolio optimizer completo.

Input:

- probabilita' regimi;
- asset allocation strategica;
- bande min/max;
- turnover massimo;
- cash minimo;
- vincoli fiscali e costi.

Output:

- proposta di tilt;
- motivazione;
- costo stimato;
- rischio stimato;
- decisione suggerita: hold, partial rebalance, full rebalance, wait.

### Milestone 5: UI e Report

Solo dopo avere dominio e run auditabile.

Dashboard minima:

- regime corrente probabilistico;
- variazione rispetto al mese precedente;
- driver principali;
- segnali contrari;
- proposta allocativa;
- vincoli che bloccano o modificano la proposta;
- audit trail.

### Milestone 6: Research Lab

Python puo' restare nel research lab, mentre C# resta il runtime applicativo.

Qui entrano:

- HMM;
- clustering;
- Markov switching;
- walk-forward;
- stress test;
- confronto contro baseline rule-based.

Nessun modello avanzato deve andare in produzione senza model card, validazione out-of-sample e confronto contro baseline.

## Gate di governance

- Design Gate: nessun codice se non esiste una decisione architetturale esplicita per la scelta rilevante.
- Data Gate: nessuna feature senza definizione, polarita', formula, frequenza e fonte.
- Model Gate: nessun modello senza model card e test di riproducibilita'.
- Allocation Gate: nessuna proposta senza vincoli IPS, turnover, costi e spiegazione.
- Release Gate: nessuna release senza run demo, test automatici e report generato.

## Architettura C# consigliata

```text
src/
  MacroRegime.Domain/
  MacroRegime.Application/
  MacroRegime.Infrastructure/
  MacroRegime.Reporting/
  MacroRegime.Web/
tests/
  MacroRegime.Domain.Tests/
  MacroRegime.Application.Tests/
research/
  regime-eval/
docs/
```

Regola: `MacroRegime.Domain` non deve conoscere EF Core, API, UI o file system. Il cuore del progetto deve poter essere testato con dati in memoria.

## Decisione chiave

Costruire prima un sistema che sa spiegare bene una diagnosi prudente e riproducibile, poi aggiungere modelli avanzati come challenger.

La prossima mossa concreta e' creare:

- `macro_regime_governance.md`;
- `macro_regime_delivery_plan.md`.

Questi due documenti dovranno essere scritti sapendo che Codex sara' l'esecutore operativo dei piani.
