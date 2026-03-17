# Docker Desktop 重新安装脚本
# 此脚本将清理旧安装并重新安装Docker Desktop

Write-Host "开始重新安装Docker Desktop..."

# 下载Docker Desktop安装程序
$downloadUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$installerPath = "$env:USERPROFILE\Downloads\DockerDesktopInstaller.exe"

Write-Host "正在下载Docker Desktop安装程序..."

# 下载安装程序
try {
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $installerPath)
    Write-Host "下载完成！"
} catch {
    Write-Host "下载失败，请手动从官网下载: https://www.docker.com/products/docker-desktop"
    exit 1
}

# 检查文件是否存在
if (Test-Path $installerPath) {
    Write-Host "安装文件已准备就绪，正在运行安装程序..."
    
    # 运行安装程序（带参数）
    Start-Process -FilePath $installerPath -ArgumentList "install" -Wait
    
    Write-Host "安装完成！"
    
    # 检查安装是否成功
    if (Test-Path "C:\Program Files\Docker\Docker") {
        Write-Host "Docker Desktop安装目录存在"
        
        # 添加Docker到PATH环境变量
        $dockerPath = "C:\Program Files\Docker\Docker\resources\bin"
        $env:PATH += ";$dockerPath"
        
        # 验证Docker命令
        Write-Host "正在验证Docker命令..."
        try {
            docker --version
            Write-Host "Docker命令已可用！"
        } catch {
            Write-Host "Docker命令尚未可用，请重启计算机后再试。"
        }
    } else {
        Write-Host "安装可能未完成，请检查安装过程。"
    }
} else {
    Write-Host "安装文件未找到，安装失败。"
}