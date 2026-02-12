import os
import requests
import tempfile
import shutil
import zipfile
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QMessageBox

class UpdateManager:
    def __init__(self, current_version, update_source="github", repo_owner="yourusername", repo_name="yourrepository"):
        self.current_version = current_version
        self.update_source = update_source
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        
        if update_source == "github":
            self.update_server_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        else:
            self.update_server_url = "https://your-update-server.com/api"
        
    def check_for_updates(self):
        """检查是否有可用更新"""
        try:
            if self.update_source == "github":
                # 使用 GitHub Releases API
                response = requests.get(self.update_server_url, timeout=10)
                if response.status_code == 200:
                    release_info = response.json()
                    latest_version = release_info.get("tag_name", "").lstrip("v")
                    release_notes = release_info.get("body", "")
                    
                    # 找到 Windows 可执行文件的下载链接
                    download_url = None
                    for asset in release_info.get("assets", []):
                        if asset.get("name").endswith(".exe") or asset.get("name").endswith(".zip"):
                            download_url = asset.get("browser_download_url")
                            break
                    
                    # 使用 version.py 中的 compare_versions 函数
                    from utils.version import compare_versions
                    if compare_versions(self.current_version, latest_version) < 0 and download_url:
                        return {
                            "available": True,
                            "version": latest_version,
                            "release_notes": release_notes,
                            "download_url": download_url
                        }
            else:
                # 从自定义服务器获取最新版本信息
                response = requests.get(f"{self.update_server_url}/version", timeout=10)
                if response.status_code == 200:
                    latest_version_info = response.json()
                    latest_version = latest_version_info.get("version")
                    
                    # 使用 version.py 中的 compare_versions 函数
                    from utils.version import compare_versions
                    if compare_versions(self.current_version, latest_version) < 0:
                        return {
                            "available": True,
                            "version": latest_version,
                            "release_notes": latest_version_info.get("release_notes", ""),
                            "download_url": latest_version_info.get("download_url")
                        }
            return {"available": False}
        except Exception as e:
            print(f"检查更新失败: {e}")
            return {"available": False, "error": str(e)}

