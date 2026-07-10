# ADR 0003: Persistenza locale file-based

Data: 2026-07-10

Status: Accepted

## Contesto

Il Macro-Regime Engine ha raggiunto una prima forma informativa locale dopo le Fasi A e B:

- run JSON persistite con schema versionato;
- manifest locale delle run;
- lettura del dettaglio run senza riesecuzione;
- confronto tra run salvate;
- report markdown;
- diagnostica import/config;
- batch multi-data locale.

Il piano operativo prevedeva in Fase C di decidere se introdurre un database locale o formalizzare il file-based come scelta di lungo periodo iniziale.

Il piano originario citava una possibile persistenza EF Core, ma il restart architetturale ha protetto intenzionalmente il dominio da database, filesystem, web framework e clock di sistema. Le Fasi A e B hanno dimostrato che, per lo stato attuale, i bisogni principali sono coperti senza introdurre un database.

## Decisione

La decisione e':

> mantenere la persistenza locale file-based come scelta stabile per la prossima fase del progetto, senza introdurre ora SQLite, EF Core o altri database.

Il file-based non e' piu' solo una scorciatoia temporanea della prima release: diventa l'adapter persistente ufficiale per il sistema informativo locale finche' i requisiti non richiederanno query storiche piu' ricche, concorrenza, dataset piu' grandi o relazioni persistenti difficili da governare su file.

## Ambito della decisione

Restano file-based:

- run JSON;
- manifest JSON;
- report markdown;
- report diagnostici import/config;
- input locali JSON;
- batch locale multi-data.

Restano vietati nei layer core:

- riferimenti EF Core;
- DbContext;
- SQLite;
- database provider;
- dipendenze Infrastructure dentro Domain o Application.

## Alternative considerate

### 1. Introdurre subito SQLite/EF Core

Vantaggi:

- query storiche piu' semplici;
- vincoli relazionali;
- migliore gestione di dataset ampi;
- percorso naturale verso analytics piu' avanzati.

Svantaggi:

- complessita' prematura;
- migrazioni e schema management;
- rischio di spostare logica in Infrastructure;
- possibile erosione dei confini Domain/Application;
- nessun requisito attuale richiede davvero query relazionali.

Esito: non scelta.

### 2. File-based stabile con trigger di rivalutazione

Vantaggi:

- coerente con il restart architetturale;
- mantiene il runtime locale semplice e ispezionabile;
- preserva audit trail leggibile;
- riduce accoppiamento infrastrutturale;
- valorizza run JSON v2, manifest, diagnostica e batch gia' implementati.

Svantaggi:

- query storiche complesse richiedono scansione file o indici aggiuntivi;
- nessun vincolo relazionale nativo;
- dataset molto grandi potrebbero diventare scomodi;
- concorrenza e locking restano limitati.

Esito: scelta.

### 3. Approccio ibrido immediato

Vantaggi:

- file-based come source of truth, database come indice derivato;
- query piu' rapide senza abbandonare artifact leggibili.

Svantaggi:

- doppia fonte da sincronizzare;
- rischio di divergenza;
- maggiore superficie di test;
- non necessario finche' lo storico resta locale e contenuto.

Esito: non scelta per ora; potra' essere rivalutata in futuro.

## Trigger per rivalutare il database

Una nuova ADR dovra' rivalutare SQLite/EF Core se si verifica almeno una di queste condizioni:

1. servono query storiche interattive su molte date, feature e allocation;
2. il numero di run o la dimensione dei dataset rende lenta la scansione file;
3. servono relazioni persistenti tra run, input, model version, feature set e decision record;
4. serve confronto multi-run avanzato non gestibile bene dal manifest;
5. serve concorrenza di scrittura o accesso multi-processo robusto;
6. serve conservare dati importati storici oltre i file sorgente locali;
7. viene introdotto un vero workflow di decision record persistente.

## Conseguenze positive

- Il Domain resta puro.
- Application continua a dipendere solo da porte.
- Infrastructure resta l'unico layer che conosce filesystem e formati concreti.
- Gli artifact restano leggibili, versionabili e facili da ispezionare.
- Le prossime fasi possono concentrarsi su provider dati, research lab e robustezza informativa senza schema database prematuro.

## Conseguenze negative

- Alcune funzionalita' storiche richiederanno indici file-based o scansioni.
- Il manifest potrebbe dover evolvere per supportare query piu' ricche.
- Le validazioni cross-file restano applicative, non relazionali.
- Un futuro passaggio a database richiedera' mapping e migrazione dedicati.

## Implicazioni operative

Per le prossime fasi:

- non aggiungere package EF Core;
- non creare progetti database;
- non introdurre migrazioni;
- continuare a versionare gli schemi JSON;
- preferire manifest o indici file-based derivati quando serve una consultazione piu' veloce;
- documentare ogni nuova persistenza concreta come adapter Infrastructure.

## Test di accettazione

La decisione e' rispettata se:

- `MacroRegime.Domain` non ha dipendenze da database o filesystem;
- `MacroRegime.Application` non referenzia Infrastructure o provider database;
- non ci sono `DbContext`, migrazioni o package EF Core nella solution;
- run, report, manifest e diagnostica restano leggibili da file locali;
- ogni futura esigenza database passa da una nuova ADR.

