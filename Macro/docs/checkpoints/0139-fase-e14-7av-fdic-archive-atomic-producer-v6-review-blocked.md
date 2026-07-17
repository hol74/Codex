# Checkpoint 0139 - E14.7av FDIC archive atomic producer v6 review blocked

Data: 2026-07-17

## Esito

La review indipendente restituisce `needs_changes`. V6 blocca il replay
cross-parent entro un checkout, rileva rollback unilaterale, recupera il crash
dopo la pubblicazione interna e conserva correttamente i lock live.

Restano sette finding: root derivato da una location copiabile; ledger e anchor
nello stesso dominio locale e rollbackabili insieme; crash non recuperabile
dopo il rename finale; target cross-volume che consuma lo stato prima di
fallire; marker anchor unsigned e symlink-following; directory rename non
fsync; ownership del lock ambigua in caso di PID reuse.

## Decisione

Il receipt E14.7av ha SHA-256
`fbcc2cac80c5349e4c50d97910696668057b43a22c213040547d0dc222a33a07`.
Rete e downstream restano chiusi. Il prossimo passo deve usare identita' e
anchor monotono esterni al workspace, correggere la finestra post-rename,
preflight cross-volume, no-follow/autenticazione dei marker, directory fsync e
lock legati all'identita' di avvio del processo; seguira' nuova review.
