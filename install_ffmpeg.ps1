# Script to download and install FFmpeg for Windows
$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Installing FFmpeg for Stream-Plus" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Create tools directory if it doesn't exist
$toolsDir = "C:\Users\josea\Desktop\Stream-plus\tools"
if (-not (Test-Path $toolsDir)) {
    Write-Host "Creating tools directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $toolsDir | Out-Null
}

# FFmpeg download URL (essentials build from GitHub)
$ffmpegUrl = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
$zipPath = "$toolsDir\ffmpeg.zip"
$extractPath = "$toolsDir\ffmpeg"

Write-Host "Downloading FFmpeg..." -ForegroundColor Yellow
Write-Host "URL: $ffmpegUrl" -ForegroundColor Gray

try {
    # Download FFmpeg
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "Download completed!" -ForegroundColor Green
    
    # Extract the zip
    Write-Host "Extracting FFmpeg..." -ForegroundColor Yellow
    if (Test-Path $extractPath) {
        Remove-Item -Path $extractPath -Recurse -Force
    }
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force
    
    # Find the bin folder (it's inside a versioned folder)
    $binFolder = Get-ChildItem -Path $extractPath -Filter "bin" -Recurse -Directory | Select-Object -First 1
    
    if ($binFolder) {
        $ffprobePath = Join-Path $binFolder.FullName "ffprobe.exe"
        $ffmpegPath = Join-Path $binFolder.FullName "ffmpeg.exe"
        
        if (Test-Path $ffprobePath) {
            Write-Host "FFmpeg installed successfully!" -ForegroundColor Green
            Write-Host "Location: $($binFolder.FullName)" -ForegroundColor Gray
            Write-Host ""
            
            # Test ffprobe
            Write-Host "Testing ffprobe..." -ForegroundColor Yellow
            & $ffprobePath -version | Select-Object -First 1
            Write-Host ""
            
            Write-Host "================================" -ForegroundColor Cyan
            Write-Host "Installation Complete!" -ForegroundColor Green
            Write-Host "================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "FFprobe path: $ffprobePath" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Note: This is a local installation in the tools folder." -ForegroundColor Gray
            Write-Host "The test script will be updated to use this path." -ForegroundColor Gray
            
            # Save the path to a file for easy reference
            $ffprobePath | Out-File -FilePath "$toolsDir\ffprobe_path.txt" -Encoding UTF8
            
        } else {
            Write-Host "Error: ffprobe.exe not found after extraction" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Error: bin folder not found in extracted files" -ForegroundColor Red
        exit 1
    }
    
    # Clean up zip file
    Remove-Item -Path $zipPath -Force
    Write-Host "Cleanup completed" -ForegroundColor Gray
    
} catch {
    Write-Host "Error during installation: $_" -ForegroundColor Red
    exit 1
}
