# Prompt di esecuzione: Superset Period Compare

Come usarlo:
1. Apri una nuova sessione con la cartella di lavoro `D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare`.
2. Modello consigliato: Sonnet 5.5 con effort alto.
3. Incolla tutto quello che sta sotto la riga "INIZIO PROMPT" fino a "FINE PROMPT".
4. La sessione si ferma da sola ai gate. Rispondi "via libera" per proseguire, oppure scrivi le correzioni.
5. Per riprendere dopo una pausa incolla solo la sezione "RIPRESA" in fondo.

---

## INIZIO PROMPT

Sei l'orchestratore del progetto **Superset Period Compare**: una patch per Apache Superset 6.1.0 che aggiunge il confronto tra un periodo di riferimento e un periodo di confronto (scelti liberamente dall'utente della dashboard) su un solo campo timestamp. Il piano completo e approvato e' in `docs/plans/2026-10-24-period-compare.md`. Leggilo per intero prima di fare qualsiasi cosa, poi leggi `D:\Actual\03_Sviluppo_Software\Repositories\AGENTS.md` e `D:\Actual\03_Sviluppo_Software\Repositories\superset-plugins\AGENTS.md`. Il piano e' la fonte di verita': se qualcosa nel codice contraddice il piano, fermati e dimmelo, non improvvisare.

### 1. Obiettivo in due righe
Superset 6.1.0 ha gia' `time_offsets` con intervalli (`"YYYY-MM-DD : YYYY-MM-DD"`, flag `DATE_RANGE_TIMESHIFTS_ENABLED`). Mancano un filtro nativo per scegliere i due periodi, il collegamento ai grafici (Table, Big Number, barre e linee ECharts, Pivot Table) e l'allineamento delle date nei grafici temporali. Il risultato finale e' una repository privata con SOLI i file modificati, la spiegazione completa e un installer `.bat` automatico che applica tutto su un Superset 6.1.0 esistente, senza toccare i plugin dell'utente.

### 2. Principi non negoziabili
1. **Universale.** Nessun nome di cliente, schema, vista, server, colonna reale o dato reale in codice, test, patch, documenti, fixture, commit. Solo esempi generici (vendite, ticket, prestazioni) e dati sintetici. Il campo data e' qualunque colonna temporale del dataset: nessun nome di colonna nel codice.
2. **Zero regressioni.** Con il confronto spento tutti i grafici si comportano come prima. I test esistenti dei plugin toccati passano SENZA modifiche.
3. **Modifiche minime e localizzate.** Riusa quello che c'e' (`time_offsets`, `compare.py`, `getMetricOffsetsMap`, `isTimeComparison`, il filtro `Time`). Niente nuovi motori, niente Jinja, niente `custom_form_data`, niente secondo filtro `TEMPORAL_RANGE` (verrebbe sovrascritto).
4. **I plugin dell'utente non si toccano.** Nessun file dentro `superset-frontend/plugins/superset-plugin-*` viene scritto dalla patch. L'unico file condiviso con le sue personalizzazioni e' `MainPreset.ts`, modificato solo con un inserimento tra marcatori `period-compare:begin/end`.
5. **Reversibile e idempotente.** L'installer si puo' rilanciare e annullare byte per byte.
6. **TDD.** Test rosso, codice minimo, test verde. Un commit per task, messaggio convenzionale, firma `-s`. Aggiorna `[Unreleased]` in `CHANGELOG.md` a ogni task.
7. **Sicurezza.** Non leggere ne' stampare file con credenziali (`.env`, `cookies.txt`, `login.json`, `docker/.env*`, `*CREDENZIALI*`, certificati). Non copiare nel repository nulla da cartelle di clienti. Nessun dato personale o sanitario.
8. **Regole del tuo ambiente.** UTF-8 senza BOM; niente trattino lungo ne' doppio trattino come punteggiatura nei documenti e nel codice di progetto; in PowerShell usa `;` e non `&&`; i percorsi sono quelli di `D:\Actual\...`.

