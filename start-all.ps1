Set-Location "C:\Projects\Relulu\ReLuLu"

# Backend
Start-Process -FilePath "C:\Projects\Relulu\ReLuLu\backend\.venv\Scripts\python.exe" -ArgumentList "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory "C:\Projects\Relulu\ReLuLu\backend"

# Frontend
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory "C:\Projects\Relulu\ReLuLu\frontend"

Write-Host "Backend: http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"