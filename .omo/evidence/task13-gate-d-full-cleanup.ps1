$ErrorActionPreference = "Continue"
$root = (Get-Location).Path
$evidenceDir = Join-Path $root ".omo/evidence"
$procPath = Join-Path $evidenceDir "task13-gate-d-full-process-check.txt"
$pycachePath = Join-Path $evidenceDir "task13-gate-d-full-pycache-cleanup.txt"
$startCutoff = [datetime]"2026-08-05T10:53:57.7975733+08:00"
$now = Get-Date
Set-Content -Encoding UTF8 -Path $procPath -Value ("Process check at " + $now.ToString("o"))
Add-Content -Encoding UTF8 -Path $procPath -Value "Looking for python/pytest processes with command line referencing repo or pytest command; no unscoped termination performed."
$procs = Get-CimInstance Win32_Process -Filter "name = 'python.exe' or name = 'python3.exe' or name = 'py.exe'" | Where-Object { $_.CommandLine -like "*pytest*" -or $_.CommandLine -like "*多流派新思路*" }
if ($procs) { $procs | Select-Object ProcessId,Name,CommandLine | Format-List | Out-String | Add-Content -Encoding UTF8 -Path $procPath } else { Add-Content -Encoding UTF8 -Path $procPath -Value "No scoped python/pytest processes found." }
Set-Content -Encoding UTF8 -Path $pycachePath -Value ("Pycache cleanup at " + $now.ToString("o"))
Add-Content -Encoding UTF8 -Path $pycachePath -Value ("Criteria: __pycache__ dirs under " + $root + " with LastWriteTime >= " + $startCutoff.ToString("o"))
$rootFull = [System.IO.Path]::GetFullPath($root)
$dirs = Get-ChildItem -Path $root -Directory -Recurse -Force -Filter "__pycache__" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $startCutoff }
if ($dirs) {
  foreach ($d in $dirs) {
    $full = [System.IO.Path]::GetFullPath($d.FullName)
    if ($full.StartsWith($rootFull)) {
      Add-Content -Encoding UTF8 -Path $pycachePath -Value ("REMOVED " + $full + " LastWriteTime=" + $d.LastWriteTime.ToString("o"))
      Remove-Item -LiteralPath $full -Recurse -Force -ErrorAction SilentlyContinue
    } else {
      Add-Content -Encoding UTF8 -Path $pycachePath -Value ("SKIPPED_OUTSIDE_ROOT " + $full)
    }
  }
} else { Add-Content -Encoding UTF8 -Path $pycachePath -Value "No scoped __pycache__ directories found." }
"__PROCESS_CHECK__"
Get-Content $procPath
"__PYCACHE_CLEANUP__"
Get-Content $pycachePath
