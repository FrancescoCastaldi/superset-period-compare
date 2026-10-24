# Superset Period Compare

Patch modulare, universale e reversibile per Apache Superset 6.1.0 che abilita il confronto libero tra un periodo di riferimento e un periodo di confronto su qualsiasi colonna temporale della dashboard.

## Cos'e' e a cosa serve

Nei cruscotti aziendali di Business Intelligence, una delle esigenze primarie e' confrontare l'andamento di una metrica (es. fatturato, ordini, ticket di assistenza, accessi) tra due intervalli temporali definiti liberamente dall'utente finale: ad esempio il mese corrente rispetto al mese precedente, oppure l'anno in corso rispetto all'anno passato, o due finestre arbitrarie scelte su calendario.

Storicamente, in Apache Superset questo risultato richiedeva complessi artifici a livello di database: viste SQL cartesiane, query pesanti con self-join, duplicazione delle righe o filtri Jinja complessi non adatti agli utenti di business.

Superset Period Compare risolve questo problema alla radice, sfruttando l'architettura nativa di Apache Superset 6.1.0:
1. Aggiunge un filtro nativo di dashboard denominato **PeriodCompare** (Filtro confronto periodi).
2. Fornisce all'utente una selezione immediata tra preset comuni (Periodo precedente, Mese precedente, Anno precedente) oppure una seconda finestra di calendario per il periodo di confronto personalizzato.
3. Consente di visualizzare i dati come valori effettivi affiancati, differenza algebrica assoluta, variazione percentuale o rapporto.
4. Allinea automaticamente le date nei grafici temporali per grana (giorno, settimana, mese), evitando buchi o disallineamenti di calendario tra mesi di diversa lunghezza (es. 31 vs 30 giorni o anni bisestili).
5. Si installa con un click tramite script automatico, non tocca in alcun modo i plugin personalizzati dell'utente e si puo' disinstallare ripristinando lo stato originale byte per byte.

## Grafici supportati

- **Table**: visualizza metriche e colonne di confronto affiancate o come scostamento.
- **Big Number with Trendline & Big Number Period over Period**: KPI principale e variazione percentuale rispetto al periodo di confronto.
- **ECharts Timeseries (Line, Bar, Smooth Line, Step Line)**: serie temporali sovrapposte con allineamento puntuale delle date.
- **Pivot Table v2**: matrice pivot aggregata con colonne di confronto.

## Quickstart: Installazione in 3 comandi

### Requisiti
- Apache Superset 6.1.0
- Windows PowerShell 5.1 o successivo
- Node 20 (opzionale, solo per ricompilare il frontend se non si usa un ambiente gia compilato)

### Procedura

1. Clonare o scaricare questo repository nella cartella desiderata:
```cmd
git clone https://github.com/FrancescoCastaldi/superset-period-compare.git
cd superset-period-compare
```

2. Eseguire una verifica preventiva senza modifiche:
```cmd
dry-run.bat D:\Percorso\Al\Tuo\Superset
```

3. Applicare la patch (crea automaticamente un backup di sicurezza prima di modificare qualsiasi file):
```cmd
install.bat D:\Percorso\Al\Tuo\Superset
```

Per disinstallare in qualsiasi momento e ripristinare Superset allo stato originale:
```cmd
uninstall.bat D:\Percorso\Al\Tuo\Superset
```

## Test

Il repository include le suite in `tests/`: 17 test backend pytest, 28 + 5 test frontend eseguibili con solo Node e 5 contesti Pester per l'installer. I comandi per eseguirle sono in [tests/README.md](tests/README.md). La compilazione del frontend non e coperta dai test.

## Struttura della documentazione

- [Architettura tecnica e decisioni di design](ARCHITETTURA.md): flussi dati, ciclo di vita delle query e logica di allineamento temporale.
- [Guida all'installazione e rollback](INSTALLAZIONE.md): opzioni CLI, gestione backup e compatibilita Docker.
- [Guida alla migrazione da viste cartesiane](MIGRARE_DA_VISTE_CARTESIANE.md): come semplificare il database e dismettere le vecchie viste di appoggio.
- [Aggiornamento a versioni successive](AGGIORNARE_VERSIONE.md): come verificare e portare la patch su Superset 6.2+ o Superset 7.
- [Contratto dati formale](docs/CONTRATTO.md): specifiche dettagliate dei payload e delle strutture extraFormData.
- [Registro delle modifiche](CHANGELOG.md): storico versioni e modifiche rilasciate.
