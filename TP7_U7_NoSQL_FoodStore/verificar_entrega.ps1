# ============================================================================
# TP Unidad 7 - Food Store NoSQL
# Autoevaluacion objetiva de la entrega.
#
# Comprueba archivos exigidos, integridad del modelo, equivalencia de
# resultados entre PostgreSQL y MongoDB y limite de paginas del PDF.
#
# Uso:
#   $env:PGPASSWORD="..."
#   .\verificar_entrega.ps1
#   .\verificar_entrega.ps1 -Psql "C:\...\psql.exe" -Mongosh "C:\...\mongosh.exe"
# ============================================================================
[CmdletBinding()]
param(
    [string]$Psql     = "psql",
    [string]$Mongosh  = "mongosh",
    [string]$PgHost   = "localhost",
    [string]$PgUser   = "postgres",
    [string]$PgDb     = "foodstore",
    [string]$MongoUri = "mongodb://127.0.0.1:27017/foodstore_nosql"
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $raiz

$checks = New-Object System.Collections.Generic.List[object]

function Agregar($criterio, $esperado, $obtenido) {
    $ok = ("$esperado" -eq "$obtenido")
    $checks.Add([pscustomobject]@{
        Criterio = $criterio
        Esperado = "$esperado"
        Obtenido = "$obtenido"
        OK       = $ok
    })
}

# ---------------------------------------------------------------------------
# 1. Archivos exigidos por la consigna y por la trazabilidad del TP.
# ---------------------------------------------------------------------------
$archivos = @(
    "consultas_mongodb.js",
    "consultas_postgresql.sql",
    "mongodb/01_crear_coleccion.js",
    "mongodb/02_datos_pedidos.js",
    "mongodb/03_verificacion_integridad.js",
    "sql/01_exportar_pedidos_mongodb.sql",
    "informe/Informe_TP_U7_NoSQL_FoodStore.pdf",
    "BITACORA_IA.md",
    "AUTOEVALUACION.md",
    "README.md"
)
foreach ($a in $archivos) {
    Agregar "Archivo presente: $a" "SI" $(if (Test-Path $a) { "SI" } else { "NO" })
}

# ---------------------------------------------------------------------------
# 2. Resumen PostgreSQL (mismo subconjunto y misma regla de estado).
# ---------------------------------------------------------------------------
$sqlPg = @'
WITH corte AS (
    SELECT max(fecha) + interval '1 day' AS f
    FROM pedido WHERE id BETWEEN 1 AND 12
),
lote AS (
    SELECT p.id,
           CASE WHEN p.fecha <= c.f - interval '30 days' THEN 'TERMINADO' ELSE 'PENDIENTE' END AS estado
    FROM pedido p CROSS JOIN corte c
    WHERE p.id BETWEEN 1 AND 12
),
totales AS (
    SELECT pedido_id, sum(cantidad * precio_unitario) AS total
    FROM linea_pedido WHERE pedido_id BETWEEN 1 AND 12
    GROUP BY pedido_id
),
b AS (
    SELECT count(*) AS n,
           string_agg(l.id::text, ',' ORDER BY l.id) AS ids,
           sum(t.total) AS imp
    FROM lote l JOIN totales t ON t.pedido_id = l.id
    WHERE l.estado = 'TERMINADO'
),
c AS (
    SELECT count(*) AS n,
           string_agg(id::text, ',' ORDER BY id) AS ids,
           sum(total) AS imp
    FROM (
        SELECT DISTINCT l.id, t.total
        FROM lote l
        JOIN linea_pedido lp ON lp.pedido_id = l.id
        JOIN totales t ON t.pedido_id = l.id
        WHERE lp.producto_id = 1
    ) s
)
SELECT json_build_object(
    'pedidos',          (SELECT count(*) FROM pedido WHERE id BETWEEN 1 AND 12),
    'lineas',           (SELECT count(*) FROM linea_pedido WHERE pedido_id BETWEEN 1 AND 12),
    'importe',          (SELECT sum(total) FROM totales),
    'b_cantidad',       (SELECT n FROM b),
    'b_ids',            (SELECT ids FROM b),
    'b_importe',        (SELECT imp FROM b),
    'c_cantidad',       (SELECT n FROM c),
    'c_ids',            (SELECT ids FROM c),
    'c_importe',        (SELECT imp FROM c),
    'huerfanas',        (SELECT count(*) FROM linea_pedido lp
                          WHERE lp.pedido_id BETWEEN 1 AND 12
                            AND NOT EXISTS (SELECT 1 FROM producto pr WHERE pr.id = lp.producto_id)),
    'lineas_invalidas', (SELECT count(*) FROM linea_pedido
                          WHERE pedido_id BETWEEN 1 AND 12
                            AND (cantidad <= 0 OR precio_unitario < 0)),
    'producto_ids',     (SELECT string_agg(producto_id::text, ',' ORDER BY producto_id)
                          FROM (SELECT DISTINCT producto_id FROM linea_pedido
                                 WHERE pedido_id BETWEEN 1 AND 12) s)
);
'@

$pgTexto = & $Psql -U $PgUser -h $PgHost -d $PgDb -t -A -c $sqlPg 2>$null
$pg = $pgTexto | ConvertFrom-Json

Agregar "Pedidos de origen en el lote" 12 $pg.pedidos
Agregar "Lineas de origen en el lote" 24 $pg.lineas
Agregar "Lineas huerfanas en PostgreSQL" 0 $pg.huerfanas
Agregar "Lineas con cantidad/importe invalido" 0 $pg.lineas_invalidas

# ---------------------------------------------------------------------------
# 3. Resumen MongoDB y comparacion cruzada.
# ---------------------------------------------------------------------------
$mongoTexto = & $Mongosh $MongoUri --quiet --file "mongodb/05_resumen_comparacion.js" 2>$null
$mongo = $mongoTexto | ConvertFrom-Json

Agregar "Documentos migrados en MongoDB" 12 $mongo.total_documentos
Agregar "Consulta a) cantidad de pedidos" 12 $mongo.a.cantidad

Agregar "Consulta b) cantidad PG" $pg.b_cantidad $mongo.b.cantidad
Agregar "Consulta b) IDs PG" $pg.b_ids ($mongo.b.ids -join ",")
Agregar "Consulta b) importe PG" $pg.b_importe $mongo.b.importe

Agregar "Consulta c) cantidad PG" $pg.c_cantidad $mongo.c.cantidad
Agregar "Consulta c) IDs PG" $pg.c_ids ($mongo.c.ids -join ",")
Agregar "Consulta c) importe PG" $pg.c_importe $mongo.c.importe

Agregar "Importe total PG" ("{0:F2}" -f [decimal]$pg.importe) ("{0:F2}" -f [decimal]$mongo.muestra.importe)
Agregar "Productos referenciados PG" $pg.producto_ids (
    (& $Mongosh $MongoUri --quiet --eval "print(db.getSiblingDB('foodstore_nosql').pedidos.distinct('items.producto_id').sort((a,b)=>a-b).join(','))" 2>$null)
)

# ---------------------------------------------------------------------------
# 4. Verificacion de integridad del motor documental.
# ---------------------------------------------------------------------------
$integridad = & $Mongosh $MongoUri --quiet --file "mongodb/03_verificacion_integridad.js" 2>$null
Agregar "Verificacion de integridad MongoDB" "OK" $(if ($integridad -match "RESULTADO: OK") { "OK" } else { "FALLO" })

# ---------------------------------------------------------------------------
# 5. Limite de cinco paginas del PDF unico.
# ---------------------------------------------------------------------------
$pdf = "informe/Informe_TP_U7_NoSQL_FoodStore.pdf"
if (Test-Path $pdf) {
    $paginas = python -c "import pypdf;print(len(pypdf.PdfReader(r'$pdf').pages))" 2>$null
    Agregar "Paginas del PDF <= 5 (obtenidas: $paginas)" "SI" $(
        if ([int]$paginas -le 5) { "SI" } else { "NO" }
    )
} else {
    Agregar "Paginas del PDF <= 5" "SI" "NO (PDF ausente)"
}

# ---------------------------------------------------------------------------
# 6. Informe de autoevaluacion.
# ---------------------------------------------------------------------------
$lineas = New-Object System.Collections.Generic.List[string]
$lineas.Add("AUTOEVALUACION OBJETIVA - TP U7 NoSQL Food Store")
$lineas.Add("Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lineas.Add("")
$lineas.Add(("{0,-58} {1,-10} {2,-34} {3}" -f "Criterio", "Esperado", "Obtenido", "Estado"))
$lineas.Add(("-" * 115))
foreach ($c in $checks) {
    $estado = if ($c.OK) { "OK" } else { "FALLA" }
    $lineas.Add(("{0,-58} {1,-10} {2,-34} {3}" -f $c.Criterio, $c.Esperado, $c.Obtenido, $estado))
}

$fallas = @($checks | Where-Object { -not $_.OK })
$lineas.Add("")
$lineas.Add("Comprobaciones: $($checks.Count) | Fallas: $($fallas.Count)")

$salida = "evidencia/verificacion_entrega.txt"
New-Item -ItemType Directory -Force -Path "evidencia" | Out-Null
$lineas | Set-Content -Path $salida -Encoding UTF8
$lineas | ForEach-Object { Write-Host $_ }

if ($fallas.Count -gt 0) {
    Write-Host ""
    Write-Host "RESULTADO: RECHAZADO - corregir las fallas y volver a ejecutar." -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "RESULTADO: APROBADO - la entrega cumple los criterios verificables." -ForegroundColor Green
exit 0
