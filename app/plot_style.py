from dataclasses import dataclass

# Origin 风格默认配色循环，新导入的数据依次分配颜色
TAB10_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]

FONT_CHOICES = [
    "Arial", "Times New Roman", "Calibri", "DejaVu Sans",
    "Microsoft YaHei", "SimHei", "SimSun",
]


CM_PER_INCH = 2.54


@dataclass
class PlotStyle:
    mode: str = "waterfall"  # "waterfall" 或 "stack"

    fig_width_cm: float = 20.0
    fig_height_cm: float = 15.0
    dpi: int = 100

    @property
    def fig_width_in(self):
        return self.fig_width_cm / CM_PER_INCH

    @property
    def fig_height_in(self):
        return self.fig_height_cm / CM_PER_INCH

    font_family: str = "Arial"
    font_size: int = 11

    x_title: str = "2 Theta (degree)"
    y_title: str = "Intensity"

    normalize: bool = True
    offset_step: float = 1.2
    stack_spacing: float = 0.05

    show_grid: bool = False
    show_legend: bool = True

    # X 轴子刻度阶数：0 = 不画；1 = 每个主刻度间隔中点画一道（长度减半，无数字）；
    # 2 = 在此基础上再对半分一次（更短一截）；以此类推。
    x_submark_order: int = 0
