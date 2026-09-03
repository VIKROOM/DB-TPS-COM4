# ============================================================================
# Orquestador Escenario 1 - Lectura no repetible (READ COMMITTED)
# Lanza SESION A (sA_rr.sql) y SESION B (sB1.sql) en paralelo con psql.
# Los paths con espacios van entre comillas para psql.
# ============================================================================
$ErrorActionPreference = 'Stop'
$dir = 'C:\UTN\3er semestre\Bases de Datos II\UNIDAD 1\concurrencia\escenario1_no_repetible'
$env:PGPASSWORD = 'postgres'

Remove-Item (Join-Path $dir 'salida_A_rr.txt'), (Join-Path $dir 'salida_B.txt'), (Join-Path $dir 'err_A.txt'), (Join-Path $dir 'err_B.txt') -ErrorAction SilentlyContinue

$qA = '"' + (Join-Path $dir 'sA_rr.sql') + '"'
$qB = '"' + (Join-Path $dir 'sB1.sql') + '"'

Write-Host '=== LANZANDO SESION A (READ COMMITTED) ==='
$procA = Start-Process -FilePath 'psql' -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qA) `
    -NoNewWindow -PassThru `
    -RedirectStandardOutput (Join-Path $dir 'salida_A_rr.txt') -RedirectStandardError (Join-Path $dir 'err_A.txt')

Start-Sleep -Seconds 2
Write-Host '=== LANZANDO SESION B (actualiza precio 800 -> 850 y COMMIT) ==='
$procB = Start-Process -FilePath 'psql' -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qB) `
    -NoNewWindow -PassThru `
    -RedirectStandardOutput (Join-Path $dir 'salida_B.txt') -RedirectStandardError (Join-Path $dir 'err_B.txt')

$procA.WaitForExit()
$procB.WaitForExit()

Write-Host ''
Write-Host '================ SALIDA SESION A (READ COMMITTED) ================'
Get-Content (Join-Path $dir 'salida_A_rr.txt')
Write-Host ''
Write-Host '================ SALIDA SESION B ================'
Get-Content (Join-Path $dir 'salida_B.txt')
