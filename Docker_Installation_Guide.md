# Docker Desktop 安装指南

## 系统要求
- Windows 11 64位（家庭版或专业版）
- WSL2 已启用（已完成）
- CPU 支持虚拟化（大多数现代CPU都支持）

## 安装步骤

### 1. 手动下载Docker Desktop
1. 打开浏览器，访问Docker官网：https://www.docker.com/products/docker-desktop
2. 点击"Download for Windows"按钮
3. 选择适合你系统的版本（Windows 11 64位）
4. 下载完成后，找到下载的安装文件（通常在Downloads文件夹中）

### 2. 运行安装程序
1. 双击Docker Desktop安装文件（Docker Desktop Installer.exe）
2. 在安装向导中，确保勾选以下选项：
   - ✅ "Use WSL 2 instead of Hyper-V"
   - ✅ "Add shortcut to desktop"
3. 点击"OK"开始安装
4. 安装过程中可能会提示需要管理员权限，点击"是"允许
5. 安装完成后，点击"Close and restart"重启计算机

### 3. 验证安装
重启后：
1. 启动Docker Desktop（从开始菜单或桌面快捷方式）
2. 等待Docker Desktop初始化完成（可能需要几分钟）
3. 打开PowerShell或命令提示符，运行以下命令验证安装：
   ```
   docker --version
   docker-compose --version
   docker run hello-world
   ```

### 4. 配置Docker Desktop（可选）
- 右键点击系统托盘中的Docker图标，选择"Settings"
- 在"Resources" > "WSL Integration"中，确保启用了Ubuntu分发
- 可以根据需要调整内存和CPU分配

## 故障排除
- 如果遇到WSL相关错误，运行：`wsl --update`
- 如果Docker Desktop无法启动，检查是否启用了虚拟化（在BIOS中）
- 确保Windows更新到最新版本

## 后续步骤
安装完成后，你可以开始使用Docker构建和运行容器。查看项目中的Dockerfile.model文件了解如何构建你的模型容器。