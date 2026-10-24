# Changelog

Tutte le modifiche rilevanti a questo progetto sono documentate in questo file.

Il formato e' basato su [Keep a Changelog](https://keepachangelog.com/it/1.1.0/)
e questo progetto aderisce a [Semantic Versioning](https://semver.org/lang/it/).

## [0.1.0] - 2026-10-24

### Added
- **Filtro Nativo PeriodCompare**: componente filtro nativo di dashboard per la selezione interattiva del periodo di riferimento, preset di confronto (Periodo precedente, Mese precedente, Anno precedente, Personalizzato) e modalita di calcolo (Valori effettivi, Differenza, Variazione percentuale, Rapporto).
- **Date Arithmetic Engine (`resolveComparison.ts`)**: motore puro per il calcolo e la traslazione delle date con supporto a scostamenti per mesi interi, giorni esatti, anni bisestili e chiusure mese.
- **Integrazione Backend Superset**: estensione di `superset/models/helpers.py` con allineamento temporale 1:1 delle serie storiche, supporto formati ISO con timestamp orario in `query_object.py` e feature flag `DATE_RANGE_TIMESHIFTS_ENABLED` abilitato per default.
- **Integrazione Grafici Chiave**:
  - `plugin-chart-table`: supporto colonne e metriche di confronto affiancate o scostate.
  - `plugin-chart-echarts`: Big Number Period over Period e serie storiche Timeseries (Line, Bar, Smooth Line, Step Line).
  - `plugin-chart-pivot-table`: matrice pivot aggregata con colonne di confronto.
- **Controllo Grafico `follow_dashboard_comparison`**: opzione nei controlli temporali per abilitare o escludere un singolo grafico dal confronto di dashboard.
- **Toolchain di Installazione Idempotente**:
  - `install.bat`, `uninstall.bat`, `verify.bat`, `dry-run.bat`.
  - Motore PowerShell modulare `installer/PeriodCompare.ps1` con librerie `Backup.ps1`, `Verify.ps1`, `Patch.ps1`, `Restore.ps1`, `BuildFrontend.ps1`.
  - Salvaguardia assoluta dei plugin personalizzati utente (`superset-frontend/plugins/superset-plugin-*`) con merge selettivo tra marcatori `period-compare:begin/end` in `MainPreset.ts`.
- **Suite di Test Automatizzata**:
  - 63 test unitari backend pytest passati al 100%.
  - 28 test di logica temporale frontend passati al 100%.
  - 5 test di contratto interfaccia `applyDashboardComparison` passati al 100%.
  - Test suite Pester dell'installer passata al 100% su albero pulito e personalizzato.
- **Documentazione Completa**:
  - `README.md`, `ARCHITETTURA.md`, `INSTALLAZIONE.md`, `AGGIORNARE_VERSIONE.md`, `MIGRARE_DA_VISTE_CARTESIANE.md`, `docs/CONTRATTO.md`.
