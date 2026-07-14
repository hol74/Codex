# Consolidamento Git - artefatti runtime `.tmp`

Data di completamento: 2026-07-14.

## Esito

Il repository non versiona piu' le directory `.tmp` prodotte da smoke test,
batch, Web runtime e ASP.NET Core Data Protection. La regola `**/.tmp/**` e'
stata aggiunta alla `.gitignore` di radice e i file gia' tracciati sono stati
rimossi esclusivamente dall'indice Git.

Le copie locali restano disponibili: questo checkpoint non cancella output di
sviluppo e non modifica il comportamento dell'applicazione, che continua a
persistire le chiavi Data Protection nella propria directory temporanea.

## Ambito bonificato

L'audit ha individuato 36 file runtime tracciati nelle directory `.tmp` di
`Macro/` e della copia storica `Macro_FaseB/`, tra cui:

- dataset e manifest di smoke;
- report e run applicative;
- output dei batch e della validazione import;
- una chiave ASP.NET Core Data Protection generata in sviluppo.

Tutti questi path sono ora ignorati e non compariranno nei commit successivi.

## Confine intenzionale

La correzione e' forward-only. I file restano raggiungibili nei commit storici
che li contenevano. Una rimozione completa dalla history richiederebbe la
riscrittura dei commit e il force-push dei riferimenti condivisi: non e' stata
eseguita perche' e' un'operazione distruttiva e deve essere autorizzata in modo
esplicito.

La chiave individuata e' un artefatto di sviluppo, ma deve essere considerata
non affidabile e non riutilizzata fuori dall'ambiente locale.

## Verifiche

- nessun path `.tmp` resta tracciato nell'albero corrente;
- i file locali preesistenti sono stati preservati;
- la regola di ignore copre sia `Macro/` sia eventuali copie sorelle;
- nessuna modifica al codice applicativo o agli artefatti shadow-live.
