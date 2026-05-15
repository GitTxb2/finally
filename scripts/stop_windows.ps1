<#
.SYNOPSIS
    Stop and remove the FinAlly container. The named volume (finally-data) is preserved.

.EXAMPLE
    .\scripts\stop_windows.ps1
#>
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$Container = 'finally'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'docker is not installed or not on PATH.'
    exit 1
}

docker container inspect $Container *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Stopping $Container..."
    docker rm -f $Container *> $null
    Write-Host "Stopped. Data volume 'finally-data' is preserved."
} else {
    Write-Host "Container $Container is not running. Nothing to do."
}
