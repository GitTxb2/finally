<#
.SYNOPSIS
    Start the FinAlly container on Windows. Idempotent: safe to run repeatedly.

.PARAMETER Build
    Force rebuild of the Docker image before starting.

.PARAMETER Open
    Open the default browser to the app once the container is started.

.EXAMPLE
    .\scripts\start_windows.ps1
    .\scripts\start_windows.ps1 -Build
    .\scripts\start_windows.ps1 -Open
#>
[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$Open
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = Resolve-Path (Join-Path $ScriptDir '..')
Set-Location $RepoRoot

$Image     = 'finally:latest'
$Container = 'finally'
$Volume    = 'finally-data'
$Port      = 8000

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'docker is not installed or not on PATH.'
    exit 1
}

$envPath = Join-Path $RepoRoot '.env'
if (-not (Test-Path $envPath)) {
    $examplePath = Join-Path $RepoRoot '.env.example'
    if (Test-Path $examplePath) {
        Write-Host 'No .env found — creating one from .env.example.'
        Copy-Item $examplePath $envPath
        Write-Host 'Edit .env to set OPENROUTER_API_KEY before using the AI chat.'
    } else {
        Write-Error '.env not found and no .env.example to copy from.'
        exit 1
    }
}

# Check whether image exists.
$imageExists = $false
try {
    docker image inspect $Image *> $null
    if ($LASTEXITCODE -eq 0) { $imageExists = $true }
} catch { $imageExists = $false }

if ($Build -or -not $imageExists) {
    Write-Host "Building image $Image..."
    docker build -t $Image .
    if ($LASTEXITCODE -ne 0) { throw "docker build failed (exit $LASTEXITCODE)" }
}

# Ensure named volume exists.
docker volume inspect $Volume *> $null
if ($LASTEXITCODE -ne 0) {
    docker volume create $Volume *> $null
}

# Inspect any pre-existing container with this name.
$containerExists = $false
try {
    docker container inspect $Container *> $null
    if ($LASTEXITCODE -eq 0) { $containerExists = $true }
} catch { $containerExists = $false }

if ($containerExists) {
    $state = (docker inspect -f '{{.State.Status}}' $Container).Trim()
    switch ($state) {
        'running' {
            Write-Host "Container $Container is already running."
        }
        'paused' {
            Write-Host "Unpausing $Container..."
            docker unpause $Container *> $null
        }
        default {
            Write-Host "Removing stopped container $Container and recreating..."
            docker rm -f $Container *> $null
            docker run -d `
                --name $Container `
                --restart unless-stopped `
                -p "${Port}:8000" `
                -v "${Volume}:/app/db" `
                --env-file .env `
                $Image *> $null
            if ($LASTEXITCODE -ne 0) { throw "docker run failed (exit $LASTEXITCODE)" }
        }
    }
} else {
    Write-Host "Starting $Container..."
    docker run -d `
        --name $Container `
        --restart unless-stopped `
        -p "${Port}:8000" `
        -v "${Volume}:/app/db" `
        --env-file .env `
        $Image *> $null
    if ($LASTEXITCODE -ne 0) { throw "docker run failed (exit $LASTEXITCODE)" }
}

$Url = "http://localhost:$Port"
Write-Host "FinAlly is starting at $Url"
Write-Host "Tail logs:  docker logs -f $Container"
Write-Host "Stop with:  .\scripts\stop_windows.ps1"

if ($Open) {
    Start-Process $Url
}
