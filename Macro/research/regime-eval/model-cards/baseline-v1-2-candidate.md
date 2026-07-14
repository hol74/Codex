# Model card - Baseline v1.2 candidate

Data: 2026-07-13.

## Stato

Respinta al preflight train-only. L'outer OOS non e' stato aperto per report,
audit o confronto NBER.

## Modifica valutata

La candidate conserva le feature temporali v1.1 e sostituisce raw score e
confidence con:

- distanza media da cinque archetipi macro preregistrati;
- potenza 2 applicata al fit per aumentare la separazione;
- confidence composta da fit assoluto e margine fra i primi due archetipi;
- penalita' gia' esistenti per dati mancanti e segnali divergenti.

La configurazione congelata e' `models/baseline-v1-2-preregistered.json`. Demo,
v1.0 e v1.1 mantengono il comportamento precedente.

## Preflight

Su ciascuno dei 6 outer train, gli ultimi due anni sono stati usati come inner
validation. Nessuna ricerca di parametri e' stata eseguita; tutte le righe outer
test sono state escluse dai diagnostici e dai gate.

Risultato: 0 fold eleggibili su 6, minimo richiesto 4.

- fold 1-3: concentrazione primaria e diversita' insufficienti; saturazione di
  `RISK_APPETITE`;
- fold 4: saturazione di `GROWTH_MOM`;
- fold 5: saturazione di `GROWTH_MOM` e 60% `UncertainTransition`;
- fold 6: solo 2 regimi primari e Reflation al 92%.

## Decisione e limite del protocollo

La candidate non e' promossa e la configurazione non viene modificata post-hoc.
Il preflight ha inoltre mostrato un difetto strutturale del gate v1: richiedere
diversita' minima e assenza di concentrazione in ogni singola finestra biennale
confonde robustezza del modello e naturale persistenza dei regimi. Il prossimo
incremento deve preregistrare un gate v2 che separi:

1. integrita' delle feature, valutata su validation interne aggregate;
2. copertura multiregime, valutata su date validation uniche aggregate;
3. robustezza operativa/confidence, mantenuta per fold.

Questa e' una correzione della struttura del protocollo, non un abbassamento
delle soglie osservando l'OOS. La v1.2 resta un risultato negativo conservato.

## Riesame con train gate v2

Il gate v2 e' stato preregistrato mantenendo tutte le soglie numeriche e
separando gli ambiti. Sulle 84 date inner-validation uniche:

- copertura superata: 4 regimi e dominante al 57,14%;
- operativita' superata: 5 fold su 6 entro il limite di incertezza;
- integrita' fallita: `RISK_APPETITE` al bordo nel 27,38%, limite 25%.

La decisione non cambia: v1.2 non eleggibile e OOS non aperto. Il prossimo
modello dovra' correggere la normalizzazione VIX in una versione nuova, senza
alterare retroattivamente la v1.2.
