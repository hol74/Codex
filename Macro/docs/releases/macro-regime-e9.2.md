# Release Macro-Regime E9.2

Data: 2026-07-14.

Tag previsto: `macro-regime-e9.2`.

## Contenuto

Questa release consolida il sistema fino alla Fase E9.2:

- orchestratore mensile end-to-end `shadow-operations`;
- modalita' `prepare-only` e `full`;
- selezione sequenziale del cutoff senza salti;
- state machine atomica con recovery dal primo step incompleto;
- preflight, ledger e receipt write-once;
- log, exit code e SHA-256 degli artifact operativi;
- bonifica degli artifact runtime `.tmp` dal tracciamento Git;
- documentazione organica di architettura, letteratura e glossario;
- CI GitHub per build/test .NET e test del laboratorio Python.

## Stato operativo

La release completa lo sviluppo tecnico E9.2, ma non chiude la validazione
prospettica E9. Il primo ciclo `full` eleggibile resta quello del cutoff
2026-07-31, da eseguire soltanto dopo la chiusura del mese e la disponibilita'
degli input. La baseline v1.4 resta congelata e nessuno scoring anticipato e'
ammesso.

## Artifact e compatibilita'

- runtime C#: .NET 10;
- research lab: Python 3.12 o successivo;
- persistenza: JSON e Markdown file-based;
- rete: confinata agli adapter Infrastructure invocati dalla CLI;
- database: non richiesto;
- trading automatico: non presente.

## Verifica di release

La pipeline CI esegue:

1. restore della solution;
2. build Release senza warning ammessi implicitamente dal compilatore;
3. tutti i test C#;
4. `compileall` del laboratorio Python;
5. tutti i test Python con `unittest`.

Verifica locale della release:

- build Release: 0 warning, 0 errori;
- test C#: 240 superati;
- `compileall`: superato;
- test Python: 25 superati.

## Limiti noti

- una sola osservazione shadow-live, non ancora scorable;
- dataset NBER OOS con soli due mesi positivi;
- fonti finanziarie giornaliere non interamente vintage;
- Yahoo come adapter pragmatico e sostituibile;
- ottimizzazione allocativa e stress test della Fase F non ancora implementati.
