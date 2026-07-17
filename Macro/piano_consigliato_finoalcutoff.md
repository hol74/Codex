# Piano consigliato fino al cutoff del 31 luglio 2026

**Data di redazione:** 17 luglio 2026  
**Orizzonte:** dal 17 luglio 2026 alla disponibilità degli input relativi al cutoff del 31 luglio 2026  
**Obiettivo:** migliorare affidabilità, riproducibilità e prontezza operativa del Macro-Regime Engine senza contaminare la prima prova prospettica completa di E9.

---

## 1. Principio guida

Fino al cutoff possiamo migliorare significativamente il progetto, ma non dobbiamo modificare ciò che determina il risultato scientifico della prova prospettica.

Devono quindi restare congelati:

- baseline v1.4;
- feature utilizzate dalla baseline;
- pesi e soglie;
- tassonomia operativa;
- information cutoff;
- protocollo E9;
- criteri di preflight;
- separazione tra previsione e outcome;
- criteri di scoring e promozione.

Il lavoro utile deve concentrarsi sulla robustezza operativa: rendere il ciclo del 31 luglio difficile da eseguire in modo errato e semplice da verificare e recuperare.

---

## 2. Risultato atteso

Prima di eseguire il ciclo prospettico E9 dovranno essere disponibili:

1. una versione consolidata e identificabile del sistema;
2. un controllo automatico di readiness;
3. test di recovery e integrità più completi;
4. una prova generale offline conclusa;
5. una vista operativa di sola lettura;
6. un ambiente di esecuzione congelato;
7. un backup con ripristino verificato;
8. un runbook operativo breve e approvato;
9. una bozza progettuale della fase F che non modifichi il runtime corrente.

---

## 3. Attività prioritarie

### 3.1 Consolidare E14.7 ed E14.8

Questa è la priorità immediata. Il lavoro prodotto dalle fasi E14.7 ed E14.8 deve diventare una baseline tecnica chiaramente identificabile.

#### Attività

- verificare che tutti i nuovi file appartengano realmente alle fasi concluse;
- controllare completezza e coerenza dei checkpoint;
- verificare contratti, schemi, receipt e relativi hash;
- eseguire l'intera suite di test C#;
- eseguire l'intera suite di test Python;
- verificare la compilazione Python con `compileall`;
- controllare la documentazione generale e operativa;
- organizzare le modifiche in commit coerenti;
- creare una release candidate chiaramente identificata;
- registrare commit, fingerprint e hash degli artefatti governati.

#### Criteri di completamento

- working tree del perimetro consolidato e comprensibile;
- build senza errori;
- test C# e Python verdi;
- nessun artefatto runtime accidentale incluso nella release;
- checkpoint E14.8 coerente con gli artefatti effettivi;
- commit o release candidate identificabile in modo univoco.

#### Rischio mitigato

Arrivare al cutoff senza sapere esattamente quale versione del sistema abbia prodotto il ledger.

---

### 3.2 Creare un controllo `shadow-readiness`

È consigliata l'introduzione di un comando read-only, per esempio:

```text
shadow-readiness
```

Il comando non deve scaricare osservazioni, creare dataset, generare previsioni o scrivere ledger.

#### Controlli richiesti

- versione .NET disponibile;
- versione Python disponibile;
- disponibilità della CLI C#;
- disponibilità della CLI Python;
- presenza della variabile `FRED_API_KEY`, senza mostrarne il contenuto;
- presenza e hash del modello congelato;
- presenza e integrità dell'ultimo ledger;
- ultimo cutoff congelato;
- cutoff successivo atteso;
- assenza di ledger duplicati;
- assenza di conflitti nelle directory operative;
- percorsi configurati validi;
- permessi di lettura e scrittura;
- spazio disponibile;
- orologio e timezone coerenti con UTC;
- raggiungibilità tecnica dei provider, senza acquisizione del dataset operativo;
- assenza di outcome o forward return negli input destinati al ledger;
- corrispondenza dei fingerprint C# e Python con la release candidata.

#### Output suggerito

```text
E9 readiness: READY | NOT_READY
Next expected cutoff: 2026-07-31
Blocking findings: [...]
Warnings: [...]
```

#### Criteri di completamento

- il comando non modifica artefatti autorevoli;
- ogni controllo ha un test positivo e almeno un test negativo;
- credenziali e segreti non compaiono nell'output;
- un finding bloccante produce `NOT_READY` e un exit code non zero;
- il risultato è leggibile anche da un operatore non sviluppatore.

#### Rischio mitigato

Scoprire configurazioni, credenziali o conflitti mancanti soltanto durante il ciclo reale.

---

### 3.3 Rafforzare i test di recovery

I test correnti coprono già:

- assenza di un mese eleggibile;
- passaggio da `prepare-only` a `full`;
- fallimento durante la costruzione del dataset;
- retry idempotente;
- dati obsoleti;
- conflitto con un ledger congelato.

