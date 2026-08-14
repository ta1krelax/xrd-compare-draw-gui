import os

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDockWidget, QFileDialog, QMainWindow, QMessageBox, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)

from .dataset_panel import DatasetPanel
from .dialogs import AxisTitleDialog, DatasetEditDialog
from .plot_canvas import render_plot
from .style_panel import StylePanel

EXPORT_FILTERS = "PNG 图片 (*.png);;TIFF 图片 (*.tiff *.tif);;SVG 矢量图 (*.svg)"
EXPORT_DEFAULT_EXT = {
    "PNG 图片 (*.png)": ".png",
    "TIFF 图片 (*.tiff *.tif)": ".tiff",
    "SVG 矢量图 (*.svg)": ".svg",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 窗口标题栏由操作系统而不是 Qt 样式表绘制，这里用英文以避免个别
        # 环境下标题栏的中文字体回退失败、显示成方块乱码。
        self.setWindowTitle("XRD Compare")
        self.resize(1500, 950)

        self.fig = Figure()
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.nav_toolbar = NavigationToolbar2QT(self.canvas, self)

        self.btn_export = QPushButton("导出图片…")
        self.btn_export.clicked.connect(self._export_image)
        self.nav_toolbar.addWidget(self.btn_export)

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setWidget(self.canvas)

        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.nav_toolbar)
        v.addWidget(scroll, 1)
        self.setCentralWidget(central)

        self.dataset_panel = DatasetPanel()
        self.style_panel = StylePanel()

        dock_data = QDockWidget("数据管理", self)
        dock_data.setObjectName("dock_data")
        dock_data.setWidget(self.dataset_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_data)

        dock_style = QDockWidget("绘图设置", self)
        dock_style.setObjectName("dock_style")
        dock_style.setWidget(self.style_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock_style)

        self.tabifyDockWidget(dock_data, dock_style)
        dock_data.raise_()

        panel_toolbar = self.addToolBar("面板")
        panel_toolbar.addAction(dock_data.toggleViewAction())
        panel_toolbar.addAction(dock_style.toggleViewAction())

        self.dataset_panel.dataChanged.connect(self.refresh_plot)
        self.style_panel.styleChanged.connect(self.refresh_plot)

        self._line_to_dataset = {}
        self._label_to_dataset = {}
        self._view_state = {}  # 记住每套数据（或瀑布图共用坐标框）当前的缩放/平移范围
        self._last_rendered_mode = None
        self._drag_label = None
        self._drag_dataset = None
        self._drag_ax = None

        self.canvas.mpl_connect("button_press_event", self._on_canvas_press)
        self.canvas.mpl_connect("motion_notify_event", self._on_canvas_motion)
        self.canvas.mpl_connect("button_release_event", self._on_canvas_release)

        self.refresh_plot()

    def refresh_plot(self):
        style = self.style_panel.style
        self._capture_view_state()

        w_in, h_in = style.fig_width_in, style.fig_height_in
        self.fig.set_dpi(style.dpi)
        self.fig.set_size_inches(w_in, h_in)
        self.canvas.setFixedSize(int(w_in * style.dpi), int(h_in * style.dpi))

        # 上面的 setFixedSize() 会同步触发 canvas 的 resizeEvent；matplotlib
        # 的 Qt 后端在那个 resizeEvent 里会用 devicePixelRatio() 重新算一遍
        # figure 的英寸尺寸——如果系统显示缩放不是 100%（125%/150%/200% 很
        # 常见），这个内部换算会把尺寸算错（通常翻倍），导致图幅跟我们上面
        # 设的不一致。这里再显式设一遍，用我们自己的值把算错的结果覆盖回去。
        self.fig.set_size_inches(w_in, h_in)

        result = render_plot(self.fig, self.dataset_panel.datasets, style) or {}
        self._line_to_dataset = result.get("lines", {})
        self._label_to_dataset = result.get("labels", {})

        self._restore_view_state()
        self._last_rendered_mode = style.mode
        self.canvas.draw_idle()

    # --------------------------------------------------- 缩放/平移状态保留
    def _capture_view_state(self):
        """在重新画图之前，把每套数据当前的 X/Y 轴显示范围记下来，这样改字号、
        调整顺序这类跟坐标轴范围无关的设置，就不会因为整张图重新生成而把用户
        手动缩放/平移过的视图弄丢、跳回自动缩放的默认范围。

        只有在"上一次渲染确实画出过数据"时才记录——如果上一次是"还没导入
        数据"的占位提示（此时坐标轴是 matplotlib 默认的 0-1 空坐标系，没有
        任何实际意义），就不能把这个 0-1 存下来，否则导入数据后会被这个空
        坐标系覆盖回去，导致新数据的坐标轴范围被强行锁定在 0-1，看起来就像
        "画不出来"。

        模式刚发生切换（堆叠图 <-> 瀑布图）时也跳过：这时旧的坐标轴布局跟
        新模式完全不是一回事（比如瀑布图切到堆叠图，fig.axes[0] 会变成
        某一个子图，而不是瀑布图那个共用坐标框），记下来也没有意义。
        """
        style = self.style_panel.style
        if style.mode != self._last_rendered_mode:
            return
        if style.mode == "stack":
            for line, ds in self._line_to_dataset.items():
                ax = line.axes
                self._view_state[id(ds)] = (ax.get_xlim(), ax.get_ylim())
        else:
            if self.fig.axes and self._line_to_dataset:
                ax = self.fig.axes[0]
                self._view_state["_shared"] = (ax.get_xlim(), ax.get_ylim())

    def _restore_view_state(self):
        style = self.style_panel.style
        if style.mode == "stack":
            for line, ds in self._line_to_dataset.items():
                saved = self._view_state.get(id(ds))
                if saved is not None:
                    ax = line.axes
                    ax.set_xlim(saved[0])
                    ax.set_ylim(saved[1])
        else:
            saved = self._view_state.get("_shared")
            if saved is not None and self.fig.axes:
                ax = self.fig.axes[0]
                ax.set_xlim(saved[0])
                ax.set_ylim(saved[1])

    # ------------------------------------------------------- 双击图上元素编辑
    def _on_canvas_press(self, event):
        if event.button != 1:
            return

        if event.dblclick:
            self._drag_label = None
            self._drag_dataset = None
            self._drag_ax = None
            self._handle_double_click(event)
            return

        # 单击命中某个数据名称标注 -> 开始拖动
        for label, ds in self._label_to_dataset.items():
            contains, _ = label.contains(event)
            if contains:
                self._drag_label = label
                self._drag_dataset = ds
                self._drag_ax = label.axes
                return

    def _on_canvas_motion(self, event):
        if self._drag_label is None or event.x is None or event.y is None:
            return
        inv = self._drag_ax.transAxes.inverted()
        x_frac, y_frac = inv.transform((event.x, event.y))
        self._drag_label.set_position((x_frac, y_frac))
        self.canvas.draw_idle()

    def _on_canvas_release(self, event):
        if self._drag_label is None:
            return
        x_frac, y_frac = self._drag_label.get_position()
        self._drag_dataset.label_x = x_frac
        self._drag_dataset.label_y = y_frac
        self._drag_label = None
        self._drag_dataset = None
        self._drag_ax = None

    def _handle_double_click(self, event):
        # 1) 双击某个数据名称标注 -> 弹出该数据的编辑窗口
        for label, ds in self._label_to_dataset.items():
            contains, _ = label.contains(event)
            if contains:
                self._open_dataset_dialog(ds)
                return

        # 2) 双击某条曲线 -> 弹出该数据的编辑窗口
        if event.inaxes is not None:
            for line, ds in self._line_to_dataset.items():
                contains, _ = line.contains(event)
                if contains:
                    self._open_dataset_dialog(ds)
                    return

        # 3) 双击 X / Y 轴标题或刻度文字 -> 弹出对应坐标轴的设置窗口
        try:
            renderer = self.canvas.get_renderer()
        except AttributeError:
            renderer = None
        if renderer is None:
            return

        for ax in self.fig.axes:
            x_targets = [ax.xaxis.label] + list(ax.get_xticklabels())
            for t in x_targets:
                if t.get_window_extent(renderer=renderer).contains(event.x, event.y):
                    self._open_axis_dialog("X")
                    return
            y_targets = [ax.yaxis.label] + list(ax.get_yticklabels())
            for t in y_targets:
                if t.get_window_extent(renderer=renderer).contains(event.x, event.y):
                    self._open_axis_dialog("Y")
                    return

        # 堆叠图的 Y 轴标题是整张图共用的 fig.supylabel，不属于任何单个 ax
        for t in self.fig.texts:
            if t.get_window_extent(renderer=renderer).contains(event.x, event.y):
                self._open_axis_dialog("Y")
                return

    def _open_dataset_dialog(self, dataset):
        dlg = DatasetEditDialog(dataset, self)
        if dlg.exec():
            dlg.apply_to_dataset()
            row = self.dataset_panel.datasets.index(dataset)
            self.dataset_panel._rebuild_list(keep_row=row)
            self.dataset_panel.dataChanged.emit()

    def _open_axis_dialog(self, axis_label):
        style = self.style_panel.style
        current = style.x_title if axis_label == "X" else style.y_title
        dlg = AxisTitleDialog(axis_label, current, self)
        if dlg.exec():
            new_title = dlg.title_text() or current
            if axis_label == "X":
                style.x_title = new_title
            else:
                style.y_title = new_title
            self.style_panel._load_from_style()

    def _export_image(self):
        if not self.dataset_panel.datasets:
            QMessageBox.information(self, "没有数据", "请先导入并显示至少一套 XRD 数据。")
            return

        path, selected_filter = QFileDialog.getSaveFileName(
            self, "导出图片", "", EXPORT_FILTERS
        )
        if not path:
            return

        root, ext = os.path.splitext(path)
        if not ext:
            path += EXPORT_DEFAULT_EXT.get(selected_filter, ".png")

        try:
            # transparent=True：导出时背景透明（屏幕上仍然是白底，方便查看），
            # 这样放进 Illustrator 之类的软件里可以直接叠加在别的图层上。
            self.fig.savefig(path, dpi=self.style_panel.style.dpi, transparent=True)
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))
            return

        QMessageBox.information(self, "导出成功", f"已保存到：\n{path}")
