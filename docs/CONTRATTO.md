# Contratto Dati: Superset Period Compare

Versione: 1.0.0
Stato: Congelato (Fase 1)
Data: 2026-10-24

Questo documento definisce il contratto dati formale tra il filtro nativo di dashboard (PeriodCompare), il livello intermedio di trasformazione del form data (applyDashboardComparison), il backend analitico di Superset (processing_time_offsets, helpers.py, query_object.py) e i componenti di visualizzazione (Table, Big Number, ECharts Timeseries, Pivot Table).

## 1. Struttura extraFormData emessa dal filtro PeriodCompare

Il filtro nativo PeriodCompare produce un oggetto dataMask contenente extraFormData con le seguenti chiavi:

```json
{
  "extraFormData": {
    "time_range": "2026-09-01 : 2026-10-01",
    "time_compare": ["2026-08-01 : 2026-09-01"],
    "comparison_type": "values"
  },
  "filterState": {
    "value": {
      "reference": "2026-09-01 : 2026-10-01",
      "comparison": "2026-08-01 : 2026-09-01",
      "preset": "previous_month"
    },
    "label": "Settembre 2026 vs Agosto 2026"
  }
}
```

### 1.1 Specifiche dei campi
- time_range (stringa): intervallo temporale del periodo di riferimento, espresso come "YYYY-MM-DD : YYYY-MM-DD" o con orario "YYYY-MM-DDTHH:MM:SS : YYYY-MM-DDTHH:MM:SS". Gli intervalli sono convenzionalmente semiaperti [inizio, fine), con estremo superiore escluso.
- time_compare (array di stringhe o stringa): periodo o periodi di confronto. Nel caso di intervallo libero o calcolato da preset, il formato e' "YYYY-MM-DD : YYYY-MM-DD". Viene normalizzato in array di stringhe.
- comparison_type (stringa): tipo di calcolo del confronto. Valori ammessi:
  - "values": restituisce i valori grezzi di riferimento e confronto affiancati.
  - "difference": differenza algebrica (riferimento - confronto).
  - "percentage": variazione percentuale ((riferimento - confronto) / confronto).
  - "ratio": rapporto (riferimento / confronto).
- granularity_sqla (stringa, facoltativa): emessa solo se l'utente configura esplicitamente il campo "reference_column" nel pannello del filtro per indirizzare una specifica colonna data quando il dataset ne possiede molteplici. Se non configurata, ogni grafico applica il filtro sulla propria colonna temporale primaria (asse X, granularity_sqla o filtro temporale nativo).

## 2. Helper di integrazione: applyDashboardComparison e resolveTimeOffsets

I due metodi di utilita' esportati da `@superset-ui/chart-controls` coordinano l'applicazione del confronto di dashboard ai singoli grafici.

### 2.1 Firma TypeScript

```typescript
export type ComparisonType = 'values' | 'difference' | 'percentage' | 'ratio';

export interface DashboardComparisonResult {
  formData: Record<string, any>;
  timeOffsets: string[];
  comparisonType: ComparisonType;
  isComparing: boolean;
}

export function applyDashboardComparison(
  formData: Record<string, any>
): DashboardComparisonResult;

export function resolveTimeOffsets(
  formData: Record<string, any>,
  baseQueryObject?: Record<string, any>
): string[];
```

### 2.2 Regole di precedenza
1. Se il grafico ha `follow_dashboard_comparison === false`, il filtro di dashboard viene ignorato e il grafico segue esclusivamente i propri controlli interni di confronto.
2. Se `follow_dashboard_comparison` e' true (default), il valore di `extra_form_data.time_compare` sovrascrive qualsiasi configurazione `time_compare` locale del grafico.
3. Se `time_compare` e' assente o vuoto, `isComparing` e' false e `timeOffsets` e' un array vuoto.
4. `comparison_type` della dashboard ha priorita' sul `comparison_type` del grafico se presente in `extra_form_data`. In sua assenza, il grafico ricade sul proprio valore o sul default "values".

## 3. Contratto Backend: Query e Nomenclatura Colonne

### 3.1 Payload richiesta POST /api/v1/chart/data

Esempio di query inviata al backend:

```json
{
  "datasource": {
    "id": 1,
    "type": "table"
  },
  "queries": [
    {
      "columns": ["order_date", "category"],
      "metrics": ["sum__sales_amount"],
      "time_range": "2026-09-01 : 2026-10-01",
      "time_offsets": ["2026-08-01 : 2026-09-01"],
      "granularity": "order_date",
      "time_grain_sqla": "P1D",
      "post_processing": [
        {
          "operation": "compare",
          "options": {
            "source_columns": ["sum__sales_amount"],
            "compare_columns": ["sum__sales_amount__2026-08-01 : 2026-09-01"],
            "compare_type": "difference"
          }
        }
      ]
    }
  ]
}
```

### 3.2 Convenzione nomi colonne risultanti
- Metrica riferimento: `<nome_metrica>` (esempio: `sales_amount` o `count`).
- Metrica confronto per intervallo: `<nome_metrica>__<offset>` (esempio: `sales_amount__2026-08-01 : 2026-09-01`).
- Differenza algebrica: `difference__<nome_metrica>__<nome_metrica>__<offset>`.
- Variazione percentuale: `percentage__<nome_metrica>__<nome_metrica>__<offset>`.
- Rapporto: `ratio__<nome_metrica>__<nome_metrica>__<offset>`.

### 3.3 Regola di allineamento temporale (Backend)
Quando la query include una colonna temporale reale (asse X):
1. Calcolo del delta di traslazione tra i due intervalli: `delta = inizio_riferimento - inizio_confronto`.
2. Se sia l'inizio del riferimento che l'inizio del confronto cadono sul primo giorno del mese (giorno 1), la traslazione temporale del dataframe di confronto viene calcolata in mesi interi (tramite `pandas.DateOffset(months=N)`), garantendo il perfetto allineamento giorno-per-giorno o mese-per-mese senza sfasamenti dovuti a mesi di 28, 30 o 31 giorni.
3. In tutti gli altri casi, la traslazione viene calcolata in giorni esatti (`pandas.Timedelta(days=N)`).
4. Unione (join) dei dataframe: avviene sulla colonna temporale traslata aggregata per la grana (time_grain). Per i periodi con differente numero di giorni (esempio: 31 giorni contro 30), le date mancanti in coda presentano valore nullo (NaN o None) e non provocano alcuna traslazione spuria.