La copertura deve essere estesa con fault injection dopo ogni confine operativo.

#### Scenari aggiuntivi

1. fallimento durante population;
2. crash dopo population e prima del dataset;
3. fallimento durante dataset build;
4. crash dopo il dataset e prima dell'evaluation;
5. fallimento durante evaluation;
6. crash dopo evaluation e prima del preflight;
7. fallimento durante preflight;
8. crash prima della scrittura del ledger;
9. crash dopo il ledger e prima dell'indice;
10. receipt già presente;
11. ledger già presente e identico;
12. ledger già presente ma differente;
13. modifica di un file completato prima del retry;
14. spazio insufficiente;
15. permesso di scrittura negato;
16. due esecuzioni concorrenti;
17. differenza tra ora locale e UTC;
18. confine temporale tra 30 luglio, 31 luglio e 1º agosto;
19. file temporaneo o staging incompleto;
20. indice assente ma ledger valido;
21. indice alterato ma ledger valido;
22. input contenente accidentalmente outcome o forward return.

#### Proprietà da dimostrare

- nessun mese viene saltato;
- non vengono creati due ledger per lo stesso cutoff;
- un ledger esistente non viene sovrascritto;
- gli step completati e invariati non vengono ripetuti;
- un artefatto modificato blocca il recovery;
- un indice derivato può essere ricostruito;
- un fallimento non viene trasformato silenziosamente in successo.

#### Rischio mitigato

Corruzione o duplicazione del ciclo in presenza di crash e fallimenti parziali.

---

### 3.4 Eseguire una prova generale offline

La prova generale deve utilizzare una directory temporanea separata dalla root shadow ufficiale.

#### Sequenza

```text
preparazione fixture/stub
        ↓
prepare-only
        ↓
verifica receipt, log e preflight
        ↓
full
        ↓
seconda esecuzione identica
        ↓
verifica idempotenza
        ↓
alterazione controllata di una copia
        ↓
verifica fail-closed
        ↓
prova di recovery
```

#### Vincoli

- usare `.tmp` o un'altra directory dichiaratamente non autorevole;
- non scrivere nella root `data/shadow-live-2026/` ufficiale;
- non creare un ledger reale del 31 luglio;
- non usare outcome futuri;
- non modificare baseline o configurazioni congelate;
- distinguere chiaramente fixture e dati reali.

#### Verbale della prova

Il verbale deve registrare:

- ambiente utilizzato;
- commit e fingerprint;
- comandi eseguiti;
- date e orari UTC;
- exit code;
- hash degli artefatti;
- tempi di esecuzione;
- problemi incontrati;
- recovery effettuato;
- esito finale;
- eventuali modifiche richieste al runbook.

#### Rischio mitigato

Utilizzare per la prima volta la procedura completa direttamente sul ciclo prospettico reale.

---

### 3.5 Aggiungere una vista operativa read-only

La dashboard Web può essere estesa con una pagina di stato operativo che non avvii download né modifichi artefatti.

#### Informazioni da mostrare

- ultimo ledger disponibile;
- ultimo cutoff congelato;
- prossimo cutoff atteso;
- stato dell'ultimo ciclo;
- ultimo preflight;
- risultato del controllo degli hash;
- modello e versione attivi;
- fingerprint del codice;
- stato `prepared`, `frozen`, `failed` o `no-eligible-month`;
- warning di freschezza;
- link locali a receipt e log;
- esito dell'ultimo `shadow-readiness`.

#### Vincoli

- sola lettura;
- nessuna rete;
- nessun ricalcolo del modello;
- nessuna visualizzazione anticipata di outcome o score;
- nessuna modifica a ledger, manifest o receipt.

#### Rischio mitigato

Errori operativi dovuti alla consultazione manuale di numerosi file e directory.

---

### 3.6 Congelare l'ambiente di esecuzione

Prima del cutoff deve essere prodotto un manifest dell'ambiente.

#### Informazioni da registrare

- versione esatta del .NET SDK;
- versione Python;
- versione delle dipendenze Python;
- versioni delle dipendenze NuGet;
- sistema operativo;
- architettura del sistema;
- timezone;
- commit Git;
- hash della baseline v1.4;
- hash del model config;
- hash della feature set;
- hash del protocollo E9;
- fingerprint del codice C#;
- fingerprint del codice Python;
- comando `prepare-only` previsto;
- comando `full` previsto;
- root operativa prevista.

#### Regola sulle dipendenze

È opportuno bloccare le versioni, ma non aggiornarle indiscriminatamente vicino al cutoff. Ogni variazione deve essere seguita dall'intera pipeline CI e da una nuova prova generale.

#### Rischio mitigato

Ottenere risultati diversi perché l'ambiente cambia tra rehearsal e ciclo reale.

