# Docker Desktop 完整安装指南

## 系统状态检查
✅ WSL2已正确安装和配置
✅ 网络连接正常
❌ Docker Desktop未正确安装

## 手动安装步骤

### 步骤 1: 下载Docker Desktop安装程序
1. **打开浏览器**，访问Docker官方网站：
   ```
   https://www.docker.com/products/docker-desktop
   ```

2. **点击下载按钮**：
   - 找到"Download for Windows"按钮
   - 选择适合Windows 11的64位版本
   - 下载文件保存到Downloads文件夹

3. **验证下载**：
   - 确保文件名为 `Docker Desktop Installer.exe`
   - 文件大小约为 400-500MB

### 步骤 2: 准备系统环境
1. **确保WSL2已启用**：
   ```powershell
   # 以管理员身份运行PowerShell
   wsl --status
   ```

2. **更新WSL2**：
   ```powershell
   wsl --update
   ```

3. **设置WSL2为默认版本**：
   ```powershell
   wsl --set-default-version 2
   ```

### 步骤 3: 安装Docker Desktop
1. **以管理员身份运行安装程序**：
   - 找到下载的 `Docker Desktop Installer.exe`
   - 右键点击 → "以管理员身份运行"
   - 在UAC对话框中点击"是"

2. **安装配置**：
   - 在安装向导中，**必须勾选**：
     ✅ "Use WSL 2 instead of Hyper-V"
     ✅ "Add shortcut to desktop"
   - 点击"OK"开始安装

3. **完成安装**：
   - 等待安装过程完成（约5-10分钟）
   - 安装完成后，点击"Close and restart"
   - 重启计算机

### 步骤 4: 验证安装
1. **启动Docker Desktop**：
   - 从开始菜单或桌面快捷方式启动
   - 等待Docker Desktop初始化（约2-3分钟）

2. **验证Docker命令**：
   ```powershell
   # 检查Docker版本
   docker --version
   
   # 检查Docker Compose版本
   docker-compose --version
   
   # 运行测试容器
   docker run hello-world
   ```

3. **验证WSL集成**：
   ```powershell
   wsl -l -v
   ```

### 步骤 5: 环境变量配置（如果需要）
如果Docker命令无法识别：
1. **打开环境变量设置**：
   - 右键点击"此电脑" → "属性" → "高级系统设置" → "环境变量"

2. **编辑系统PATH变量**：
   - 在"系统变量"中找到"Path" → 点击"编辑"
   - 点击"新建" → 添加以下路径：
     ```
     C:\Program Files\Docker\Docker\resources\bin
     ```
   - 点击"确定"保存

3. **重启终端**：
   - 关闭所有终端窗口
   - 重新打开PowerShell

## 故障排除

### 常见问题及解决方案

1. **Docker命令未找到**
   - 检查环境变量是否正确配置
   - 确保Docker Desktop正在运行
   - 重启计算机后重试

2. **WSL2错误**
   - 运行：`wsl --update`
   - 运行：`wsl --shutdown` 然后重新启动
   - 检查WSL版本：`wsl --version`

3. **虚拟化问题**
   - 重启计算机进入BIOS
   - 确保CPU虚拟化已启用（Intel VT-x/AMD-V）
   - 保存BIOS设置并重启

4. **安装失败**
   - 清理残留文件：删除 `C:\Program Files\Docker` 目录
   - 清理注册表：删除 `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Docker Desktop`
   - 重新下载安装程序

5. **网络问题**
   - 检查网络连接
   - 尝试使用不同的网络
   - 暂时禁用防火墙或 antivirus

## 验证检查清单

### 安装前
- [ ] WSL2已安装
- [ ] WSL2设置为默认版本
- [ ] 网络连接正常
- [ ] 系统权限足够

### 安装后
- [ ] Docker Desktop启动成功
- [ ] `docker --version` 正常显示
- [ ] `docker run hello-world` 运行成功
- [ ] WSL集成正常

## 后续步骤

安装成功后，你可以：
1. 查看项目中的 `Dockerfile.model` 文件
2. 开始构建和运行你的Docker容器
3. 配置Docker Desktop设置（如资源分配）

## 联系方式

如果在安装过程中遇到任何问题，请参考：
- Docker官方文档：https://docs.docker.com/desktop/install/windows-install/
- WSL官方文档：https://docs.microsoft.com/en-us/windows/wsl/

祝你安装成功！