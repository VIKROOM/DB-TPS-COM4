param([string]$sA)
# Orquestador generico: sA = archivo de sesion A (rc o rr)
$ErrorActionPreference = 'Stop'
$dir = 'C:\UTN\3er semestre\Bases de Datos II\UNIDAD 1\concurrencia\escenario2_fantasma'
$env:PGPASSWORD = 'postgres'
Remove-Item (Join-Path $dir 'salida_A.txt'),(Join-Path $dir 'salida_B.txt') -ErrorAction SilentlyContinue
$qA = '"' + (Join-Path $dir $sA) + '"'
$qB = '"' + (Join-Path $dir 'sB2.sql') + '"'
$pA = Start-Process psql -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qA) -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $dir 'salida_A.txt') -RedirectStandardError (Join-Path $dir 'err_A.txt')
Start-Sleep -Seconds 2
$pB = Start-Process psql -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qB) -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $dir 'salida_B.txt') -RedirectStandardError (Join-Path $dir 'err_B.txt')
$pA.WaitForExit(); $pB.WaitForExit()
Write-Host '=== SESION A ==='; Get-Content (Join-Path $dir 'salida_A.txt')
Write-Host '=== SESION B ==='; Get-Content (Join-Path $dir 'salida_B.txt')
