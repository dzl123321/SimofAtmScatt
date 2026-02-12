# 大气散射特性建模仿真系统 - 部署与更新方案

## 1. 打包为可执行文件

### 1.1 打包工具选择

本项目使用 **PyInstaller** 作为打包工具，它具有以下优势：
- 支持 Windows 平台的 .exe 文件创建
- 能够自动处理大多数依赖项
- 配置简单，易于使用
- 支持单文件和目录两种打包模式

### 1.2 打包步骤

1. **安装依赖**：
   ```bash
   pip install -r requirement.txt
   pip install pyinstaller
   ```

2. **生成打包配置文件**：
   ```bash
   pyi-makespec --onefile --windowed --name "AtmScattSim" --icon=resources/icons/rain_cloud.png main.py
   ```

3. **修改配置文件**：
   编辑生成的 `AtmScattSim.spec` 文件，添加必要的依赖项和资源文件路径：
   ```python
   a = Analysis(
       ['main.py'],
       pathex=['.'],
       binaries=[],
       datas=[
           ('VERSION', '.'),
           ('data', 'data'),
           ('resources', 'resources')
       ],
       hiddenimports=[
           'numpy',
           'scipy',
           'matplotlib',
           'PyMieScatt',
           'PyQt5.QtWidgets',
           'PyQt5.QtCore',
           'PyQt5.QtGui'
       ],
       # 其他配置保持不变
   )
   ```

4. **执行打包**：
   ```bash
   pyinstaller AtmScattSim.spec
   ```

5. **获取可执行文件**：
   打包完成后，可执行文件将位于 `dist` 目录中：
   - `dist/AtmScattSim.exe` - 主可执行文件

### 1.3 打包选项说明

- `--onefile`：生成单个可执行文件，所有依赖项都被打包到一个文件中
- `--windowed`：无控制台窗口模式，适合 GUI 应用
- `--name`：指定生成的可执行文件名称
- `--icon`：指定应用图标

## 2. 自动更新功能

### 2.1 实现原理

本项目实现了基于 **GitHub Releases** 的自动更新功能，主要组件包括：

1. **版本检查**：程序启动时检查 GitHub Releases 上的最新版本
2. **版本比较**：比较本地版本与远程版本
3. **更新提示**：如有新版本，弹出更新提示窗口
4. **更新下载**：用户确认后自动下载更新包
5. **更新安装**：下载完成后自动安装更新并重启应用

### 2.2 配置方法

1. **GitHub 仓库设置**：
   - 创建 GitHub 仓库（如 `SimofAtmScatt`）
   - 在仓库中创建 Releases，使用语义化版本号作为标签（如 `v2.0.1`）
   - 每次发布时上传打包好的可执行文件或压缩包

2. **更新管理器配置**：
   编辑 `utils/update_manager.py` 文件，修改以下参数：
   ```python
   update_manager = UpdateManager(
       current_version,
       update_source="github",
       repo_owner="yourusername",  # 替换为实际的 GitHub 用户名
       repo_name="SimofAtmScatt"  # 替换为实际的 GitHub 仓库名
   )
   ```

3. **版本文件管理**：
   确保 `VERSION` 文件包含正确的版本信息：
   ```json
   {
     "version": "2.0.0",
     "release_date": "2024-01-01",
     "release_notes": "初始发布版本",
     "download_url": "https://github.com/yourusername/SimofAtmScatt/releases/latest",
     "min_compatible_version": "2.0.0"
   }
   ```

### 2.3 更新流程

1. **用户启动应用**：
   - 程序自动检查 GitHub Releases 上的最新版本
   - 比较版本号，判断是否需要更新

2. **发现更新**：
   - 弹出更新提示窗口，显示新版本信息和更新内容
   - 用户可以选择立即更新或稍后提醒

3. **下载更新**：
   - 用户确认后，程序开始下载更新包
   - 显示下载进度条

4. **安装更新**：
   - 下载完成后自动解压并安装更新
   - 备份当前版本（以防更新失败）
   - 替换可执行文件

5. **重启应用**：
   - 更新完成后自动重启应用
   - 用户可以看到新版本的功能

## 3. 部署与分发

### 3.1 分发方式

1. **直接分发**：
   - 将 `dist/AtmScattSim.exe` 文件直接发送给用户
   - 用户可以将文件放在任意位置运行

2. **安装包分发**：
   - 使用 Inno Setup 或 NSIS 等工具创建安装包
   - 安装包可以添加快捷方式、注册表项等

3. **网络分发**：
   - 将可执行文件上传到 GitHub Releases
   - 用户可以从 GitHub 下载最新版本
   - 已安装的用户可以通过自动更新功能获取新版本

### 3.2 系统要求

- **操作系统**：Windows 7/8/10/11
- **处理器**：Intel Core i3 或同等性能
- **内存**：4GB 或更多
- **磁盘空间**：200MB 或更多
- **Python**：无需安装（已打包到可执行文件中）

## 4. 常见问题与解决方案

### 4.1 打包问题

1. **依赖项缺失**：
   - **症状**：运行时提示 "ModuleNotFoundError"
   - **解决方案**：在 `spec` 文件的 `hiddenimports` 中添加缺失的模块

2. **资源文件找不到**：
   - **症状**：运行时提示 "FileNotFoundError"
   - **解决方案**：在 `spec` 文件的 `datas` 中添加资源文件路径

3. **打包后文件过大**：
   - **症状**：生成的 .exe 文件超过 100MB
   - **解决方案**：使用 `--exclude` 选项排除不需要的模块，或使用 UPX 压缩

### 4.2 更新问题

1. **更新检查失败**：
   - **症状**：程序启动时提示 "检查更新失败"
   - **解决方案**：检查网络连接，确保 GitHub 访问正常

2. **更新下载失败**：
   - **症状**：下载更新时提示 "下载失败"
   - **解决方案**：检查网络连接，确保 GitHub Releases 中的文件存在

3. **更新安装失败**：
   - **症状**：安装更新时提示 "安装失败"
   - **解决方案**：手动下载最新版本并替换当前可执行文件

## 5. 最佳实践

### 5.1 版本管理

- 使用 **语义化版本号**（如 `MAJOR.MINOR.PATCH`）
- 每次发布时更新 `VERSION` 文件
- 在 GitHub Releases 中使用相同的版本号作为标签

### 5.2 发布策略

- **补丁版本**：修复 bug，不添加新功能
- **次版本**：添加新功能，保持向后兼容
- **主版本**：重大变更，可能不兼容旧版本

### 5.3 测试流程

1. **本地测试**：在开发环境中测试打包后的可执行文件
2. **发布测试**：在 GitHub 上创建预发布版本进行测试
3. **正式发布**：测试通过后创建正式发布版本

### 5.4 安全措施

- 定期更新依赖项，修复安全漏洞
- 使用 HTTPS 进行更新检查和下载
- 验证更新包的完整性

## 6. 总结

本部署与更新方案通过以下步骤实现了用户友好的软件分发：

1. 使用 **PyInstaller** 打包为单文件可执行文件
2. 实现基于 **GitHub Releases** 的自动更新功能
3. 提供多种分发方式，适应不同场景
4. 建立完善的版本管理和发布流程

通过这套方案，用户可以：
- 直接运行 .exe 文件，无需安装 Python 和依赖项
- 收到自动更新提示，一键更新到最新版本
- 查看详细的更新内容和版本信息

这样既提高了用户体验，又保证了软件的及时更新和维护。