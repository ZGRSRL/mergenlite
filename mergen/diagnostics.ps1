# ZgrBid System Diagnostics Script
Write-Host "=== ZgrBid System Diagnostics ===" -ForegroundColor Green

# Check ports
Write-Host "`n1. Checking Port Usage:" -ForegroundColor Yellow
$ports = @(3000, 8000, 8001, 5432)
foreach ($port in $ports) {
    $process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($process) {
        $pid = $process.OwningProcess
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        Write-Host "Port $port is in use by PID $pid ($($proc.ProcessName))" -ForegroundColor Red
    } else {
        Write-Host "Port $port is available" -ForegroundColor Green
    }
}

# Check Docker
Write-Host "`n2. Checking Docker:" -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "Docker: $dockerVersion" -ForegroundColor Green
    
    $containers = docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    Write-Host "`nContainers:" -ForegroundColor Cyan
    Write-Host $containers
} catch {
    Write-Host "Docker not found or not running" -ForegroundColor Red
}

# Check Python packages
Write-Host "`n3. Checking Python Packages:" -ForegroundColor Yellow
$packages = @("fastapi", "uvicorn", "sqlalchemy", "psycopg", "pydantic-settings")
foreach ($pkg in $packages) {
    try {
        $version = python -c "import $pkg; print($pkg.__version__)" 2>$null
        if ($version) {
            Write-Host "$pkg: $version" -ForegroundColor Green
        } else {
            Write-Host "$pkg: Not installed" -ForegroundColor Red
        }
    } catch {
        Write-Host "$pkg: Not installed" -ForegroundColor Red
    }
}

# Check Node.js
Write-Host "`n4. Checking Node.js:" -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Host "Node.js: $nodeVersion" -ForegroundColor Green
    Write-Host "NPM: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js not found" -ForegroundColor Red
}

# Check PostgreSQL connection
Write-Host "`n5. Checking PostgreSQL Connection:" -ForegroundColor Yellow
try {
    $env:PGPASSWORD = "zgrpw"
    $result = psql -h 127.0.0.1 -U zgr -d zgrsam -c "SELECT version();" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL connection successful" -ForegroundColor Green
    } else {
        Write-Host "PostgreSQL connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "PostgreSQL not accessible" -ForegroundColor Red
}

Write-Host "`n=== Diagnostics Complete ===" -ForegroundColor Green



