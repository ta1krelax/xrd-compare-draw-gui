"""无界面（offscreen）端到端自测：导入样例数据、切换两种作图模式、确认不报错。"""
import glob
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtWidgets import QApplication  # noqa: E402

from app.data_io import load_xrd_txt  # noqa: E402
from app.main_window import MainWindow  # noqa: E402
from app.models import Dataset  # noqa: E402
from app.plot_style import TAB10_COLORS  # noqa: E402

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()

    paths = sorted(glob.glob(os.path.join(SAMPLE_DIR, "*.txt")))
    assert paths, "没有样例数据，先运行 scripts/make_sample_data.py"

    for i, p in enumerate(paths):
        x, y = load_xrd_txt(p)
        name = os.path.splitext(os.path.basename(p))[0]
        ds = Dataset(name=name, two_theta=x, intensity=y, path=p, color=TAB10_COLORS[i % len(TAB10_COLORS)])
        win.dataset_panel.datasets.append(ds)
    win.dataset_panel._rebuild_list()
    win.refresh_plot()
    assert len(win.fig.axes) >= 1, "waterfall 模式下应至少有一个坐标轴"
    print(f"[ok] waterfall 模式渲染成功，共 {len(paths)} 套数据，axes={len(win.fig.axes)}")

    win.style_panel.style.mode = "stack"
    win.style_panel._load_from_style()
    win.refresh_plot()
    assert len(win.fig.axes) == len(paths), "stack 模式下坐标轴数量应等于可见数据条数"
    print(f"[ok] stack 模式渲染成功，axes={len(win.fig.axes)}")

    # 测试删除、隐藏、重排序、编辑属性等操作不会崩溃
    win.dataset_panel.datasets[0].visible = False
    win.refresh_plot()
    assert len(win.fig.axes) == len(paths) - 1
    print("[ok] 隐藏某套数据后 stack 面板数正确减少")

    win.dataset_panel._move(1)
    win.refresh_plot()
    print("[ok] 上下移动排序不报错")

    win.dataset_panel.datasets[0].offset = 5.0
    win.dataset_panel.datasets[0].scale = 2.0
    win.refresh_plot()
    print("[ok] 编辑 offset/scale 不报错")

    # 测试导出 PNG / TIFF / SVG（透明背景）不报错
    export_dir = os.path.join(os.path.dirname(__file__), "..", "_smoke_export")
    os.makedirs(export_dir, exist_ok=True)
    for ext in ("png", "tiff", "svg"):
        out_path = os.path.join(export_dir, f"test_export.{ext}")
        win.fig.savefig(out_path, dpi=win.style_panel.style.dpi, transparent=True)
        assert os.path.exists(out_path), f"{ext} 导出文件未生成"
    print("[ok] PNG/TIFF/SVG 透明背景导出成功")

    print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    main()
