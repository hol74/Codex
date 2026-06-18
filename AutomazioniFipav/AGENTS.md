# AGENTS.md

Questo progetto supporta le attivita del responsabile gare del Comitato Territoriale FIPAV di Ancona. Le istruzioni qui sotto valgono per ogni agente o assistente che lavora in questa cartella.

## Obiettivo

Aiutare a gestire in modo ordinato, verificabile e ripetibile le attivita legate a:

- calendari e spostamenti gara;
- comunicazioni con societa, arbitri, uffici federali e organismi territoriali;
- raccolta, controllo e archiviazione di documenti;
- promemoria, scadenze e monitoraggi;
- produzione di bozze, riepiloghi, verbali, elenchi e report.

## Lingua e tono

- Usa l'italiano come lingua predefinita.
- Mantieni un tono istituzionale, chiaro e collaborativo.
- Per email, comunicati e messaggi ufficiali usa formule cortesi, concise e prive di ambiguita.
- Evita espressioni informali quando il testo e destinato a societa, tesserati, arbitri o organismi federali.
- Quando prepari bozze, distingui sempre tra testo pronto da inviare e note interne.

## Principi operativi

- Prima di proporre o modificare una procedura, cerca di capire il flusso reale di lavoro gia esistente.
- Non inventare dati, scadenze, normative, recapiti, risultati, calendari o decisioni ufficiali.
- Quando un dato puo cambiare nel tempo, verifica la fonte piu aggiornata o segnala chiaramente che serve conferma.
- Evidenzia sempre eventuali assunzioni, dubbi o informazioni mancanti.
- Preferisci output riutilizzabili: tabelle, checklist, modelli, procedure passo-passo e template.
- Mantieni separati fatti verificati, ipotesi, proposte operative e decisioni gia prese.

## Fonti e verifiche

- Considera fonti primarie, quando disponibili:
  - documenti ufficiali FIPAV;
  - comunicati del Comitato Territoriale di Ancona;
  - comunicati del Comitato Regionale Marche;
  - regolamenti federali;
  - portali gestionali federali e documenti ricevuti dagli uffici competenti.
- Quando usi informazioni da web o documenti esterni, riporta la fonte e la data di consultazione.
- Per regolamenti, indizioni, calendari e scadenze, non affidarti alla memoria: verifica sempre la versione corrente.
- Se ci sono versioni diverse dello stesso documento, segnala la differenza e chiedi quale faccia fede.

## Privacy e dati personali

- Tratta con attenzione dati personali di atleti, dirigenti, arbitri, allenatori e societa.
- Non includere dati sensibili o non necessari in bozze, report o file di lavoro.
- Quando possibile, usa identificativi minimi: societa, codice gara, categoria, data, impianto.
- Non pubblicare recapiti personali, documenti sanitari, eta di minori o informazioni riservate se non strettamente necessario e autorizzato.
- Prima di preparare comunicazioni massive, controlla destinatari, copie conoscenza e allegati.

## Convenzioni sui file

- Usa nomi file chiari e ordinabili.
- Preferisci il formato:

```text
YYYY-MM-DD_area_argomento_versione.ext
```

Esempi:

```text
2026-09-15_gare_spostamenti_v1.xlsx
2026-10-02_comunicazione_societa_under16_v1.md
2026-11-08_report_omologazioni_v1.pdf
```

- Usa `bozza` nel nome file quando un documento non e definitivo.
- Usa `definitivo` solo quando il contenuto e stato controllato e approvato.
- Non sovrascrivere documenti ufficiali originali: crea copie di lavoro quando serve elaborarli.

## Struttura consigliata del progetto

La struttura dei file operativi deve essere suddivisa per stagione sportiva. Usa sempre il formato `YYYY_YYYY`, per esempio `2025_2026` o `2026_2027`.

- La stagione `2025_2026` e l'ambiente di test e validazione delle procedure.
- La stagione `2026_2027` sara la prima stagione operativa reale.
- Ogni script, report o automazione che legge o scrive dati stagionali deve indicare esplicitamente la stagione di riferimento.
- Non mischiare dati di stagioni diverse nella stessa cartella operativa.
- Mantieni fuori dalle cartelle stagionali solo regole generali, template riutilizzabili, script condivisi e documentazione non legata a una singola stagione.

Quando il progetto cresce, mantieni una struttura simile:

```text
AGENTS.md
README.md
stagioni/
  2025_2026/
    calendari.md
    data/
      input/
        calendari/
      output/
        calendari/
      archive/
    reports/
  2026_2027/
    calendari.md
    data/
      input/
        calendari/
      output/
        calendari/
      archive/
    reports/
docs/
  regolamenti/
  modelli/
  procedure/
scripts/
templates/
```

- `stagioni/2025_2026/`: stagione di test per prove, verifiche e sviluppo procedure.
- `stagioni/2026_2027/`: prima stagione reale di utilizzo operativo.
- `calendari.md`: registro stagionale dei calendari campionato scaricati.
- `data/input/`: file ricevuti o scaricati per la stagione.
- `data/output/`: file generati o trasformati per la stagione.
- `data/input/calendari/`: calendari originali scaricati dal sito FIPAV Online.
- `data/output/calendari/`: calendari convertiti in Markdown per analisi e automazioni.
- `data/archive/`: copie storiche non piu operative per la stagione.
- `reports/`: riepiloghi e analisi prodotti per la stagione.
- `docs/regolamenti/`: riferimenti normativi e documenti ufficiali.
- `docs/modelli/`: modelli riutilizzabili.
- `docs/procedure/`: procedure interne.
- `scripts/`: automazioni.
- `templates/`: template per email, comunicati, report.

