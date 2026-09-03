param([string]$sA)
# Orquestador generico escenario 2: $sA = sA_rc.sql o sA_rr.sql
# Usa un nombre de salida propio por script para no pisar la evidencia.
$ErrorActionPreference = 'Stop'
$dir = 'C:\UTN\3er semestre\Bases de Datos II\UNIDAD 1\concurrencia\escenario2_fantasma'
$env:PGPASSWORD = 'postgres'
$tag = ($sA -replace '^sA_','' -replace '\.sql$','')
$outA = Join-Path $dir ("salida_A_{0}.txt" -f $tag)
Remove-Item $outA,(Join-Path $dir 'salida_B.txt') -ErrorAction SilentlyContinue
$qA = '"' + (Join-Path $dir $sA) + '"'
$qB = '"' + (Join-Path $dir 'sB2.sql') + '"'
$pA = Start-Process psql -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qA) -NoNewWindow -PassThru -RedirectStandardOutput $outA -RedirectStandardError (Join-Path $dir 'err_A.txt')
Start-Sleep -Seconds 2
$pB = Start-Process psql -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qB) -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $dir 'salida_B.txt') -RedirectStandardError (Join-Path $dir 'err_B.txt')
$pA.WaitForExit(); $pB.WaitForExit()
Write-Host "=== SESION A ($sA) ==="; Get-Content $outA
Write-Host '=== SESION B ==='; Get-Content (Join-Path $dir 'salida_B.txt')