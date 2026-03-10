# build-skill.ps1 - Generic skill builder
param([string]$Version = "")

Add-Type -AssemblyName System.IO.Compression.FileSystem

function New-UnixZip {
    param([string]$SourceDir, [string]$ZipPath)

    $destDir = Split-Path -Path $ZipPath
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force > $null
    }

    if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
    $zip = [System.IO.Compression.ZipFile]::Open($ZipPath, 'Create')
    Get-ChildItem -Path $SourceDir -Recurse -File | ForEach-Object {
        $basePath = $SourceDir.TrimEnd('\','/')
        $entry = $_.FullName.Substring($basePath.Length + 1).Replace('\','/')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, $_.FullName, $entry) > $null
    }
    $zip.Dispose()
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$parentDir = Split-Path -Parent $scriptDir
$skillName = Split-Path -Leaf $scriptDir
$releasesDir = Join-Path $scriptDir "releases_public"
$distPrivateDir = Join-Path $scriptDir "releases_private"

Write-Host "=== Skill Builder: $skillName ===" -ForegroundColor Cyan
Write-Host "Ubicacion: $scriptDir`n" -ForegroundColor Gray

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = Read-Host "Version (ej: 1.0.0)"
}
$version = $Version

if ([string]::IsNullOrWhiteSpace($version)) {
    Write-Host "Error: Version requerida" -ForegroundColor Red
    exit 1
}

# Verificar archivos necesarios
Write-Host "Verificando archivos..." -ForegroundColor Yellow
$requiredFiles = @("SKILL.md", "README.md", "LICENSE", ".env.example", "scripts")
foreach ($file in $requiredFiles) {
    $filePath = Join-Path $scriptDir $file
    if (-not (Test-Path $filePath)) {
        Write-Host "Falta: $file" -ForegroundColor Red
        exit 1
    }
}

$envFile = Join-Path $distPrivateDir ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Falta: .env en releases_private/" -ForegroundColor Red
    exit 1
}

# Limpiar zips privados legacy del directorio padre
$oldPrivate = Get-ChildItem -Path $parentDir -Filter "$skillName-v*-private.zip" -File
if ($oldPrivate) {
    Write-Host "Eliminando privados legacy del directorio padre..." -ForegroundColor Yellow
    $oldPrivate | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "   Eliminado: $($_.Name)" -ForegroundColor Gray
    }
}

# Limpiar dist_private anterior
if (Test-Path $distPrivateDir) {
    $oldDistPrivate = Get-ChildItem -Path $distPrivateDir -Filter "*.zip"
    if ($oldDistPrivate) {
        Write-Host "Eliminando dist_private anteriores..." -ForegroundColor Yellow
        $oldDistPrivate | ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "   Eliminado: $($_.Name)" -ForegroundColor Gray
        }
    }
} else {
    New-Item -ItemType Directory -Path $distPrivateDir -Force > $null
}

# Limpiar releases anteriores
if (Test-Path $releasesDir) {
    $oldReleases = Get-ChildItem -Path $releasesDir -Filter "*.zip"
    if ($oldReleases) {
        Write-Host "Eliminando releases anteriores..." -ForegroundColor Yellow
        $oldReleases | ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "   Eliminado: $($_.Name)" -ForegroundColor Gray
        }
    }
} else {
    New-Item -ItemType Directory -Path $releasesDir -Force > $null
}

# Archivos base a empaquetar
$baseItems = @(
    (Join-Path $scriptDir "SKILL.md"),
    (Join-Path $scriptDir "README.md"),
    (Join-Path $scriptDir "LICENSE"),
    (Join-Path $scriptDir "scripts")
)
$templatesDir = Join-Path $scriptDir "templates"
if (Test-Path $templatesDir) { $baseItems += $templatesDir }

# ── PUBLIC ────────────────────────────────────────────────────────────────────
Write-Host "`nConstruyendo PUBLICO..." -ForegroundColor Green
$temp = "$env:TEMP\skill-pub-$([System.Random]::new().Next())"
New-Item -ItemType Directory -Path $temp -Force > $null
$publicItems = $baseItems + @((Join-Path $scriptDir ".env.example"))
Copy-Item -Path $publicItems -Destination $temp -Recurse -Force
$publicZip = Join-Path $releasesDir "$skillName-v${version}-public.zip"
New-UnixZip -SourceDir $temp -ZipPath $publicZip
Remove-Item -Path $temp -Recurse -Force
Write-Host "   OK: $($publicZip | Split-Path -Leaf)" -ForegroundColor Green

