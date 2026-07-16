# Checkpoint 0104 - E14.7m remediation vintage bloccata

Data: 2026-07-16

## Esito

La remediation mirata e' stata eseguita come discovery metadata-only, senza
scaricare osservazioni o generare un catalogo di acquisizione. Gli hash di
E14.7l, snapshot, acquisition audit, scope, fitness plan e manifest E14.7i sono
stati verificati.

- H.8: 1.042 release post-2005 fino al 2025 e tutti gli 88 mesi richiesti prima
  del taper tantrum sono individuabili tramite locator datati.
- H.10: 910 release post-2005, ma soltanto 57 degli 88 mesi richiesti prima del
  taper tantrum; mancano 31 mesi consecutivi da 2006-06 a 2008-12.
- FDIC: i QBP quarter-specific sono individuabili, ma al cutoff 2025-12-31
  l'ultimo trimestre eleggibile e' 2025Q3. Q4 2025 non puo' essere trattato come
  disponibile al quarter-end.

L'audit immutabile ha SHA-256
`bf64490b65527077b829190224e0af5144268283e36a052b5bec40963ac2cdd4`.

## Decisione

La remediation non puo' soddisfare le policy E14.7l invariate. Request catalog,
acquisizione, trasformazione, candidati, evaluation e outer OOS restano chiusi.
Il prossimo passo ammesso e' una proposta separatamente revisionata che
sostituisca H.10 con una fonte event-time dotata di almeno 60 mesi pre-taper e
definisca la copertura FDIC tramite vintage reale di pubblicazione.
