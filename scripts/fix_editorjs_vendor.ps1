$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RootDir

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "npm was not found. Install Node.js/npm, then rerun this script."
}

if (Test-Path "package-lock.json") {
    $lock = Get-Content "package-lock.json" -Raw
    if ($lock -match "applied-caas|artifactory|openai\.org") {
        Copy-Item "package-lock.json" "package-lock.json.local-backup" -Force
        Remove-Item "package-lock.json" -Force
        Write-Host "Backed up package-lock.json to package-lock.json.local-backup and regenerated it from the public npm registry."
    }
}

npm install --registry=https://registry.npmjs.org/
npm run build-vendor
npm run build-css

Write-Host ""
Write-Host "EditorJS static files were rebuilt. Restart Django runserver, then reopen /new/ with cache disabled or hard refresh."
