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
- Evita espressioni informali quando il testo è destinato a societa, tesserati, arbitri o organismi federali.
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

### Gestione eccezioni e casi limite (FIPAV Online)

Il portale FIPAV Online non e omogeneo: formati, layout e contenuti variano per tipo di campionato e fase. Le automazioni devono gestire le eccezioni in modo esplicito, tracciabile e prudente.

#### Principi

- **Mai successo silenzioso**: se un output e vuoto o ambiguo, segnalarlo nel registro e nel riepilogo a fine run.
- **Conservare le fonti**: non sovrascrivere file input originali; in fallback HTML conservare sia `.xlsx` che `.html`.
- **Tracciabilita**: ogni eccezione deve finire in `calendari.md` con stato, nota standardizzata e riferimento al girone.
- **Prudenza operativa**: gironi `da_verificare` o `errore` non vanno usati per decisioni su spostamenti finche non confermati.

#### Stati del registro

| Stato | Quando usarlo |
| --- | --- |
| `convertito` | Almeno una gara estratta; file output utilizzabile |
| `da_verificare` | Download riuscito ma 0 gare, dati incompleti, nomi `DA_VERIFICARE`, o schema anomalo |
| `errore` | Fallimento tecnico (rete, parsing, file corrotto) dopo retry |
| `scaricato` | Solo input salvato, conversione non completata (uso manuale) |

#### Catalogo casi limite noti

Pattern osservati nella stagione 2025_2026:

1. **XLSX senza righe gara** — frequente su fasi finali, playoff e semifinali; usare fallback `gare_girone`. Nota: `N gare da HTML; XLSX senza righe gara`.
2. **XLSX vuoto anche su gironi regolari** — es. girone 60897 (Prima Div. M Girone A); stesso fallback HTML.
3. **Nomi non ricavabili** — registrare `DA_VERIFICARE` per campionato o girone; aggiungere nota `nome girone DA_VERIFICARE`.
4. **Calendario non ancora pubblicato** — entrambe le fonti restituiscono 0 gare; stato `da_verificare`, nota `nessuna gara pubblicata`.
5. **Risposta non-XLSX** — il portale puo restituire HTML al posto del file; tentare fallback `gare_girone` prima di segnalare errore. Nota: `N gare da HTML; risposta non-XLSX`.
6. **Variazione struttura pagina campionati** — se lo script trova 0 gironi, fermarsi: probabile cambio layout HTML.
7. **Differenza schema output** — output da HTML include colonne `Risultato` e `Parziali`; le automazioni downstream devono accettare 8 o 10 colonne.

Quando scopri un nuovo caso limite ricorrente, aggiungilo a questo catalogo con data e esempio di numero girone. Non modificare la logica di parsing senza un esempio salvato in `data/input/calendari/`.

#### Playbook dopo ogni run

1. Controllare il riepilogo stdout (`convertiti / saltati / errori / da_verificare`).
2. Filtrare in `calendari.md` le righe con stato `errore` o `da_verificare`.
3. Per ogni `da_verificare` con 0 gare: verificare manualmente `https://fipavonline.it/main/gare_girone/{numero_girone}` — puo essere normale pre-pubblicazione.
4. Per ogni `errore`: rieseguire lo script (retry automatico); se persiste, aprire l'URL e ispezionare la risposta.
5. Per aggiornamenti calendario: usare `--force` solo se richiesto esplicitamente.

#### Convenzione note nel registro

```text
{N} gare da XLSX
{N} gare da HTML; XLSX senza righe gara
{N} gare da HTML; risposta non-XLSX
nessuna gara pubblicata
nome girone DA_VERIFICARE
{messaggio errore sintetico}
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

- Applica il catalogo eccezioni e il playbook definiti nella sezione **Gestione eccezioni e casi limite (FIPAV Online)**.
- Lavora sempre dentro una stagione esplicita. Se non indicata, usa `stagioni/2025_2026/` per test.
- Leggi la pagina campionati e individua i gironi tramite link con `href` nel formato `/main/gare_girone/{numero_girone}` oppure `/gironi/edit/{numero_girone}`.
- Per ogni girone, ricava dal contesto della pagina il nome del campionato e il nome del girone. Se il nome non e ricavabile con certezza, registra il valore come `DA_VERIFICARE`.
- Prima di scaricare un calendario, controlla il registro `stagioni/<stagione>/calendari.md`.
- Salta i gironi gia in stato `convertito` o `scaricato`. Ri-tenta automaticamente i gironi in stato `errore` o `da_verificare` al run successivo, senza `--force`.
- Usa `--force` solo per riscaricare gironi gia `convertito`, su richiesta esplicita di aggiornamento.
- Scarica il calendario dall'URL `https://fipavonline.it/gironi/stampa_calendario/{numero_girone}`.
- Salva il file originale in `stagioni/<stagione>/data/input/calendari/`.
- Converti il calendario in Markdown e salva il risultato in `stagioni/<stagione>/data/output/calendari/`.
- Se la risposta non e un file XLSX valido, o se l'XLSX contiene solo l'intestazione senza gare, usa la pagina pubblica `https://fipavonline.it/main/gare_girone/{numero_girone}` come fallback e conserva l'HTML in `data/input/calendari/`.
- Se entrambe le fonti restituiscono 0 gare, registra stato `da_verificare` con nota `nessuna gara pubblicata` — non usare `convertito`.
- Usa `SAMPLE/calendario_gare.xlsx` come esempio di struttura del calendario da interpretare.
- Dopo ogni tentativo, aggiorna `stagioni/<stagione>/calendari.md` appendendo una nuova riga (audit trail).
- Se un download o una conversione fallisce dopo i retry, registra stato `errore` con nota sintetica.
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