### 3. Cartelle
- Repository del progetto: `D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare` (oggi contiene solo `docs/plans/`; inizializzala con `git init -b main` alla Fase 6.1, non prima).
- Checkout di lavoro: crea con `git worktree add` dal tag `6.1.0` del clone `D:\Actual\03_Sviluppo_Software\Repositories\superset-6.1.0` una copia pulita in `D:\Actual\03_Sviluppo_Software\Repositories\_work\superset-6.1.0-pc` (branch `period-compare`). Una seconda copia "personalizzata" in `_work\superset-6.1.0-custom` per le prove di non invasivita' (con i 5 plugin dell'utente copiati da `superset-6.1.0\superset-frontend\plugins\` e il suo `MainPreset.ts`).
- NON modificare mai l'albero originale `superset-6.1.0` (6.367 voci sporche per i fine riga, contiene file con credenziali). Leggi da li' solo cio' che serve per copiare i plugin.
- Python 3.11 con `uv`; Node 20 (come il `Dockerfile` dell'utente); `npm ci --legacy-peer-deps`; heap 8192 o piu'.
- Non toccare le dashboard di altri progetti sul server.

### 4. Come lavori: agenti
Usa il tool Agent. Massimo 3 agenti in parallelo. Ogni agente riceve: il percorso del piano, il suo perimetro di file (sezione 6 del piano), il contratto `docs/CONTRATTO.md` quando esiste, le regole della sezione 2 qui sopra, e deve consegnare: elenco file toccati, test eseguiti con esito, cosa non e' riuscito. Nessun agente scrive fuori dal proprio perimetro. Quando un agente finisce, controlli tu il risultato (diff e test) prima di dichiararlo fatto.

Brief pronti (adatta solo il percorso delle copie di lavoro):

- **Agente E (ambiente e dati)**: Fase 0 e Fase 8. Crea i checkout, il venv, installa le dipendenze, lancia i test di baseline (backend: `tests/unit_tests/common/test_time_shifts.py`, `test_query_context_processor.py`, `tests/unit_tests/pandas_postprocessing/test_compare.py`; frontend: `plugin-chart-table`, `plugin-chart-echarts`, `superset-ui-core`, `nativeFilters/utils.test.ts`), configura Superset su SQLite con un `superset_config` di prova (credenziali di prova generate localmente, mai riutilizzate, mai nel repository). Poi in Fase 8: generatore di fixture sintetiche multi-dominio con tutte le varianti di colonna data della sezione 8 del piano, dashboard dimostrativa, benchmark.
- **Agente K (contratto)**: Fase 1. Scrive `docs/CONTRATTO.md` (chiavi `time_range`, `time_compare`, `comparison_type`, formato offset, nomi colonna, regola di allineamento con traslazione in mesi interi o giorni) e le firme di `applyDashboardComparison` e `resolveTimeOffsets` con test d'interfaccia rossi.
- **Agente A (backend)**: Fase 2. File: `superset/models/helpers.py` (traslazione e allineamento per gli offset a intervallo, join per grana), `superset/common/query_object.py` (estremi con orario), `superset/constants.py` (`time_compare`, `comparison_type` nei mapping override), config. Test in `tests/unit_tests/common/` e un test di integrazione su `/api/v1/chart/data`.
- **Agente B (frontend core)**: Fase 3. `packages/superset-ui-core/src/query/constants.ts` e tipi, `packages/superset-ui-chart-controls/src/utils/applyDashboardComparison.ts` (nuovo, esportato), `isTimeComparison.ts`, controllo `follow_dashboard_comparison` in `sections/timeComparison.tsx`, test del merge in `nativeFilters/utils.test.ts`.
- **Agente C (filtro nativo)**: Fase 4. `src/filters/components/PeriodCompare/` (modello: `Time/`), funzioni pure `resolveComparison.ts` con almeno 25 test, controllo `reference_column`, registrazioni (`src/constants.ts`, `components/index.ts`, ancora in `MainPreset.ts`, `FILTER_SUPPORTED_TYPES`), tutti i punti che trattano `filter_time` nella finestra dei filtri, traduzioni italiano e inglese.
- **Agente D (grafici, in sequenza)**: Fase 5. Prima Table e Big Number, poi barre e linee ECharts, infine Pivot Table. Ogni grafico chiama `applyDashboardComparison` all'inizio di `buildQuery` e `transformProps`; i test esistenti passano senza modifiche.
- **Agente I (installer e documenti)**: Fase 6, parallelo a A e B. Scheletro repository, `tools/make-payload.ps1`, `installer/PeriodCompare.ps1` con le librerie, `install.bat`, `uninstall.bat`, `verify.bat`, `dry-run.bat`, test Pester (gli 8 casi della sezione 8), README e `docs/*` completi in italiano.
- **Agente R (revisore)**: a ogni gate. Sola lettura. Controlla diff, regole della sezione 2, riuso invece di duplicazione, esegue `/simplify` sul codice nuovo, scansione segreti e nomi di clienti nel repository.

### 5. Ordine, gate e cosa devi mostrarmi
Segui le fasi 0-11 del piano. A ogni gate (G0 ... G6) fermati e scrivi un riepilogo di al massimo 8 righe: cosa e' fatto, test passati con numeri, cosa resta, rischi nuovi, e la domanda "via libera?". Non passare alla fase successiva senza la mia risposta ai gate G0, G1, G4 e G6. Gli altri gate puoi superarli da solo se tutti i test sono verdi e il revisore non ha trovato problemi bloccanti.

Gate G0 in particolare: oltre alla baseline, dimmi RAM libera, spazio su disco, tempo di `npm ci`, e se la build del frontend e' fattibile. Se non lo e', passa al piano B del piano (Jest piu' `tsc` piu' prova API) e dimmelo.

### 6. Verifica finale prima del push
1. `pytest` dei test nuovi e di quelli esistenti sul tempo e sugli offset: tutto verde.
2. Jest dei pacchetti e dei plugin toccati: tutto verde, test esistenti non modificati.
3. `tsc --noEmit` sui pacchetti toccati.
4. Pester dell'installer: tutti i casi verdi su albero pulito e su albero personalizzato (hash dei plugin dell'utente identici prima e dopo).
5. Prova end to end su Superset locale con dati sintetici: due periodi scelti, quattro grafici controllati contro una query SQL scritta a mano, con screenshot.
6. Confronto spento = comportamento identico a prima.
7. Matrice di universalita' (tipi di colonna data, grane, due dataset diversi nella stessa dashboard).
8. Scansione finale: nessun segreto, nessun dato personale, nessun nome di cliente, schema o server nel repository; `.gitignore` dal modello `templates\gitignore.template`; `CHANGELOG.md` con la release `0.1.0`.

### 7. Fase 11: repository privata
Solo dopo il mio via libera esplicito sul riepilogo G6: `git init -b main` (se non gia' fatto), commit finale, `gh repo create FrancescoCastaldi/superset-period-compare --private --source . --remote origin --push`. Solo GitHub, repository privata, nessun remote Bitbucket. Poi `gh repo view` per confermare che sia privata, e dimmi l'indirizzo.

### 8. Se qualcosa non torna
Se un test esistente fallisce per una tua modifica, correggi la modifica, non il test. Se il piano e' impossibile da seguire in un punto (per esempio una funzione di Superset e' diversa da come descritta), fermati, spiega cosa hai trovato con percorso e riga, e proponi un'alternativa: non procedere con un'ipotesi. Se un comando richiederebbe di toccare cio' che e' fuori perimetro (albero originale, plugin dell'utente, server), non eseguirlo e chiedi.

Comincia ora: leggi il piano e i due `AGENTS.md`, poi lancia l'Agente E per la Fase 0 e fermati al gate G0.

## FINE PROMPT

---

## RIPRESA (da incollare dopo una pausa o in una nuova sessione)

Riprendi il progetto Superset Period Compare. Leggi `docs/plans/2026-10-24-period-compare.md` e `git log --oneline` nella repository del progetto e nel checkout `_work\superset-6.1.0-pc` (branch `period-compare`) per capire a che punto siamo. Elenca le fasi gia' completate (task spuntati nel piano e commit), la fase in corso e i test che oggi passano. Riesegui i test di baseline della fase in corso per verificare lo stato, scrivimi un riepilogo di 8 righe e fermati in attesa del via libera. Le regole sono le stesse della sezione 2 del prompt di esecuzione: universale, zero regressioni, plugin dell'utente intatti, nessun segreto, push solo dopo la mia conferma.
