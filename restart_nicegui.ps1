# NiceGUI uygulamasını yeniden başlat
Write-Host "NiceGUI uygulaması durduruluyor..."

# Port 8080'i kullanan process'i bul ve durdur
$process = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($process) {
    Write-Host "Process bulundu: $process"
    Stop-Process -Id $process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Host "NiceGUI uygulaması başlatılıyor..."
python app_nicegui.py

