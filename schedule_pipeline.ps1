param(
    [string]$TaskName = "Monterey Capstone Data Refresh",
    [string]$Time = "03:00"
)

$project = (Get-Location).Path
$python = Join-Path $project ".venv\Scripts\python.exe"
$runner = Join-Path $project "run_pipeline.py"

if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment not found. Run: python -m venv .venv"
}

$action = New-ScheduledTaskAction -Execute $python -Argument "`"$runner`"" -WorkingDirectory $project
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description "Refresh Monterey public health data" -Force
Write-Host "Scheduled '$TaskName' daily at $Time."
