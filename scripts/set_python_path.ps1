# PowerShell Script to add Python to the System PATH
# IMPORTANT: This script must be run in a PowerShell window that was started "As Administrator".

try {
    # Paths to be added
    $pythonPath = "C:\Users\pasca\AppData\Local\Programs\Python\Python313"
    $scriptsPath = "C:\Users\pasca\AppData\Local\Programs\Python\Python313\Scripts"

    # --- Update System PATH (requires Admin rights) ---
    Write-Host "Updating System PATH (requires Admin rights)..."
    
    # Get current System PATH
    $systemPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    
    # Add Python path if it doesn't exist
    if (-not $systemPath.Contains($pythonPath)) {
        $newSystemPath = $systemPath + ";" + $pythonPath
        [System.Environment]::SetEnvironmentVariable("Path", $newSystemPath, "Machine")
        Write-Host "- Python directory added to System PATH."
    } else {
        Write-Host "- Python directory is already in the System PATH."
    }

    # Get path again in case it was just added
    $systemPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    if (-not $systemPath.Contains($scriptsPath)) {
        $newSystemPath = $systemPath + ";" + $scriptsPath
        [System.Environment]::SetEnvironmentVariable("Path", $newSystemPath, "Machine")
        Write-Host "- Python Scripts directory added to System PATH."
    } else {
        Write-Host "- Python Scripts directory is already in the System PATH."
    }

    Write-Host ""
    Write-Host "SUCCESS: The System PATH has been updated." -ForegroundColor Green
    Write-Host "IMPORTANT: Please close this Admin PowerShell window and open a NEW, normal PowerShell window for the changes to take effect."

} catch {
    Write-Host ""
    Write-Host "ERROR: An error occurred." -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host "Please ensure you are running this script from a PowerShell window started 'As Administrator'."
}

# Pause to allow the user to read the message
Write-Host "This window will close in 10 seconds."
Start-Sleep -Seconds 10