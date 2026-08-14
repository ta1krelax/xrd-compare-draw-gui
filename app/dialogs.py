"""双击图上元素时弹出的小编辑窗口：双击某条曲线 -> 编辑该数据；
双击 X/Y 轴标题或刻度文字 -> 编辑对应坐标轴标题。
"""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout,
    QLineEdit, QPushButton,
)


class DatasetEditDialog(QDialog):
    def __init__(self, dataset, parent=None):
        super().__init__(parent)
        self.dataset = dataset
        self._color = dataset.color
        self.setWindowTitle(f"编辑数据 - {dataset.name}")

        form = QFormLayout(self)

        self.name_edit = QLineEdit(dataset.name)
        form.addRow("名称", self.name_edit)

        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(70, 22)
        self.color_btn.clicked.connect(self._pick_color)
        form.addRow("颜色", self.color_btn)
        self._update_color_btn()

        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.2, 10.0)
        self.linewidth_spin.setSingleStep(0.1)
        self.linewidth_spin.setValue(dataset.linewidth)
        form.addRow("线宽", self.linewidth_spin)

        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-1e9, 1e9)
        self.offset_spin.setSingleStep(0.1)
        self.offset_spin.setDecimals(3)
        self.offset_spin.setValue(dataset.offset)
        form.addRow("Y 方向额外偏移", self.offset_spin)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.001, 1000.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setDecimals(3)
        self.scale_spin.setValue(dataset.scale)
        form.addRow("强度缩放倍数", self.scale_spin)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        form.addRow(btn_box)

    def _update_color_btn(self):
        self.color_btn.setStyleSheet(f"background-color:{self._color}; border:1px solid #666;")

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self, "选择线条颜色")
        if color.isValid():
            self._color = color.name()
            self._update_color_btn()

    def apply_to_dataset(self):
        self.dataset.name = self.name_edit.text().strip() or self.dataset.name
        self.dataset.color = self._color
        self.dataset.linewidth = self.linewidth_spin.value()
        self.dataset.offset = self.offset_spin.value()
        self.dataset.scale = self.scale_spin.value()


class AxisTitleDialog(QDialog):
    def __init__(self, axis_label, current_title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{axis_label} 轴设置")

        form = QFormLayout(self)
        self.title_edit = QLineEdit(current_title)
        form.addRow(f"{axis_label} 轴标题", self.title_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        form.addRow(btn_box)

    def title_text(self):
        return self.title_edit.text().strip()
