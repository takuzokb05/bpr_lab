$env:GEMINI_API_KEY = "AIzaSyC6Z8PHJe_fpuwf4HysOtyLRdTWaOTfD1k"
$nodePath = Get-Command node -ErrorAction SilentlyContinue
if ($nodePath) {
    Write-Host "Node.js found at $($nodePath.Source)"
    node data/generate-image.js "cute cat illustration" "images/cat.png"
    if (Test-Path "images/cat.png") {
        Write-Host "Success: Image created at images/cat.png" -ForegroundColor Green
    } else {
        Write-Host "Error: Image generation failed." -ForegroundColor Red
    }
} else {
    Write-Host "Error: Node.js not found in this PowerShell session." -ForegroundColor Red
}
