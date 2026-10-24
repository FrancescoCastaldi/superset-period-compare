# Architettura Tecnica: Superset Period Compare

Questo documento descrive il funzionamento interno, il flusso dei dati e le decisioni architetturali alla base del modulo Period Compare per Apache Superset 6.1.0.

## 1. Principi Architetturali

1. **Riuso delle primitive native**:
   Superset 6.1.0 possiede gia un motore backend (`processing_time_offsets` in `helpers.py`) capace di gestire offset ad intervallo esplicito tramite il feature flag `DATE_RANGE_TIMESHIFTS_ENABLED`. Il modulo estende questo meccanismo senza introdurre motori paralleli, filtri duplicati o logiche di templating Jinja.
2. **Allineamento temporale 1:1**:
   La limitazione principale di Superset upstream era la mancanza di allineamento dell'asse temporale per gli offset a intervallo nelle serie storiche: Superset eliminava la colonna data secondaria producendo valori nulli (NaN). Period Compare trasla temporalmente la colonna data del periodo di confronto con granularita esatta (per mesi interi se le date cadono a inizio mese, oppure per giorni altrimenti), consentendo una join pulita sulla colonna temporale del periodo di riferimento.
3. **Isolamento e rispetto dei plugin utente**:
   Nessun file presente in `superset-frontend/plugins/superset-plugin-*` viene toccato o sovrascritto. L'unico punto di contatto del registro plugin e' `MainPreset.ts`, modificato esclusivamente tra marcatori espliciti `period-compare:begin` e `period-compare:end`.

## 2. Diagramma del Flusso dei Dati

```
 +-------------------------------------------------------------------+
 | Dashboard UI (Filtro Nativo PeriodCompare)                        |
 | Utente seleziona:                                                 |
 |  - Periodo Riferimento: "2026-09-01 : 2026-10-01"                 |
 |  - Preset Confronto:    "Mese precedente" (o intervallo libero)   |
 |  - Modalita Calcolo:    "Valori effettivi", "Differenza", "%"     |
 +----------------------------------+--------------------------------+
                                    |
                                    v emette dataMask (extraFormData)
 +-------------------------------------------------------------------+
 | extraFormData:                                                    |
 |   time_range:      "2026-09-01 : 2026-10-01"                      |
 |   time_compare:    ["2026-08-01 : 2026-09-01"]                    |
 |   comparison_type: "values"                                       |
 +----------------------------------+--------------------------------+
                                    |
                                    v merge via Redux
 +-------------------------------------------------------------------+
 | Grafici (Table, Big Number, ECharts Timeseries, Pivot Table)      |
 |  - Chiamata ad applyDashboardComparison(formData)                 |
 |  - Se follow_dashboard_comparison !== false:                      |
 |      time_compare locale viene sovrascritto da quello di dashboard|
 +----------------------------------+--------------------------------+
                                    |
                                    v buildQuery() -> POST /api/v1/chart/data
 +-------------------------------------------------------------------+
 | Backend Superset (QueryContextProcessor / helpers.py)             |
 |  1. Esegue query principale sul periodo di riferimento            |
 |  2. Esegue query secondaria sul periodo di confronto (offset)     |
 |  3. In join_offset_dfs():                                         |
 |     - Calcola scostamento temporale (mesi interi o giorni)        |
 |     - Trasla la colonna temporale della query di confronto        |
 |     - Esegue outer/left join con riallineamento delle serie       |
 |  4. Esegue compare.py se e' richiesta differenza o variazione %  |
 +----------------------------------+--------------------------------+
                                    |
                                    v DataFrame consolidato
 +-------------------------------------------------------------------+
 | Frontend Visualizzazione (transformProps)                         |
 |  - Renderizza metriche affiancate, serie sovrapposte o variazioni |
 +-------------------------------------------------------------------+
```

## 3. Gestione dei Casi Limite nel Trasferimento Temporale

Il calcolo dello shift in `helpers.py` distingue due modalita:
- **Shift per Mesi Interi (`pd.DateOffset(months=N)`)**:
  Applicato quando entrambi gli estremi di inizio cadono al giorno 1 del mese (es. 1 Settembre vs 1 Agosto). Garantisce che il 30 Giugno corrisponda al 30 Agosto, e che l'ultimo giorno del mese resti allineato anche tra mesi con 30 e 31 giorni.
- **Shift per Giorni (`pd.DateOffset(days=N)`)**:
  Applicato per periodi infrasettimanali o intervalli arbitrari (es. dal 12 al 24 del mese). Lo scostamento e' esattamente pari al numero di giorni intercorrenti tra le date di inizio.
- **Anni Bisestili**:
  Il 29 Febbraio confrontato con l'anno precedente trasla al 28 Febbraio senza errori di fuori scala.

## 4. Controllo Granularita Multi-Colonna Data

In dataset con molteplici colonne data (es. data ordine, data spedizione, data fattura):
- Ogni grafico mantiene per default la propria colonna temporale assegnata nell'asse X o nella configurazione metrica.
- Se nella configurazione del filtro PeriodCompare viene indicata una `reference_column`, questa viene propagata tramite `granularity_sqla` per indirizzare specificamente tale dimensione.
