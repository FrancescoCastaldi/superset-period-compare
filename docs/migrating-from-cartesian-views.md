# Guida alla Migrazione da Viste SQL Cartesiane a Period Compare

Questa guida illustra come dismettere le vecchie viste di database con self-join o prodotti cartesiani utilizzate in precedenza per confrontare periodi storici, sostituendole con l'approccio nativo ad alte prestazioni di Superset Period Compare.

## 1. Il Problema delle Viste SQL Tradizionali

Per confrontare periodi temporali in Superset, molti team implementavano viste SQL con strutture simili a:

```sql
/* VECCHIO APPROCCIO (PROBLEMATICO): */
SELECT 
    t1.id,
    t1.data_evento AS data_riferimento,
    t1.valore AS valore_riferimento,
    t2.valore AS valore_confronto,
    (t1.valore - t2.valore) AS differenza
FROM tabella_eventi t1
LEFT JOIN tabella_eventi t2 
    ON t2.categoria = t1.categoria 
    AND t2.data_evento = DATEADD(month, -1, t1.data_evento);
```

### Limiti e Inconvenienti del Vecchio Approccio:
1. **Rigidita**: il confronto e' fisso nel codice SQL (es. solo mese precedente). Per confrontare un anno prima o due finestre arbitrarie servivano viste duplicate.
2. **Esplosione dei Record**: le self-join su milioni di righe degradano le prestazioni del database e aumentano i tempi di risposta della dashboard.
3. **Manutenzione Complessa**: ogni modifica di colonna o metrica richiedeva la modifica e il riallineamento delle viste di produzione.

## 2. Il Nuovo Approccio Nativo

Con Superset Period Compare, il dataset su Superset punta direttamente alla **tabella nativa semplice** (o vista pulita senza join temporali):

```sql
/* NUOVO APPROCCIO (SEMPLICE, PULITO E VELOCE): */
SELECT 
    id,
    data_evento,
    categoria,
    valore
FROM tabella_eventi;
```

Tutta la logica di confronto viene demandata al motore analitico di Superset:
1. Il backend esegue due query aggregate distinte e mirate: una sul periodo di riferimento e una su quello di confronto.
2. Le due query filtrano nativamente solo gli intervalli temporali interessati, sfruttando al meglio indici e partizioni su database.
3. L'allineamento e il calcolo di scostamento o variazione percentuale avvengono in memoria nel processo analitico di Superset.

## 3. Checklist di Migrazione Passo Passo

1. **Creare il dataset semplice**:
   In Superset, creare o selezionare il dataset puntando alla tabella fisica o vista snella.
2. **Aggiungere il filtro nativo**:
   Nella dashboard, creare un nuovo filtro nativo selezionando il tipo `Period comparison filter` (Filtro confronto periodi).
3. **Collegare i grafici**:
   Verificare che i grafici della dashboard abbiano attiva l'opzione `Follow dashboard comparison` (attiva per default).
4. **Validare i totali**:
   Controllare che i valori mostrati coincidano con i dati storici effettivi.
5. **Dismettere la vecchia vista**:
   Rimuovere la vecchia vista SQL o tabella di appoggio dal database, recuperando spazio disco e semplificando la manutenzione.
