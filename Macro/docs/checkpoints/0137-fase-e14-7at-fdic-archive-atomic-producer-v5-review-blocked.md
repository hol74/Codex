# Checkpoint 0137 - E14.7at FDIC archive atomic producer v5 review blocked

Data: 2026-07-17

## Esito

La review indipendente di E14.7as restituisce `needs_changes`. Sono confermati
contract pin statico, test-runner key esterna al receipt, assenza del relativo
secret nel workspace, rifiuto totale della rete, roster hash chiusi, chain e
replay protection entro un singolo ledger e qualifica Windows.

Quattro finding restano bloccanti:

- il ledger deriva da `target.parent`: lo stesso run e' stato pubblicato due
  volte scegliendo parent differenti e ottenendo due ledger vuoti distinti;
- il ledger e' JSON non autenticato: cancellazione o rollback a un prefisso
  valido riabilitano nonce e receipt gia' consumati;
- un crash tra commit del ledger e rename del target crea stato orfano senza
  transazione pending/committed o riconciliazione;
- il lock esclusivo non ha ownership, lease o procedura sicura di recovery e
  puo' causare denial of service permanente dopo un crash.

## Decisione

Il receipt E14.7at ha SHA-256
`6a17eb17137b107bb9b0cfe98bba1b8bc884f320cf6793cbabc34579da27d29f`.
Discovery catalog, rete, execution gate e source acquisition restano chiusi.
Il prossimo passo deve introdurre uno state root deployment-pinned indipendente
dal target, un anchor anti-rollback esterno, recovery transazionale e gestione
sicura degli stale lock; seguira' nuova review indipendente.
