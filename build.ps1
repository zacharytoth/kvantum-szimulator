param (
    [switch]$Clean
)

Write-Host "BB84_Simulator build indítása..." -ForegroundColor Cyan

if ($Clean) {
    Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
}

# Ellenőrizzük a virtuális környezetet
if (-not (Test-Path ".\.venv\Scripts\pyinstaller.exe")) {
    Write-Error "A .venv virtuális környezet nincs inicializálva!"
    exit 1
}

.\.venv\Scripts\pyinstaller.exe `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "BB84_Simulator" `
    --collect-data customtkinter `
    main.py

if ($LASTEXITCODE -eq 0) {
    $exeSize = (Get-Item "dist\BB84_Simulator.exe").Length / 1MB
    Write-Host ("Sikeres build! Méret: {0:N2} MB" -f $exeSize) -ForegroundColor Green
} else {
    Write-Error "A build meghiúsult!"
}