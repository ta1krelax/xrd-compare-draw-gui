from dataclasses import dataclass
import numpy as np


@dataclass
class Dataset:
    """一套已导入的 XRD 数据（2theta / 强度）及其显示样式。"""

    name: str
    two_theta: np.ndarray
    intensity: np.ndarray
    path: str = ""
    visible: bool = True
    color: str = "#1f77b4"
    linewidth: float = 1.4
    offset: float = 0.0
    scale: float = 1.0

    # 堆叠图里该数据名称标注的位置（ax.transAxes 分数坐标，0-1），
    # 默认贴在每个子图的右上角，可以用鼠标拖动调整。
    label_x: float = 0.98
    label_y: float = 0.92
