__version__ = "2.0.2"
__app_name__ = "大气散射特性建模仿真系统"
__author__ = "西安电子科技大学"
__copyright__ = "Copyright © 2024 西安电子科技大学"
__release_date__ = "2026-02-13"
__description__ = "降雨环境下激光散射特性仿真、激光雷达系统性能分析、多维度结果可视化和数据导出报告生成"


def get_version_info():
    """获取版本信息字典"""
    return {
        "version": __version__,
        "app_name": __app_name__,
        "author": __author__,
        "copyright": __copyright__,
        "release_date": __release_date__,
        "description": __description__
    }


def compare_versions(current, remote):
    """
    比较两个版本号
    
    Args:
        current: 当前版本号 (如 "2.0.0")
        remote: 远程版本号 (如 "2.1.0")
    
    Returns:
        -1: 当前版本较旧
        0: 版本相同
        1: 当前版本较新
    """
    current_parts = [int(x) for x in current.split('.')]
    remote_parts = [int(x) for x in remote.split('.')]
    
    for i in range(max(len(current_parts), len(remote_parts))):
        current_val = current_parts[i] if i < len(current_parts) else 0
        remote_val = remote_parts[i] if i < len(remote_parts) else 0
        
        if current_val < remote_val:
            return -1
        elif current_val > remote_val:
            return 1
    
    return 0