---

### 3.7 Provare backup e ripristino

Il backup deve essere verificato tramite un ripristino reale in una posizione isolata.

#### Procedura

1. copiare la root shadow in un'area isolata;
2. registrare hash e numero degli artefatti;
3. ripristinare la copia in una seconda directory;
4. verificare gli hash dopo il ripristino;
5. ricostruire `ShadowIndex` dai ledger;
6. eseguire `shadow-readiness` sulla copia;
7. verificare che non venga creato alcun ledger nuovo;
8. documentare tempi e risultato.

#### Artefatti da proteggere

- dati sorgente;
- configurazioni congelate;
- preflight;
- ledger;
- score, quando disponibili;
- GateDecision;
- receipt;
- checkpoint;
- manifest e fingerprint.

#### Rischio mitigato

Scoprire che il backup è incompleto o inutilizzabile soltanto dopo un incidente.

---

### 3.8 Preparare il runbook operativo di luglio

Il manuale `istructions.md` contiene la procedura generale. Per il ciclo reale serve anche una checklist breve e specifica.

#### Checklist proposta

- [ ] Il mese di luglio è chiuso.
- [ ] Gli input richiesti sono effettivamente disponibili.
- [ ] Il commit corrisponde alla release candidate approvata.
- [ ] I fingerprint corrispondono al manifest congelato.
- [ ] La pipeline CI è verde.
- [ ] I test locali richiesti sono verdi.
- [ ] La credenziale FRED è disponibile e non esposta.
- [ ] Il backup precedente è completato.
- [ ] `shadow-readiness` restituisce `READY`.
- [ ] Non esiste già un ledger per il cutoff.
- [ ] `prepare-only` è stato eseguito.
- [ ] La receipt `prepare-only` è stata revisionata.
- [ ] Il preflight è stato accettato.
- [ ] Non sono presenti outcome o forward return.
- [ ] È stata registrata l'autorizzazione umana al `full`.
- [ ] Il comando `full` è stato eseguito.
- [ ] Il ledger write-once è presente.
- [ ] L'indice è stato ricostruito.
- [ ] Ledger, receipt e indice sono stati verificati.
- [ ] Lo scoring è stato rinviato al momento previsto.

#### Rischio mitigato

Omissioni o decisioni improvvisate durante il ciclo reale.

---

### 3.9 Preparare la fase F soltanto sul piano progettuale

Il periodo può essere usato anche per preparare la fase F, purché il lavoro non modifichi il runtime operativo o il protocollo E9.

#### Attività consentite

- definire il contratto dell'ottimizzatore;
- formalizzare bande IPS e vincoli;
- definire il turnover massimo;
- definire costi e fiscalità rappresentabili;
- definire la penalità per portafogli estremi;
- definire lo shrinkage degli expected return;
- formalizzare gli stress storici;
- formalizzare gli stress fattoriali;
- definire il reverse stress test;
- individuare fonti per i periodi 1973-74 e 2000-02;
- definire metriche e criteri di accettazione;
- preparare ADR, Data Gate, Allocation Gate e test plan.

#### Attività non ancora consentite

- attivare un ottimizzatore nel runtime operativo;
- modificare la proposta allocativa corrente;
- scegliere parametri usando il risultato di luglio;
- generare ordini;
- sostituire l'IPS;
- avviare la fase F prima della chiusura formale della fase E.

---

## 4. Attività vietate prima del cutoff

Non devono essere eseguite le seguenti attività:

- modificare baseline v1.4;
- modificare feature, pesi o soglie;
- cambiare la tassonomia operativa;
- cambiare retroattivamente il protocollo E9;
- scegliere configurazioni dopo aver visto i dati di luglio;
- usare dati pubblicati dopo il cutoff come se fossero disponibili prima;
- acquisire outcome futuri nel percorso della previsione;
- anticipare lo scoring del ledger di giugno;
- creare anticipatamente il ledger del 31 luglio;
- creare due ledger per lo stesso cutoff;
- sovrascrivere preflight, ledger o receipt;
- cancellare lo stato del ciclo per aggirare un conflitto;
- promuovere challenger già respinti senza un nuovo protocollo;
- attivare il provisioning progettato in E14.8;
- scegliere provider o creare credenziali per l'autorità esterna senza una nuova fase autorizzata;
- attivare rete o pubblicazione downstream non autorizzata;
- implementare nel percorso operativo l'ottimizzazione della fase F;
- trasformare una proposta allocativa in ordine automatico.

---

## 5. Sequenza temporale raccomandata

Le date sono indicative e possono essere adattate mantenendo l'ordine logico.

