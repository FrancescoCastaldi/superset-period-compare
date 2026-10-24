# Procedura di Aggiornamento a Nuove Versioni di Superset

Questa guida spiega come mantenere o trasferire la patch Period Compare quando viene rilasciata una nuova versione minore o maggiore di Apache Superset (es. 6.2.0, 7.0.0).

## 1. Verifica Preventiva di Compatibilita

Prima di applicare la patch su una nuova release di Superset:

1. Eseguire una verifica con `verify.bat`:
   ```cmd
   verify.bat D:\Percorso\Al\Nuovo\Superset
   ```
2. Lo script analizzera ogni file rispetto agli hash registrati in `compat.json`. Se alcuni file upstream hanno subito modifiche nel frattempo (es. nuove righe in `helpers.py`), l'installer li segnalera come `ModifiedOrCustom`.

## 2. Allineamento dei File Modificati

I file toccati dalla patch appartengono a tre aree ben circoscritte:

### Backend Python:
- `superset/models/helpers.py`: logica di allineamento e join in `join_offset_dfs` e `processing_time_offsets`.
- `superset/common/query_object.py`: supporto stringhe orarie in `_is_valid_date_range`.
- `superset/constants.py`: mappatura `time_compare` e `comparison_type` in `EXTRA_FORM_DATA_OVERRIDE_REGULAR_MAPPINGS`.
- `superset/config.py`: abilitazione feature flag `DATE_RANGE_TIMESHIFTS_ENABLED: True`.

### Frontend Core e Controlli:
- `packages/superset-ui-chart-controls/src/utils/applyDashboardComparison.ts`: helper di normalizzazione.
- `packages/superset-ui-chart-controls/src/sections/timeComparison.tsx`: controllo `follow_dashboard_comparison`.
- `packages/superset-ui-core/src/query/constants.ts`: costante mappatura override.

### Filtro Nativo e Registrazioni:
- `src/filters/components/PeriodCompare/`: modulo indipendente autocontenuto.
- `src/visualizations/presets/MainPreset.ts`: marcatori `period-compare:begin` e `period-compare:end`.

## 3. Rigenerazione del Payload per la Nuova Release

Quando la nuova versione di Superset e' allineata nel proprio ambiente di sviluppo:
1. Portare le modifiche sul branch di lavoro della nuova versione.
2. Eseguire lo script di estrazione automatica:
   ```powershell
   powershell -File tools/make-payload.ps1 -WorktreePath "D:\Percorso\SupersetNuovo" -BaseTag "6.2.0"
   ```
3. Lo script estrarra i nuovi file in `payload/` e aggiornera il manifest `compat.json` con gli hash esatti della nuova versione di riferimento.
4. Eseguire la suite Pester di test (`Invoke-Pester tests/installer.Tests.ps1`) per convalidare il flusso di installazione e rollback.
