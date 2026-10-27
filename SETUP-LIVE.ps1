$ErrorActionPreference = 'Stop'
$Host.UI.RawUI.WindowTitle = 'TaulSaathi - local Gnani key setup'
Set-Location -LiteralPath $PSScriptRoot
Write-Host 'TaulSaathi local live setup' -ForegroundColor Cyan
Write-Host 'Enter your Gnani API key below. It is masked and is not saved to a file.'
Write-Host 'This window starts the local server; keep it open during testing.'
Write-Host 'Speech buttons can use your programme credits. No requests run automatically.'
$taulSecureKey = Read-Host 'Gnani API key' -AsSecureString
$taulPlainKey = [System.Net.NetworkCredential]::new('', $taulSecureKey).Password
if ([string]::IsNullOrWhiteSpace($taulPlainKey)) {
    Write-Host 'No key entered. Nothing was started.'
    Read-Host 'Press Enter to close'
    exit 1
}
$env:GNANI_API_KEY = $taulPlainKey.Trim()
$taulPlainKey = $null
$taulSecureKey = $null
try {
    python app.py --port 8765
} finally {
    Remove-Item Env:GNANI_API_KEY -ErrorAction SilentlyContinue
}
Read-Host 'Server stopped. Press Enter to close'
