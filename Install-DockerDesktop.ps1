# Docker Desktop 安装脚本
# 此脚本将下载并安装Docker Desktop for Windows

Write-Host "正在下载Docker Desktop安装程序..."

# 下载Docker Desktop安装程序
$downloadUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$installerPath = "$env:USERPROFILE\Downloads\DockerDesktopInstaller.exe"

# 使用更可靠的下载方法
try {
    Write-Host "正在从 $downloadUrl 下载..."
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $installerPath)
    Write-Host "下载完成！"
} catch {
    Write-Host "下载失败，请手动从官网下载: https://www.docker.com/products/docker-desktop"
    Write-Host "错误信息: $_"
    exit 1
}

# 检查文件是否下载成功
if (Test-Path $installerPath) {
    Write-Host "安装文件已保存到: $installerPath"
    Write-Host "正在运行安装程序..."
    
    # 运行安装程序
    Start-Process -FilePath $installerPath -Wait
    
    Write-Host "Docker Desktop安装完成！"
    Write-Host "请重启计算机以完成安装。"
} else {
    Write-Host "安装文件未找到，请手动下载并安装。"
}