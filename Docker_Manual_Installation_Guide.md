# Docker Desktop 手动安装指南

## 问题分析
从之前的尝试中，我们发现：
- WSL2已经正确安装和配置
- 系统尝试安装Docker Desktop但可能遇到了网络或权限问题
- Docker命令尚未在系统中可用

## 手动安装步骤

### 步骤 1: 手动下载Docker Desktop
1. 打开浏览器，访问官方Docker下载页面：
   https://www.docker.com/products/docker-desktop

2. 点击"Download for Windows"按钮
3. 选择适合Windows 11的版本（64位）
4. 下载完成后，找到下载的安装文件（通常在Downloads文件夹中）

### 步骤 2: 以管理员身份运行安装程序
1. 找到下载的Docker Desktop Installer.exe文件
2. 右键点击该文件，选择"以管理员身份运行"
3. 在用户账户控制(UAC)对话框中点击"是"

### 步骤 3: 安装配置
1. 在安装向导中，确保勾选以下选项：
   - ✅ "Use WSL 2 instead of Hyper-V"
   - ✅ "Add shortcut to desktop"
2. 点击"OK"开始安装
3. 等待安装完成（可能需要几分钟）
4. 安装完成后，点击"Close and restart"重启计算机

### 步骤 4: 验证安装
重启后：
1. 启动Docker Desktop（从开始菜单或桌面快捷方式）
2. 等待Docker Desktop初始化完成（可能需要几分钟）
3. 打开PowerShell或命令提示符，运行以下命令验证安装：
   ```powershell
   # 检查Docker版本
   docker --version
   
   # 检查Docker Compose版本
   docker-compose --version
   
   # 运行测试容器
   docker run hello-world
   ```

### 步骤 5: 环境变量配置（如果需要）
如果Docker命令仍然无法识别：
1. 右键点击"此电脑" → "属性" → "高级系统设置" → "环境变量"
2. 在"系统变量"中找到"Path"变量，点击"编辑"
3. 点击"新建"，添加以下路径：
   ```
   C:\Program Files\Docker\Docker\resources\bin
   ```
4. 点击"确定"保存更改
5. 重新打开终端，再次尝试Docker命令

## 故障排除

### 常见问题及解决方案：

1. **Docker命令未找到**
   - 检查环境变量是否正确配置
   - 确保Docker Desktop正在运行
   - 重启计算机后重试

2. **WSL2相关错误**
   - 运行：`wsl --update`
   - 运行：`wsl --status` 检查状态
   - 确保WSL2设置为默认版本：`wsl --set-default-version 2`

3. **虚拟化问题**
   - 重启计算机进入BIOS，确保CPU虚拟化已启用
   - 常见BIOS设置：Intel VT-x或AMD-V

4. **权限问题**
   - 确保以管理员身份运行安装程序
   - 检查用户权限是否足够

5. **网络问题**
   - 确保网络连接正常
   - 尝试使用不同的网络环境

## 验证步骤
安装完成后，请运行以下命令验证：

```powershell
# 检查Docker版本
docker --version

# 检查Docker服务状态
docker info

# 运行测试容器
docker run hello-world

# 检查WSL状态
wsl --status
```

## 后续步骤
安装成功后，你可以开始使用Docker构建和运行项目中的容器。查看项目中的`Dockerfile.model`文件了解如何构建你的模型容器。

如果在安装过程中遇到任何问题，请随时参考此指南或寻求进一步帮助。