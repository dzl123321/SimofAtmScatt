# utils/style_utils.py
import matplotlib
import matplotlib.pyplot as plt


def setup_chinese_font():
    """设置中文字体支持"""
    chinese_fonts = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong', 'STSong', 'Arial']

    # 设置Matplotlib字体
    matplotlib.rcParams['font.sans-serif'] = chinese_fonts
    matplotlib.rcParams['axes.unicode_minus'] = False

    # 设置默认字体
    plt.rcParams.update({
        'font.sans-serif': chinese_fonts,
        'axes.unicode_minus': False
    })
