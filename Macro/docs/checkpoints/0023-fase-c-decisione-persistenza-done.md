# Macro Regime - Fase C: Decisione persistenza - Done

Data: 2026-07-10

## Scopo della fase

La Fase C del piano operativo (`docs/0001-piano-operativo.md`) richiedeva una decisione architetturale esplicita sulla persistenza locale:

1. valutare se e quando introdurre un database locale;
2. in caso positivo, limitarlo a un adapter Infrastructure;
3. in caso negativo, formalizzare il file-based come scelta stabile.

## Decisione presa

E' stata scelta la terza direzione: persistenza locale file-based stabile per la prossima fase del progetto, senza introdurre ora SQLite, EF Core o altri database.

La decisione e' formalizzata in:

- `docs/adr/0003-persistenza-locale-file-based.md`.

## Motivazione

Dopo le Fasi A e B il sistema copre gia' i bisogni informativi locali principali usando artifact file-based:

- run JSON con schema versionato;
- manifest locale delle run;
- dettaglio storico letto da disco;
- confronto tra run;
- report markdown;
- diagnostica import/config;
- batch multi-data.

Introdurre subito un database aggiungerebbe migrazioni, mapping relazionale e complessita' infrastrutturale senza un requisito attuale abbastanza forte. La priorita' resta proteggere Domain e Application, mantenere audit trail leggibile e proseguire verso provider dati e research lab con un runtime locale semplice.

## Alternative considerate

### Database locale immediato

Scartato per ora. SQLite/EF Core resta tecnicamente compatibile con l'architettura solo come adapter Infrastructure, ma introdurlo ora sarebbe prematuro rispetto alle necessita' correnti.

### File-based stabile

Scelto. La persistenza JSON/markdown resta source of truth locale per run, manifest, report, diagnostica e input.

### Ibrido file-based + database derivato

Non scelto ora. Potra' essere rivalutato se serviranno query storiche interattive, dataset piu' grandi o indici derivati difficili da gestire sul manifest.

## Trigger futuri per rivalutare SQLite/EF Core

La decisione dovra' essere riaperta con una nuova ADR se emergeranno:

- query storiche multi-run non gestibili bene dal manifest;
- dataset locali molto piu' grandi;
- relazioni persistenti tra run, input, model version, feature set e decision record;
- necessita' di concorrenza o locking robusto;
- decision record persistenti con workflow dedicato;
- conservazione strutturata di dati storici importati oltre i file sorgente.

## Verifiche eseguite

Verifica documentale:

- ADR 0003 creata;
- piano operativo aggiornato;
- riepilogo lavoro svolto aggiornato;
- nessun codice applicativo modificato per la Fase C.

Gate architetturali:

- nessun database introdotto;
- nessun package EF Core introdotto;
- Domain e Application non modificati;
- persistenza concreta confermata come responsabilita' Infrastructure/file adapter.

## Cosa resta fuori

- Implementazione SQLite/EF Core;
- migrazioni database;
- indici relazionali;
- refactoring dei run store;
- export JSON dedicato della diagnostica;
- decision record persistenti.

## Valutazione

Fase C completata come decisione architetturale. Il progetto prosegue con persistenza locale file-based, e l'introduzione di un database resta vincolata a trigger espliciti e a una futura ADR dedicata.

La prossima fase consigliata e' la Fase D: provider dati esterni, a partire da adapter isolati per FRED/ALFRED dietro le porte applicative.