# ── MASTER (todos los credenciales) ──────────────────────────────────────────
Write-Host "`nConstruyendo MASTER..." -ForegroundColor Magenta
$temp = "$env:TEMP\skill-master-$([System.Random]::new().Next())"
New-Item -ItemType Directory -Path $temp -Force > $null
Copy-Item -Path $baseItems -Destination $temp -Recurse -Force
Copy-Item -Path $envFile -Destination (Join-Path $temp ".env") -Force
$masterZip = Join-Path $distPrivateDir "$skillName-v${version}.zip"
New-UnixZip -SourceDir $temp -ZipPath $masterZip
Remove-Item -Path $temp -Recurse -Force
Write-Host "   OK: $($masterZip | Split-Path -Leaf)  [TODOS los credenciales]" -ForegroundColor Magenta

# ── PER-CLIENT ZIPs ───────────────────────────────────────────────────────────
# Detecta clientes buscando variables con prefijo {SKILLSHORTNAME}_{CLIENT}_*
# Ej: skill-holded → HOLDED_ → clientes SPIRAL, REALFLOOW, ENZO, etc.
$skillShortName = ($skillName -replace '^skill-', '').ToUpper().Replace('-', '_')
$envPrefix = "${skillShortName}_"
Write-Host "`nDetectando clientes (prefijo env: $envPrefix)..." -ForegroundColor Cyan

$clientGroups = @{}
foreach ($line in (Get-Content $envFile)) {
    $trimmed = $line.Trim()
    if ($trimmed -match '^\s*#' -or [string]::IsNullOrWhiteSpace($trimmed)) { continue }
    if ($trimmed -match '^([A-Z0-9_]+)=(.*)$') {
        $varName = $Matches[1]
        if ($varName.StartsWith($envPrefix)) {
            $clientName = $varName.Substring($envPrefix.Length).Split('_')[0]
            if (-not $clientGroups.ContainsKey($clientName)) {
                $clientGroups[$clientName] = [System.Collections.Generic.List[string]]::new()
            }
            $clientGroups[$clientName].Add($trimmed)
        }
    }
}

if ($clientGroups.Count -eq 0) {
    Write-Host "   Aviso: no se detectaron clientes con prefijo $envPrefix" -ForegroundColor Yellow
} else {
    foreach ($clientName in ($clientGroups.Keys | Sort-Object)) {
        Write-Host "`nConstruyendo cliente: $clientName..." -ForegroundColor Cyan
        $temp = "$env:TEMP\skill-client-$([System.Random]::new().Next())"
        New-Item -ItemType Directory -Path $temp -Force > $null
        Copy-Item -Path $baseItems -Destination $temp -Recurse -Force

        # .env con solo las variables de este cliente
        $lines = @("# $skillName credentials - $clientName") + $clientGroups[$clientName]
        Set-Content -Path (Join-Path $temp ".env") -Value $lines -Encoding UTF8

        $clientZip = Join-Path $distPrivateDir "$skillName-v${version}_$clientName.zip"
        New-UnixZip -SourceDir $temp -ZipPath $clientZip
        Remove-Item -Path $temp -Recurse -Force
        Write-Host "   OK: $($clientZip | Split-Path -Leaf)" -ForegroundColor Cyan
    }
}

# ── RESUMEN ────────────────────────────────────────────────────────────────────
Write-Host "`n=== Resumen ===" -ForegroundColor White
Write-Host "Publico  → releases_public/" -ForegroundColor Green
Get-ChildItem -Path $releasesDir -Filter "*.zip" | ForEach-Object { Write-Host "   $($_.Name)" -ForegroundColor Gray }
Write-Host "Privados → releases_private/" -ForegroundColor Magenta
Get-ChildItem -Path $distPrivateDir -Filter "*.zip" | ForEach-Object { Write-Host "   $($_.Name)" -ForegroundColor Gray }
Write-Host "`nHecho!" -ForegroundColor Cyan
