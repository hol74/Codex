# Checkpoint 0069 - E14.4c label-foundation gate

Data: 2026-07-14

## Obiettivo

Trasformare i 12 dossier accettati in una proposta di fondazione label
versionata, verificare conflitti e copertura e mantenere separata la decisione
di merge dall'autorizzazione a generare candidati.

## Piano eseguito

1. congelare schema e contratto del gate legandoli agli hash della queue v5,
   dell'audit di ingestione, della tassonomia v3 e dei contratti E14 esistenti;
2. ricaricare e rivalidare i byte esatti dei 12 dossier accettati;
3. espandere ogni intervallo alla granularita' mensile per meccanismo;
4. rilevare conflitti interni e conflitti con la tassonomia v3;
5. misurare la copertura per eventi indipendenti, senza contare piu' volte lo
   stesso evento rappresentato da dossier di meccanismi diversi;
6. scrivere proposta e audit write-once senza mutare ground truth o candidati.

## Modellizzazione adottata

La chiave elementare e' `(mese, meccanismo)`. Due stati opposti sulla stessa
chiave sono un conflitto bloccante. Stati diversi nello stesso mese su
meccanismi differenti sono invece informazione valida e devono essere
preservati. Questa regola mantiene, per esempio, il Messico 1994-95 positivo
per broad-market e cross-border ma hard-negative per banking-credit.

L'aggregato mensile serve soltanto come vista. Non sostituisce le label per
meccanismo e usa la precedenza `positive`, `hard-negative`, `ambiguous`,
`unlabeled`. Gli intervalli senza dossier non sono trasformati implicitamente
in negativi.

## Esito reale

- dossier accettati rivalidati: 12/12;
- dossier positivi: 8;
- dossier hard-negative: 4;
- label mensili per meccanismo: 42;
- mesi aggregati: 24;
- mesi con stati differenti tra meccanismi: 4;
- conflitti stesso mese/meccanismo: 0;
- conflitti con tassonomia v3: 0;
- episodi positivi combinati indipendenti: 11;
- copertura positiva per broad/funding/banking/cross-border: 7/3/3/5;
- episodi hard-negative combinati indipendenti: 2;
- copertura hard-negative per meccanismo: 1/1/1/1;
- soglie hard-negative richieste: 6 totali e 2 per meccanismo.

Stato: `FOUNDATION_MERGE_READY_MORE_EVIDENCE_REQUIRED`.

La proposta e' strutturalmente valida e il merge in una nuova versione della
tassonomia e' autorizzabile. La copertura hard-negative non e' sufficiente e
la generazione di candidati resta quindi vietata.

## Identita' degli artefatti

- schema proposta SHA-256:
  `4e28c87aeaf7b868d40d12255828253204b76a460a80fa65e7b8143dc7005687`;
- contratto gate SHA-256:
  `ab5f1f82373cf00bf05765be61c3e8d8f12ec6c52f16d07b26b6961f4db7533c`;
- proposta label foundation SHA-256:
  `ab47ff9eb885402af5094d3b996241da1139683739a5bde58e68923a1c051718`;
- audit gate SHA-256:
  `e8a20cd1591782c61d162ada34ad446194723aa6e26928b7e55fd5be47aa02db`.

## Garanzie di governance

- tutti gli input sono verificati con hash esatti;
- solo dossier accettati possono entrare nella proposta;
- la ground truth v3 resta byte-identica;
- proposta e audit sono deterministici e write-once;
- gli eventi con piu' meccanismi non vengono contati come episodi indipendenti;
- outer OOS, ranking e generazione dei candidati restano chiusi.

## Verifiche

- test mirati label-foundation: 3/3 superati;
- conflitto stesso mese/meccanismo: rifiutato dai test;
- uso implicito degli unlabeled come negativi: rifiutato dai test;
- suite Python completa: 77/77 test superati;
- compilazione bytecode Python: superata;
- suite .NET completa: 240/240 test superati.

## Prossimo passo

E14.4d deve materializzare la tassonomia v4 dalla proposta validata, senza
modificare in-place la v3, e proseguire la ricerca di hard negative realmente
indipendenti. Il gate informativo dovra' essere rieseguito dopo aver raggiunto
almeno 6 eventi hard-negative totali e 2 per ciascun meccanismo; fino ad allora
non e' autorizzata alcuna generazione di candidati.
