# Checkpoint 0086 - E14.6d candidate protocol v2 ready

Data: 2026-07-15

## Obiettivo

Congelare un protocollo di candidate generation v2 sui 28 ingressi readiness,
senza ricalcolare gli ID e senza materializzare, trasformare o fittare
candidati.

## Identita' e grammatica

Il protocollo contiene esattamente i 28 ID del roster E14.6c nello stesso
ordine:

| Meccanismo | Candidati | Profili |
| --- | ---: | ---: |
| banking-credit | 4 | 1 |
| broad-market-repricing | 16 | 4 |
| cross-border-growth | 4 | 1 |
| funding-liquidity | 4 | 1 |

Ogni profilo ha le quattro combinazioni di persistenza `(1,1)`, `(1,2)`,
`(2,1)` e `(2,2)` con hysteresis obbligatoria. I 16 ID broad restano identici,
i 12 ID v2 sono copiati dal roster e i 24 ID v1 ritirati non possono ricomparire.

Il generatore del prossimo step non potra' modificare ID, profilo, binding,
eligibility o persistenza. L'unica transizione consentita e' da
`readiness-planned-not-generated-not-fit` a `research-generated-not-fit`.

## Policy congelate

- soglie q80/q90/q95 selezionate esclusivamente sul training LOEO inner;
- almeno 60 osservazioni non-missing;
- `availableOn` entro la fine della scoring month e as-of semantics obbligatorie;
- nessun carry sul calendar slot missing o oltre il confine metodologico;
- nessuna imputazione a zero o fusione cross-mechanism;
- sensitivity funding 2019 identica alla readiness policy;
- confronto hash dei futuri snapshot prima dell'evaluation;
- strict vintage falso e promozione operativa vietata.

## Esito

Stato:
`RESEARCH_CANDIDATE_PROTOCOL_V2_READY_MANIFEST_GENERATION_AUTHORIZED_FITTING_CLOSED`.

- protocollo v2 congelato: si';
- materializzazione manifest v2: autorizzata come prossimo step;
- manifest gia' generato: no;
- trasformazione, fitting, evaluation e ranking: no;
- composizione, outer OOS e promozione: no;
- outer feature row usate: 0.

Protocollo SHA-256:
`edf3cbeb9bb77d502109fc25ccdb463d9f39f7496f7c24039468c70e7c379955`.

Audit SHA-256:
`565ccb0d6f7d28443d650f705c0e7f8f14656b2b1b8986c2a90a13fe4625a3e8`.

## Verifiche

- test mirati E14.6d: 3/3;
- suite Python completa: 126/126;
- determinismo e write-once verificati;
- mutazione del roster e riapertura del fitting respinte;
- tutti i feature binding risolti esattamente sulla foundation v2.

## Prossimo passo

E14.6e deve materializzare il candidate manifest v2 copiando i 28 ingressi del
roster verbatim e cambiando soltanto il lifecycle. Nessuna trasformazione,
evaluation o selezione e' autorizzata.
