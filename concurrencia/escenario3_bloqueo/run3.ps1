$ErrorActionPreference = 'Stop'
$dir = 'C:\UTN\3er semestre\Bases de Datos II\UNIDAD 1\concurrencia\escenario3_bloqueo'
$env:PGPASSWORD = 'postgres'
Remove-Item (Join-Path $dir 'salida_A.txt'),(Join-Path $dir 'salida_B.txt') -ErrorAction SilentlyContinue
$qA = '"' + (Join-Path $dir 'sA.sql') + '"'
$qB = '"' + (Join-Path $dir 'sB.sql') + '"'
Write-Host '>>> t0: A bloquea fila 1 y duerme 5s'
$pA = Start-Process psql -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qA) -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $dir 'salida_A.txt') -RedirectStandardError (Join-Path $dir 'err_A.txt')
Start-Sleep -Seconds 2
Write-Host '>>> t+2s: B intenta FOR UPDATE sobre la misma fila'
$pB = Start-Process psql -ArgumentList @('-U','postgres','-h','localhost','-d','foodstore_tp2','-X','-f',$qB) -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $dir 'salida_B.txt') -RedirectStandardError (Join-Path $dir 'err_B.txt')
$pA.WaitForExit(); $pB.WaitForExit()
Write-Host '=== SESION A ==='; Get-Content (Join-Path $dir 'salida_A.txt')
Write-Host '=== SESION B (timestamps muestran la espera) ==='; Get-Content (Join-Path $dir 'salida_B.txt')