## Gestione attivita gare

Quando lavori su gare, calendari o spostamenti:

- identifica sempre categoria, girone, codice gara, squadre, data, ora e impianto;
- controlla coerenza tra calendario, eventuale richiesta societa e decisione finale;
- segnala conflitti di impianto, sovrapposizioni, date limite e passaggi ancora da autorizzare;
- produci riepiloghi tabellari quando ci sono piu gare;
- non indicare uno spostamento come approvato se manca conferma ufficiale.

Campi minimi consigliati per una tabella gare:

```text
Codice gara | Categoria | Girone | Squadra casa | Squadra ospite | Data | Ora | Impianto | Stato | Note
```

## Comunicazioni

Per bozze email o comunicati:

- includi sempre oggetto, destinatari previsti e testo;
- mantieni il messaggio breve e operativo;
- indica chiaramente cosa viene richiesto, entro quando e a chi rispondere;
- cita allegati e riferimenti solo se effettivamente presenti;
- se il testo contiene decisioni ufficiali, lascia una nota per conferma prima dell'invio.

Formato consigliato:

```text
Oggetto:
Destinatari:
CC:

Testo:

Allegati:
Note interne:
```

## Automazioni

Quando proponi o realizzi automazioni:

- descrivi lo scopo pratico dell'automazione;
- indica input richiesti, output prodotti e frequenza di esecuzione;
- prevedi controlli su dati mancanti, duplicati e formati non validi;
- genera log o riepiloghi leggibili;
- evita operazioni distruttive sui file originali.

Ogni automazione dovrebbe rispondere a queste domande:

```text
Cosa controlla?
Da quali file o fonti legge?
Cosa produce?
Quando va eseguita?
Quali errori devono essere segnalati?
```

### Workflow `downcal`

Usa il workflow `downcal` per scaricare e convertire i calendari dei campionati dal sito FIPAV Online.

Parametri fissi del Comitato Territoriale di Ancona:

```text
Codice comitato: 09042
Pagina campionati: https://fipavonline.it/main/tutti_i_campionati/09042
URL calendario: https://fipavonline.it/gironi/stampa_calendario/{numero_girone}
```

Regole operative:

- Lavora sempre dentro una stagione esplicita. Se non indicata, usa `stagioni/2025_2026/` per test.
- Leggi la pagina campionati e individua i gironi tramite link con `href` nel formato `/main/gare_girone/{numero_girone}` oppure `/gironi/edit/{numero_girone}`.
- Per ogni girone, ricava dal contesto della pagina il nome del campionato e il nome del girone. Se il nome non e ricavabile con certezza, registra il valore come `DA_VERIFICARE`.
- Prima di scaricare un calendario, controlla il registro `stagioni/<stagione>/calendari.md`.
- Se il numero girone e gia presente nel registro, non riscaricare il file salvo richiesta esplicita di aggiornamento.
- Scarica il calendario dall'URL `https://fipavonline.it/gironi/stampa_calendario/{numero_girone}`.
- Salva il file originale in `stagioni/<stagione>/data/input/calendari/`.
- Converti il calendario in Markdown e salva il risultato in `stagioni/<stagione>/data/output/calendari/`.
- Se il file scaricato da `stampa_calendario` contiene solo l'intestazione e nessuna gara, usa la pagina pubblica `https://fipavonline.it/main/gare_girone/{numero_girone}` come fonte di fallback per generare il Markdown e conserva l'HTML in `data/input/calendari/`.
- Usa `SAMPLE/calendario_gare.xlsx` come esempio di struttura del calendario da interpretare.
- Dopo ogni download riuscito, aggiorna `stagioni/<stagione>/calendari.md`.
- Se un download o una conversione fallisce, registra comunque il tentativo con stato `errore` e una nota sintetica.
- Lo script operativo del workflow e `scripts/downcal.py`.

Convenzione consigliata per i file:

```text
girone_<numero_girone>_<campionato_slug>_<girone_slug>.xlsx
girone_<numero_girone>_<campionato_slug>_<girone_slug>.md
```

Campi minimi del registro `calendari.md`:

```text
| Stato | Data download | Campionato | Girone | Numero girone | File input | File output | Note |
```

Valori consigliati per `Stato`:

```text
scaricato | convertito | errore | da_verificare
```

## Qualita degli output

Prima di considerare completato un lavoro:

- controlla date, nomi societa, categorie e codici gara;
- verifica che tabelle e allegati siano coerenti;
- segnala informazioni mancanti o incerte;
- usa una struttura leggibile anche per chi apre il file a distanza di mesi;
- se hai modificato script o procedure, indica come verificarli.

## Regola di prudenza

In caso di dubbio tra velocita e correttezza, scegli la correttezza. Le attivita gare hanno impatti organizzativi su societa, atleti, arbitri e impianti: ogni output deve aiutare a ridurre errori, ambiguita e lavoro manuale ripetitivo.
