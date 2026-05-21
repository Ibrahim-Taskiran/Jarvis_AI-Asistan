#Requires -RunAsAdministrator

$taskName = "JARVIS"
$batPath  = "C:\Users\ibrah\Documents\GitHub\Jarvis\start_jarvis.bat"
$userName = "$env:USERDOMAIN\$env:USERNAME"

# Remove existing task if present
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing '$taskName' scheduled task."
}

# Trigger: At logon of the current user
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $userName

# Action: Run start_jarvis.bat hidden via cmd /c start /min
# Using 'cmd' wrapper with /min to minimize the console window
$action = New-ScheduledTaskAction `
    -Execute "cmd.exe" `
    -Argument "/c start /min `"`" `"$batPath`"" `
    -WorkingDirectory "C:\Users\ibrah\Documents\GitHub\Jarvis"

# Settings: allow start when on battery, don't stop on battery switch, no time limit
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable `
    -Hidden

# Principal: run with highest privileges (bypasses UAC)
$principal = New-ScheduledTaskPrincipal `
    -UserId $userName `
    -RunLevel Highest `
    -LogonType Interactive

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Trigger $trigger `
    -Action $action `
    -Settings $settings `
    -Principal $principal `
    -Description "Launch JARVIS AI Desktop Assistant silently at login with elevated privileges." `
    -Force

Write-Host ""
Write-Host "=== Task Scheduler Setup Complete ==="
Write-Host "Task Name   : $taskName"
Write-Host "Trigger     : At logon ($userName)"
Write-Host "Action      : $batPath"
Write-Host "Privileges  : Highest (no UAC prompt)"
Write-Host "Hidden      : Yes"
Write-Host ""

# Show the registered task
Get-ScheduledTask -TaskName $taskName | Format-List TaskName, State, Description
Get-ScheduledTaskInfo -TaskName $taskName | Format-List LastRunTime, NextRunTime, LastTaskResult
