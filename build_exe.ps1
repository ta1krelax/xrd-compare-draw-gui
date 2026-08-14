# 重新打包成独立 Windows exe。
# 用法：右键 -> "使用 PowerShell 运行"，或在终端里：
#   .\build_exe.ps1

Set-Location $PSScriptRoot

py -m pip show pyinstaller *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "正在安装 PyInstaller..."
    py -m pip install pyinstaller
}

py -m PyInstaller --noconfirm --onefile --windowed --name XRD_Compare_GUI main.py

Write-Host ""
Write-Host "完成。exe 位于 dist\XRD_Compare_GUI.exe"
