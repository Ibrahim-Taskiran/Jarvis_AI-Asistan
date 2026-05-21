# === Step 1: Convert PNG to ICO ===
Add-Type -AssemblyName System.Drawing

$pngPath = "C:\Users\ibrah\.gemini\antigravity\brain\6c803a1b-bbcb-4fb0-819b-3a6b0c96b229\jarvis_icon_1779269469382.png"
$icoPath = "C:\Users\ibrah\Documents\GitHub\Jarvis\jarvis.ico"

$png = [System.Drawing.Image]::FromFile($pngPath)
$resized = New-Object System.Drawing.Bitmap($png, 256, 256)

# Save resized as PNG to memory
$ms = New-Object System.IO.MemoryStream
$resized.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
$iconData = $ms.ToArray()

# Write ICO format
$fs = [System.IO.File]::Create($icoPath)
$bw = New-Object System.IO.BinaryWriter($fs)
$bw.Write([UInt16]0)        # Reserved
$bw.Write([UInt16]1)        # Type: Icon
$bw.Write([UInt16]1)        # Number of images
# Image entry
$bw.Write([byte]0)          # Width (0 = 256)
$bw.Write([byte]0)          # Height (0 = 256)
$bw.Write([UInt16]0)        # Color palette
$bw.Write([UInt16]0)        # Reserved
$bw.Write([UInt16]32)       # Bits per pixel
$bw.Write([UInt32]$iconData.Length)  # Size of image data
$bw.Write([UInt32]22)       # Offset to image data
$bw.Write($iconData)
$bw.Close()
$fs.Close()
$ms.Close()
$resized.Dispose()
$png.Dispose()

Write-Host "ICO created at $icoPath"

# === Step 2: Create Desktop Shortcut ===
$desktopPath = [System.Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktopPath "JARVIS.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "C:\Users\ibrah\Documents\GitHub\Jarvis\start_jarvis.bat"
$Shortcut.WorkingDirectory = "C:\Users\ibrah\Documents\GitHub\Jarvis"
$Shortcut.IconLocation = $icoPath
$Shortcut.Description = "Launch JARVIS AI Desktop Assistant"
$Shortcut.Save()

Write-Host "Shortcut created at $shortcutPath"

# Set "Run as Administrator" flag (byte 0x15, bit 0x20)
$bytes = [System.IO.File]::ReadAllBytes($shortcutPath)
$bytes[0x15] = $bytes[0x15] -bor 0x20
[System.IO.File]::WriteAllBytes($shortcutPath, $bytes)

Write-Host "Run as Administrator flag set."

# === Step 3: Copy to Startup ===
$startupFolder = "C:\Users\ibrah\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
$batSource = "C:\Users\ibrah\Documents\GitHub\Jarvis\start_jarvis.bat"
Copy-Item -Path $batSource -Destination $startupFolder -Force

Write-Host "Copied start_jarvis.bat to Startup folder: $startupFolder"
Write-Host ""
Write-Host "=== Setup Complete ==="
Write-Host "1. start_jarvis.bat created in project root"
Write-Host "2. JARVIS shortcut created on Desktop (Run as Admin)"
Write-Host "3. start_jarvis.bat added to Windows Startup"
