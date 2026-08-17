$GhBin = Join-Path $PSScriptRoot ".tools\gh-2.94.0\bin"
$env:Path = "$GhBin;$env:Path"

Write-Host "GitHub CLI is ready in this session." -ForegroundColor Green
gh --version
Write-Host ""
Write-Host "To sign in, run:" -ForegroundColor Yellow
Write-Host "  gh auth login --hostname github.com --git-protocol ssh --web"
