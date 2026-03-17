# Docker Desktop 安装脚本
# 此脚本将清理残留文件并重新安装Docker Desktop

Write-Host "开始安装Docker Desktop..."

# 清理残留文件
Write-Host "清理残留文件..."
if (Test-Path "C:\Program Files\Docker") {
    Remove-Item -Path "C:\Program Files\Docker" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "已清理Docker目录"
}

# 创建下载目录
$downloadDir = "$env:USERPROFILE\Downloads"
if (!(Test-Path $downloadDir)) {
    New-Item -Path $downloadDir -ItemType Directory -Force
}

# 下载Docker Desktop安装程序
$installerPath = "$downloadDir\DockerDesktopInstaller.exe"
$downloadUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

Write-Host "正在下载Docker Desktop安装程序..."
Write-Host "下载地址: $downloadUrl"
Write-Host "保存路径: $installerPath"

# 使用Invoke-WebRequest下载
try {
    Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -ErrorAction Stop
    Write-Host "下载完成！"
} catch {
    Write-Host "下载失败，错误信息: $_"
    Write-Host "请手动从官网下载: https://www.docker.com/products/docker-desktop"
    exit 1
}

# 检查文件是否下载成功
if (Test-Path $installerPath) {
    Write-Host "安装文件已准备就绪，大小: $(Get-Item $installerPath).Length 字节"
    
    # 以管理员身份运行安装程序
    Write-Host "正在运行安装程序..."
    Write-Host "请在弹出的安装向导中勾选 'Use WSL 2 instead of Hyper-V'"
    
    # 运行安装程序
    Start-Process -FilePath $installerPath -Wait
    
    Write-Host "安装程序已完成！"
    
    # 检查安装是否成功
    if (Test-Path "C:\Program Files\Docker\Docker") {
        Write-Host "✅ Docker Desktop安装成功！"
        
        # 添加Docker到PATH环境变量
        $dockerPath = "C:\Program Files\Docker\Docker\resources\bin"
        if (!(Test-Path "$dockerPath\docker.exe")) {
            Write-Host "❌ 未找到docker.exe文件"
        } else {
            Write-Host "✅ 找到docker.exe文件"
            
            # 检查环境变量
            $pathEnv = [Environment]::GetEnvironmentVariable("PATH", "Machine")
            if ($pathEnv -notcontains $dockerPath) {
                Write-Host "正在添加Docker到环境变量..."
                [Environment]::SetEnvironmentVariable("PATH", "$pathEnv;$dockerPath", "Machine")
                Write-Host "✅ 环境变量已更新"
            } else {
                Write-Host "✅ Docker已经在环境变量中"
            }
            
            # 验证Docker命令
            Write-Host "正在验证Docker命令..."
            $env:PATH += ";$dockerPath"
            try {
                docker --version
                Write-Host "✅ Docker命令已可用！"
                
                # 运行测试容器
                Write-Host "正在运行测试容器..."
                docker run hello-world
                Write-Host "✅ Docker容器运行成功！"
            } catch {
                Write-Host "⚠️ Docker命令尚未可用，请重启计算机后再试。"
            }
        }
    } else {
        Write-Host "❌ 安装失败，Docker目录不存在"
    }
} else {
    Write-Host "❌ 安装文件未找到"
}

Write-Host "安装过程完成！"
Write-Host "请按照以下步骤验证安装："
Write-Host "1. 重启计算机"
Write-Host "2. 启动Docker Desktop"
Write-Host "3. 运行: docker --version"
Write-Host "4. 运行: docker run hello-world"