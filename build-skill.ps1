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
$releasesDir = Join-Path $scriptDir "releases"

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

$envFile = Join-Path $parentDir "$skillName.env"
if (-not (Test-Path $envFile)) {
    Write-Host "Falta: $skillName.env en $parentDir" -ForegroundColor Red
    exit 1
}

# Limpiar zips privados anteriores
$oldPrivate = Get-ChildItem -Path $parentDir -Filter "$skillName-v*-private.zip" -File
if ($oldPrivate) {
    Write-Host "Eliminando privados anteriores..." -ForegroundColor Yellow
    $oldPrivate | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "   $_" -ForegroundColor Gray
    }
}

# Limpiar releases anteriores
if (Test-Path $releasesDir) {
    $oldReleases = Get-ChildItem -Path $releasesDir -Filter "*.zip"
    if ($oldReleases) {
        Write-Host "Eliminando releases anteriores..." -ForegroundColor Yellow
        $oldReleases | ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "   $_" -ForegroundColor Gray
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

# PUBLIC
Write-Host "`nConstruyendo PUBLICO..." -ForegroundColor Green
$temp = "$env:TEMP\skill-pub-$([System.Random]::new().Next())"
New-Item -ItemType Directory -Path $temp -Force > $null
$publicItems = $baseItems + @((Join-Path $scriptDir ".env.example"))
Copy-Item -Path $publicItems -Destination $temp -Recurse -Force
$publicZip = Join-Path $releasesDir "$skillName-v${version}-public.zip"
New-UnixZip -SourceDir $temp -ZipPath $publicZip
Remove-Item -Path $temp -Recurse -Force
Write-Host "   OK $publicZip" -ForegroundColor Green

# PRIVATE
Write-Host "`nConstruyendo PRIVADO..." -ForegroundColor Green
$temp = "$env:TEMP\skill-priv-$([System.Random]::new().Next())"
New-Item -ItemType Directory -Path $temp -Force > $null
Copy-Item -Path $baseItems -Destination $temp -Recurse -Force
Copy-Item -Path $envFile -Destination (Join-Path $temp ".env") -Force
$privateZip = Join-Path $parentDir "$skillName-v${version}-private.zip"
New-UnixZip -SourceDir $temp -ZipPath $privateZip
Remove-Item -Path $temp -Recurse -Force
Write-Host "   OK $privateZip (incluye .env con credenciales)" -ForegroundColor Green

Write-Host "`nHecho!" -ForegroundColor Cyan
