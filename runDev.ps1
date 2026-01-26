Write-Host "STARTING FAST API"
Start-Process powershell "-NoExit", `
  "cd blog-app/backend; venv\Scripts\python -m uvicorn main:app --reload"

Write-Host "STARTING FRONTEND"
Start-Process powershell "-NoExit", `
  "cd blog-app/frontend; npm run dev"
Start-Sleep -Seconds 3

Write-Host "OPENING IN CHROME"
Start-Process "chrome.exe" "http://localhost:5173"