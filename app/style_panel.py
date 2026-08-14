from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout,
    QGroupBox, QLineEdit, QSpinBox, QVBoxLayout, QWidget,
)

from .plot_style import FONT_CHOICES, PlotStyle
from .theme import THEME_LABELS, build_qss


class StylePanel(QWidget):
    """右 / 左侧可折叠面板：控制作图款式与全局样式（图幅、字体、坐标轴标题等），
    以及整个界面的配色主题。
    """

    styleChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.style = PlotStyle()
        self.current_theme = "white"
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ---- 界面主题（整个 GUI 的配色；不影响绘图区，绘图区始终白底，
        # 也不影响工具栏/图标，保证按钮图标始终清晰可见） ----
        theme_group = QGroupBox("界面主题")
        theme_form = QFormLayout(theme_group)
        self.theme_combo = QComboBox()
        for key, label in THEME_LABELS.items():
            self.theme_combo.addItem(label, key)
        theme_form.addRow("主题", self.theme_combo)
        layout.addWidget(theme_group)

        # ---- 作图款式 ----
        mode_group = QGroupBox("作图款式")
        mode_form = QFormLayout(mode_group)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("堆叠图 Stack（各数据独立 XY 轴，平行拼接）", "stack")
        self.mode_combo.addItem("瀑布图 Waterfall（共用坐标框，Y 方向依次偏移）", "waterfall")
        mode_form.addRow("模式", self.mode_combo)
        layout.addWidget(mode_group)

        # ---- 图幅（公制单位：厘米） ----
        fig_group = QGroupBox("图幅尺寸 / 比例")
        fig_form = QFormLayout(fig_group)
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(2.0, 100.0)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.setSuffix(" cm")
        fig_form.addRow("宽度", self.width_spin)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(2.0, 150.0)
        self.height_spin.setSingleStep(0.5)
        self.height_spin.setSuffix(" cm")
        fig_form.addRow("高度", self.height_spin)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(50, 600)
        self.dpi_spin.setSingleStep(10)
        fig_form.addRow("DPI", self.dpi_spin)
        layout.addWidget(fig_group)

        # ---- 字体 ----
        font_group = QGroupBox("字体")
        font_form = QFormLayout(font_group)
        self.font_combo = QComboBox()
        self.font_combo.addItems(FONT_CHOICES)
        font_form.addRow("字体", self.font_combo)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 40)
        font_form.addRow("字号", self.font_size_spin)
        layout.addWidget(font_group)

        # ---- 坐标轴标题 ----
        axis_group = QGroupBox("坐标轴标题")
        axis_form = QFormLayout(axis_group)
        self.x_title_edit = QLineEdit()
        axis_form.addRow("X 轴标题", self.x_title_edit)
        self.y_title_edit = QLineEdit()
        axis_form.addRow("Y 轴标题", self.y_title_edit)

        self.x_submark_spin = QSpinBox()
        self.x_submark_spin.setRange(0, 4)
        self.x_submark_spin.setSpecialValueText("不显示")
        self.x_submark_spin.setToolTip(
            "在主刻度之间画不带数字的子刻度：1 = 每格中点画一道（长度减半）；\n"
            "2 = 在此基础上再对半分一次（更短）；以此类推。"
        )
        axis_form.addRow("X 轴子刻度阶数", self.x_submark_spin)
        layout.addWidget(axis_group)

        # ---- 其它 ----
        misc_group = QGroupBox("其它")
        misc_form = QFormLayout(misc_group)

        self.normalize_check = QCheckBox("归一化强度 (0-1)，便于对比峰形")
        misc_form.addRow(self.normalize_check)

        self.offset_step_spin = QDoubleSpinBox()
        self.offset_step_spin.setRange(0.0, 1e9)
        self.offset_step_spin.setSingleStep(0.1)
        self.offset_step_spin.setDecimals(3)
        misc_form.addRow("瀑布图 Y 偏移量", self.offset_step_spin)

        self.stack_spacing_spin = QDoubleSpinBox()
        self.stack_spacing_spin.setRange(0.0, 1.0)
        self.stack_spacing_spin.setSingleStep(0.01)
        self.stack_spacing_spin.setDecimals(3)
        misc_form.addRow("堆叠图间距", self.stack_spacing_spin)

        self.grid_check = QCheckBox("显示网格线")
        misc_form.addRow(self.grid_check)

        self.legend_check = QCheckBox("显示图例（瀑布图）")
        misc_form.addRow(self.legend_check)

        layout.addWidget(misc_group)
        layout.addStretch(1)

        self._load_from_style()

        # 信号：界面主题单独处理（只套用样式表，不参与 PlotStyle / styleChanged）
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        # 其余控件变化都同步回 self.style 并广播 styleChanged
        self.mode_combo.currentIndexChanged.connect(self._on_changed)
        self.width_spin.valueChanged.connect(self._on_changed)
        self.height_spin.valueChanged.connect(self._on_changed)
        self.dpi_spin.valueChanged.connect(self._on_changed)
        self.font_combo.currentTextChanged.connect(self._on_changed)
        self.font_size_spin.valueChanged.connect(self._on_changed)
        self.x_title_edit.textChanged.connect(self._on_changed)
        self.y_title_edit.textChanged.connect(self._on_changed)
        self.x_submark_spin.valueChanged.connect(self._on_changed)
        self.normalize_check.toggled.connect(self._on_changed)
        self.offset_step_spin.valueChanged.connect(self._on_changed)
        self.stack_spacing_spin.valueChanged.connect(self._on_changed)
        self.grid_check.toggled.connect(self._on_changed)
        self.legend_check.toggled.connect(self._on_changed)

        # 启动时套用一次默认界面主题
        self._on_theme_changed()

    def _load_from_style(self):
        """把 self.style 反映到各个控件上；期间屏蔽 changed 信号，避免逐个
        setValue/setCurrentIndex 时提前触发 _on_changed() 读到半成品状态。
        """
        s = self.style
        widgets = (
            self.mode_combo, self.width_spin, self.height_spin,
            self.dpi_spin, self.font_combo, self.font_size_spin, self.x_title_edit,
            self.y_title_edit, self.x_submark_spin, self.normalize_check, self.offset_step_spin,
            self.stack_spacing_spin, self.grid_check, self.legend_check,
        )
        for w in widgets:
            w.blockSignals(True)
        try:
            self.mode_combo.setCurrentIndex(self.mode_combo.findData(s.mode))
            self.width_spin.setValue(s.fig_width_cm)
            self.height_spin.setValue(s.fig_height_cm)
            self.dpi_spin.setValue(s.dpi)
            idx = self.font_combo.findText(s.font_family)
            self.font_combo.setCurrentIndex(idx if idx >= 0 else 0)
            self.font_size_spin.setValue(s.font_size)
            self.x_title_edit.setText(s.x_title)
            self.y_title_edit.setText(s.y_title)
            self.x_submark_spin.setValue(s.x_submark_order)
            self.normalize_check.setChecked(s.normalize)
            self.offset_step_spin.setValue(s.offset_step)
            self.stack_spacing_spin.setValue(s.stack_spacing)
            self.grid_check.setChecked(s.show_grid)
            self.legend_check.setChecked(s.show_legend)
        finally:
            for w in widgets:
                w.blockSignals(False)

        theme_idx = self.theme_combo.findData(self.current_theme)
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(theme_idx if theme_idx >= 0 else 0)
        self.theme_combo.blockSignals(False)

        self.styleChanged.emit()

    def _on_theme_changed(self, *_args):
        self.current_theme = self.theme_combo.currentData() or "white"
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_qss(self.current_theme))

    def _on_changed(self, *_args):
        s = self.style
        s.mode = self.mode_combo.currentData()
        s.fig_width_cm = self.width_spin.value()
        s.fig_height_cm = self.height_spin.value()
        s.dpi = self.dpi_spin.value()
        s.font_family = self.font_combo.currentText()
        s.font_size = self.font_size_spin.value()
        s.x_title = self.x_title_edit.text() or "2 Theta (degree)"
        s.y_title = self.y_title_edit.text() or "Intensity"
        s.x_submark_order = self.x_submark_spin.value()
        s.normalize = self.normalize_check.isChecked()
        s.offset_step = self.offset_step_spin.value()
        s.stack_spacing = self.stack_spacing_spin.value()
        s.show_grid = self.grid_check.isChecked()
        s.show_legend = self.legend_check.isChecked()
        self.styleChanged.emit()