class UpdateDownloader(QThread):
    """更新下载线程"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, download_url, target_path):
        super().__init__()
        self.download_url = download_url
        self.target_path = target_path
    
    def run(self):
        try:
            # 下载更新文件
            response = requests.get(self.download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress)
            
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

def install_update(update_file, current_exe_path):
    """安装更新"""
    try:
        # 解压更新文件
        temp_dir = tempfile.mkdtemp()
        
        with zipfile.ZipFile(update_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # 找到新的可执行文件
        new_exe = None
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file.endswith('.exe'):
                    new_exe = os.path.join(root, file)
                    break
            if new_exe:
                break
        
        if not new_exe:
            raise Exception("未找到新的可执行文件")
        
        # 备份当前可执行文件
        backup_exe = current_exe_path + ".bak"
        shutil.copy2(current_exe_path, backup_exe)
        
        # 替换可执行文件
        shutil.copy2(new_exe, current_exe_path)
        
        # 清理临时文件
        shutil.rmtree(temp_dir)
        os.remove(update_file)
        
        return True
    except Exception as e:
        print(f"安装更新失败: {e}")
        return False

def check_updates_on_start(app):
    """启动时检查更新"""
    # 使用 version.py 中的版本号
    from utils.version import __version__
    current_version = __version__
    
    # 检查更新
    # 这里使用 GitHub 作为更新源，需要替换为实际的用户名和仓库名
    update_manager = UpdateManager(
        current_version,
        update_source="github",
        repo_owner="yourusername",  # 替换为实际的 GitHub 用户名
        repo_name="SimofAtmScatt"  # 替换为实际的 GitHub 仓库名
    )
    update_info = update_manager.check_for_updates()
    
    if update_info.get("available"):
        reply = QMessageBox.question(
            None,
            "发现新版本",
            f"发现新版本 {update_info['version']}\n\n更新内容:\n{update_info['release_notes']}\n\n是否下载并安装更新？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # 下载并安装更新
            temp_update_file = os.path.join(tempfile.gettempdir(), "update.zip")
            downloader = UpdateDownloader(update_info["download_url"], temp_update_file)
            
            # 显示下载进度对话框
            from PyQt5.QtWidgets import QProgressDialog
            progress_dialog = QProgressDialog("正在下载更新...", "取消", 0, 100)
            progress_dialog.setWindowTitle("下载更新")
            progress_dialog.setModal(True)
            
            def update_progress(value):
                progress_dialog.setValue(value)
            
            def on_download_finished(success, error):
                progress_dialog.close()
                if success:
                    # 安装更新
                    current_exe = os.path.abspath(sys.executable)
                    if install_update(temp_update_file, current_exe):
                        QMessageBox.information(
                            None,
                            "更新成功",
                            "更新已成功安装，请重启应用程序。",
                            QMessageBox.Ok
                        )
                        # 重启应用
                        os.execl(sys.executable, sys.executable, *sys.argv)
                    else:
                        QMessageBox.critical(
                            None,
                            "更新失败",
                            "安装更新时发生错误，请手动下载并安装更新。",
                            QMessageBox.Ok
                        )
                else:
                    QMessageBox.critical(
                        None,
                        "下载失败",
                        f"下载更新时发生错误: {error}",
                        QMessageBox.Ok
                    )
            
            downloader.progress.connect(update_progress)
            downloader.finished.connect(on_download_finished)
            downloader.start()
            progress_dialog.exec_()

def check_updates_manual(parent_widget):
    """手动检查更新（从菜单栏调用）"""
    from PyQt5.QtWidgets import QProgressDialog
    
    # 使用 version.py 中的版本号
    from utils.version import __version__
    current_version = __version__
    
    # 创建更新管理器
    update_manager = UpdateManager(
        current_version,
        update_source="github",
        repo_owner="yourusername",  # 替换为实际的 GitHub 用户名
        repo_name="SimofAtmScatt"  # 替换为实际的 GitHub 仓库名
    )
    
    # 显示检查进度对话框
    progress = QProgressDialog("正在检查更新...", "取消", 0, 0, parent_widget)
    progress.setWindowTitle("检查更新")
    progress.setWindowModality(Qt.WindowModal)
    progress.show()
    
    # 创建检查线程
    class UpdateCheckThread(QThread):
        finished = pyqtSignal(dict)
        
        def __init__(self, update_manager):
            super().__init__()
            self.update_manager = update_manager
        
        def run(self):
            result = self.update_manager.check_for_updates()
            self.finished.emit(result)
    
    check_thread = UpdateCheckThread(update_manager)
    
    def handle_check_result(result):
        progress.close()
        
        if result.get("available"):
            reply = QMessageBox.question(
                parent_widget,
                "发现新版本",
                f"发现新版本可用！\n\n"
                f"当前版本: {current_version}\n"
                f"最新版本: {result['version']}\n\n"
                f"更新说明:\n{result['release_notes']}\n\n"
                f"是否下载并安装更新？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                download_and_install_update(parent_widget, result["download_url"])
        elif result.get("error"):
            QMessageBox.warning(
                parent_widget,
                "检查更新失败",
                f"检查更新时发生错误:\n\n{result['error']}\n\n"
                "请检查网络连接或稍后重试。"
            )
        else:
            QMessageBox.information(
                parent_widget,
                "检查更新",
                f"当前已是最新版本\n\n当前版本: {current_version}"
            )
    
    check_thread.finished.connect(handle_check_result)
    check_thread.start()
    progress.exec_()

def download_and_install_update(parent_widget, download_url):
    """下载并安装更新"""
    from PyQt5.QtWidgets import QProgressDialog
    
    temp_update_file = os.path.join(tempfile.gettempdir(), "update.zip")
    downloader = UpdateDownloader(download_url, temp_update_file)
    
    # 显示下载进度对话框
    progress_dialog = QProgressDialog("正在下载更新...", "取消", 0, 100, parent_widget)
    progress_dialog.setWindowTitle("下载更新")
    progress_dialog.setModal(True)
    
    def update_progress(value):
        progress_dialog.setValue(value)
    
    def on_download_finished(success, error):
        progress_dialog.close()
        if success:
            # 安装更新
            current_exe = os.path.abspath(sys.executable)
            if install_update(temp_update_file, current_exe):
                QMessageBox.information(
                    parent_widget,
                    "更新成功",
                    "更新已成功安装，请重启应用程序。",
                    QMessageBox.Ok
                )
                # 重启应用
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                QMessageBox.critical(
                    parent_widget,
                    "更新失败",
                    "安装更新时发生错误，请手动下载并安装更新。",
                    QMessageBox.Ok
                )
        else:
            QMessageBox.critical(
                parent_widget,
                "下载失败",
                f"下载更新时发生错误: {error}",
                QMessageBox.Ok
            )
    
    downloader.progress.connect(update_progress)
    downloader.finished.connect(on_download_finished)
    downloader.start()
    progress_dialog.exec_()

# 导入必要的模块
import sys
from PyQt5.QtCore import Qt