| Periodo | Attività principale | Deliverable |
|---|---|---|
| 17-18 luglio | Consolidamento E14.7/E14.8 | Release candidate e manifest iniziale |
| 19-21 luglio | `shadow-readiness` | Comando read-only e test |
| 19-23 luglio | Test avversariali e recovery | Suite estesa verde |
| 22-24 luglio | Vista operativa read-only | Pagina o report di stato |
| 24-25 luglio | Prova generale offline | Verbale di rehearsal |
| 25-26 luglio | Backup e ripristino | Evidenza del restore riuscito |
| 26-27 luglio | Freeze ambiente | Manifest definitivo delle versioni |
| 28 luglio | Release candidate finale | Commit, fingerprint e CI verdi |
| 29-30 luglio | Revisione del runbook | Checklist approvata |
| 31 luglio | Nessuna esecuzione anticipata | Attesa della chiusura del mese |
| Dopo la chiusura e la disponibilità degli input | `prepare-only` | Preflight e receipt da revisionare |
| Dopo review positiva | `full` | Ledger prospettico congelato |

Il comando `full` non deve essere eseguito automaticamente allo scoccare della mezzanotte. Occorre attendere la disponibilità effettiva degli input richiesti.

---

## 6. Ordine di priorità

| Priorità | Attività | Valore principale |
|---:|---|---|
| 1 | Consolidamento E14.7/E14.8 | Versione identificabile e riproducibile |
| 2 | `shadow-readiness` | Controllo preventivo automatizzato |
| 3 | Test avversariali e recovery | Riduzione del rischio di ciclo corrotto |
| 4 | Rehearsal offline completo | Procedura provata end-to-end |
| 5 | Vista operativa read-only | Diagnostica semplice e trasparente |
| 6 | Freeze dell'ambiente | Esecuzione riproducibile |
| 7 | Backup/restore e runbook | Prontezza operativa |
| 8 | Disegno della fase F | Avanzamento senza contaminare E9 |

---

## 7. Incremento consigliato

Il prossimo incremento raccomandato è:

> **E9 Readiness Hardening** — consolidamento del workspace, comando `shadow-readiness`, test di recovery estesi e prova generale offline.

### Perimetro incluso

- consolidamento della versione corrente;
- readiness read-only;
- fault injection;
- recovery;
- rehearsal offline;
- manifest dell'ambiente;
- runbook specifico per luglio.

### Perimetro escluso

- modifica del modello;
- modifica dei dati congelati;
- modifica delle soglie;
- acquisizione anticipata degli input di luglio;
- produzione anticipata del ledger;
- scoring anticipato;
- provisioning E14.8;
- implementazione operativa della fase F.

### Definition of Done

L'incremento è concluso quando:

1. la release candidate è identificata;
2. CI e test locali sono verdi;
3. `shadow-readiness` restituisce risultati deterministici e non espone segreti;
4. tutti gli scenari di recovery previsti sono testati;
5. il rehearsal offline è completato;
6. backup e restore sono verificati;
7. ambiente e fingerprint sono congelati;
8. il runbook di luglio è approvato;
9. nessun artefatto prospettico reale è stato creato anticipatamente;
10. baseline v1.4 e protocollo E9 risultano invariati.

---

## 8. Sequenza operativa dopo il cutoff

Quando luglio sarà chiuso e gli input saranno disponibili:

```text
verifica release e fingerprint
        ↓
shadow-readiness
        ↓
prepare-only
        ↓
review di receipt, log, hash e preflight
        ↓
autorizzazione umana
        ↓
full
        ↓
verifica ledger e indice
        ↓
backup
        ↓
attesa della maturazione dell'outcome
        ↓
shadow-score
        ↓
GateDecision umano
```

---

## 9. Riferimenti

- [Descrizione generale del progetto](readme.md)
- [Manuale operativo](istructions.md)
- [Piano operativo completo](docs/0001-piano-operativo.md)
- [Governance](docs/planning/0003-governance-progetto.md)
- [Release E9.2](docs/releases/macro-regime-e9.2.md)
- [Checkpoint E9.2](docs/checkpoints/0044-fase-e9-shadow-operations-incremento2-done.md)
- [Checkpoint finale E14.8](docs/checkpoints/0145-fase-e14-8c-provisioning-design-review-accepted.md)
- [README del laboratorio](research/regime-eval/README.md)

---

## Conclusione

Il periodo fino al cutoff deve essere utilizzato per migliorare la qualità dell'esecuzione, non per ottimizzare il risultato atteso. La prova prospettica acquista valore proprio perché modello, regole e criteri restano congelati prima della disponibilità degli input e degli outcome.

Il progetto sarà realmente pronto quando sarà possibile dimostrare non soltanto che il comando funziona, ma anche che:

- l'ambiente è identificabile;
- gli input sono corretti;
- gli errori vengono bloccati;
- i retry sono sicuri;
- gli artefatti non vengono sovrascritti;
- il ciclo può essere recuperato;
- la decisione finale rimane umana e auditabile.
