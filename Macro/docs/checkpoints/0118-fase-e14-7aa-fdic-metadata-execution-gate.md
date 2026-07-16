# Checkpoint 0118 - E14.7aa FDIC metadata execution gate

Data: 2026-07-16

## Esito

E14.7aa ha superato il gate locale che autorizza separatamente una sola
raccolta metadata-only delle 79 prove FDIC. Il gate non ha effettuato rete e ha
congelato i seguenti limiti operativi:

- solo HTTPS verso `www.fdic.gov`;
- massimo 158 richieste logiche e 316 tentativi fisici;
- massimo 3 redirect, tutti sullo stesso host consentito;
- timeout 30 secondi e massimo 8 MiB per risposta;
- content type ammessi: `text/html` e `application/pdf`;
- massimo 2 tentativi per richiesta, retry solo per status transitori congelati;
- nessun retry su redirect off-provider, content type errato o oversize;
- pubblicazione soltanto a 79/79 righe validate, con staging e singolo rename
  atomico; ledger parziali e overwrite sono vietati.

Il contratto del gate ha SHA-256
`fcdf1bdf709b2019552219a3c1f080bfb1c66133be183a2475c70addd14060f7`.
L'audit ha SHA-256
`e75ed90a4e9b3a04af2ad8606662d26d1724b67e09277ee666f130e935605410`.

I 7 test mirati e l'intera suite di 273 test Python sono verdi. Il protocollo
del gate registra zero richieste, zero righe, zero raw artifact e zero cataloghi.

## Decisione

E' autorizzata esclusivamente l'esecuzione separata della raccolta metadata FDIC
entro i limiti E14.7aa. Catalogo v3, snapshot v2, payload event-time,
acquisizione completa, feature, candidati, evaluation e outer OOS restano
vietati. Il prossimo passo deve implementare ed eseguire il collector contro
gli artifact esatti del gate, pubblicando soltanto un ledger completo 79/79 o
un audit di fallimento senza ledger parziale.
