# Guida all'Installazione e Manutenzione

Questo documento descrive le opzioni di installazione, verifica, rollback e deployment in produzione di Superset Period Compare.

## 1. Comandi Rapidi Batch

Nella radice del repository sono presenti quattro script batch pronti per Windows:

| File | Finalita | Esempio di utilizzo |
|:---|:---|:---|
| `verify.bat` | Verifica l'integrita della cartella target e lo stato della patch | `verify.bat D:\Superset` |
| `dry-run.bat` | Simula l'installazione senza modificare alcun file | `dry-run.bat D:\Superset` |
| `install.bat` | Crea backup, applica la patch e aggiorna MainPreset.ts | `install.bat D:\Superset` |
| `uninstall.bat` | Esegue il rollback byte per byte ripristinando l'albero originale | `uninstall.bat D:\Superset` |

Tutti gli script accettano come primo parametro il percorso della root di Superset 6.1.0. Se non specificato, il percorso viene rilevato automaticamente cercando nelle cartelle adiacenti.

## 2. Opzioni da PowerShell CLI

L'orchestratore puo essere invocato direttamente da PowerShell con parametri avanzati:

```powershell
powershell -ExecutionPolicy Bypass -File installer\PeriodCompare.ps1 -Action Install -TargetDir "D:\MioSuperset" -SkipBuild
```

### Parametri supportati:
- `-Action`: operazione richiesta (`Install`, `Uninstall`, `Verify`, `DryRun`).
- `-TargetDir`: percorso completo della cartella di Apache Superset.
- `-SkipBuild`: salta la ricompilazione npm degli asset frontend (utile durante prove o quando la build viene eseguita in container Docker).
- `-BackupDir`: percorso specifico di un backup precedente da ripristinare con `Uninstall`. Se omesso, viene utilizzato automaticamente il backup piu recente presente in `.backups/`.

## 3. Politica di Backup e Rollback Idempotente

1. **Creazione Automatica del Backup**:
   Prima di modificare qualsiasi file su disco, l'installer crea una cartella `.backups\backup_YYYYMMDD_HHMMSS\` all'interno della cartella di destinazione.
2. **Manifest JSON di Integrita**:
   All'interno del backup viene salvato il file `backup-manifest.json`, contenente per ciascun file il percorso relativo, l'hash SHA-256 e l'azione originale (modificato o aggiunto).
3. **Idempotenza Garantita**:
   Se si lancia `install.bat` su un ambiente gia patchato, l'installer rileva la presenza dei marcatori e non sovrascrive il backup originale ne duplica le registrazioni.
4. **Rollback Perfetto**:
   Eseguendo `uninstall.bat`, ogni file modificato viene ricollocato nella sua esatta versione originaria, mentre tutti i file aggiunti da Period Compare vengono rimossi.

## 4. Integrazione in Ambienti Docker

Per ambienti containerizzati basati su Dockerfile:
1. Copiare la cartella `payload` all'interno dell'immagine prima della fase di build frontend:
   ```dockerfile
   COPY superset-period-compare/payload /app/superset-src
   ```
2. Oppure montare la cartella ed eseguire `install.bat` / `PeriodCompare.ps1` durante lo scaffolding dell'immagine prima di `npm run build`.
3. Verificare che la variabile di configurazione contenga `DATE_RANGE_TIMESHIFTS_ENABLED = True` nel proprio `superset_config.py`.
