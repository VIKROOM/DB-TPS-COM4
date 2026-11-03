# ============================================================================
# TP Unidad 7 - Food Store NoSQL
# Reproduce de punta a punta: extraccion desde PostgreSQL, creacion de la
# coleccion, carga, verificacion de integridad y consultas de ambos motores.
#
# Uso (desde la raiz de TP7_U7_NoSQL_FoodStore):
#   $env:PGPASSWORD="..."   # o configurar pgpass.conf
#   .\reproducir.ps1
#
# Si psql/mongosh no estan en el PATH, indicar las rutas:
#   .\reproducir.ps1 -Psql "C:\Program Files\PostgreSQL\17\bin\psql.exe" `
#                    -Mongosh "C:\...\mongosh.exe"
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

function Ejecutar($descripcion, $bloque) {
    Write-Host ""
    Write-Host "== $descripcion ==" -ForegroundColor Cyan
    & $bloque
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo: $descripcion (codigo $LASTEXITCODE)"
    }
}

Write-Host "TP7 U7 - Food Store NoSQL" -ForegroundColor Green
Write-Host "Raiz: $raiz"

Ejecutar "1/7 Extraer pedidos 1-12 desde PostgreSQL" {
    & $Psql -U $PgUser -h $PgHost -d $PgDb -v ON_ERROR_STOP=1 `
        -f "sql/01_exportar_pedidos_mongodb.sql" 2>&1 |
        Tee-Object -FilePath "evidencia/postgres_00_extraccion.txt"
}

Ejecutar "2/7 Crear base, coleccion, indices y metadatos" {
    & $Mongosh $MongoUri --quiet --file "mongodb/01_crear_coleccion.js" 2>&1 |
        Tee-Object -FilePath "evidencia/mongo_01_crear_coleccion.txt"
}

Ejecutar "3/7 Cargar documentos con insertMany()" {
    & $Mongosh $MongoUri --quiet --file "mongodb/02_datos_pedidos.js" 2>&1 |
        Tee-Object -FilePath "evidencia/mongo_02_carga.txt"
}

Ejecutar "4/7 Verificar integridad de los documentos" {
    & $Mongosh $MongoUri --quiet --file "mongodb/03_verificacion_integridad.js" 2>&1 |
        Tee-Object -FilePath "evidencia/mongo_03_verificacion_integridad.txt"
}

Ejecutar "5/7 Ejecutar consultas MongoDB (consigna 4)" {
    & $Mongosh $MongoUri --quiet --file "consultas_mongodb.js" 2>&1 |
        Tee-Object -FilePath "evidencia/mongo_04_consultas.txt"
}

Ejecutar "6/7 Ejecutar consultas PostgreSQL (consigna 5)" {
    & $Psql -U $PgUser -h $PgHost -d $PgDb -v ON_ERROR_STOP=1 `
        -f "consultas_postgresql.sql" 2>&1 |
        Tee-Object -FilePath "evidencia/postgres_01_consultas.txt"
}

Ejecutar "7/7 Resumen comparable MongoDB" {
    & $Mongosh $MongoUri --quiet --file "mongodb/05_resumen_comparacion.js" 2>&1 |
        Tee-Object -FilePath "evidencia/mongo_05_resumen_comparacion.txt"
}

Write-Host ""
Write-Host "Reproduccion completa. Ejecutar .\verificar_entrega.ps1 para la autoevaluacion." -ForegroundColor Green
