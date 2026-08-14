import itertools
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QColorDialog, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .data_io import load_xrd_txt
from .models import Dataset
from .plot_style import TAB10_COLORS

FILE_FILTER = "XRD 文本数据 (*.txt *.dat *.csv *.xy);;所有文件 (*)"


class _RowWidget(QWidget):
    """数据列表中每一行：可见性勾选框 + 颜色色块 + 名称。"""

    def __init__(self, dataset, on_visible_toggled, on_color_clicked, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(dataset.visible)
        self.checkbox.toggled.connect(lambda checked: on_visible_toggled(dataset, checked))
        layout.addWidget(self.checkbox)

        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(18, 18)
        self.color_btn.setStyleSheet(f"background-color:{dataset.color}; border:1px solid #666;")
        self.color_btn.clicked.connect(lambda: on_color_clicked(dataset))
        layout.addWidget(self.color_btn)

        self.name_label = QLabel(dataset.name)
        layout.addWidget(self.name_label, 1)


class DatasetPanel(QWidget):
    """左侧可折叠面板：导入 / 删除 / 排序 / 编辑每套 XRD 数据。"""

    dataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.datasets: list[Dataset] = []
        self._color_cycle = itertools.cycle(TAB10_COLORS)
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("导入数据…")
        self.btn_remove = QPushButton("删除")
        self.btn_up = QPushButton("↑")
        self.btn_down = QPushButton("↓")
        for b in (self.btn_add, self.btn_remove, self.btn_up, self.btn_down):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.list_widget, 1)

        self.prop_group = QGroupBox("数据属性编辑")
        form = QFormLayout(self.prop_group)

        self.name_edit = QLineEdit()
        form.addRow("名称", self.name_edit)

        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(70, 22)
        form.addRow("颜色", self.color_btn)

        self.linewidth_spin = QDoubleSpinBox()
        self.linewidth_spin.setRange(0.2, 10.0)
        self.linewidth_spin.setSingleStep(0.1)
        form.addRow("线宽", self.linewidth_spin)

        self.offset_spin = QDoubleSpinBox()
        self.offset_spin.setRange(-1e9, 1e9)
        self.offset_spin.setSingleStep(0.1)
        self.offset_spin.setDecimals(3)
        form.addRow("Y 方向额外偏移", self.offset_spin)

        self.scale_spin = QDoubleSpinBox()
        self.scale_spin.setRange(0.001, 1000.0)
        self.scale_spin.setSingleStep(0.1)
        self.scale_spin.setDecimals(3)
        form.addRow("强度缩放倍数", self.scale_spin)

        layout.addWidget(self.prop_group)
        self.prop_group.setEnabled(False)

        # ---- 信号连接 ----
        self.btn_add.clicked.connect(self._add_files)
        self.btn_remove.clicked.connect(self._remove_selected)
        self.btn_up.clicked.connect(lambda: self._move(-1))
        self.btn_down.clicked.connect(lambda: self._move(1))
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        self.name_edit.editingFinished.connect(self._apply_props)
        self.color_btn.clicked.connect(self._pick_color_for_selected)
        self.linewidth_spin.valueChanged.connect(self._apply_props)
        self.offset_spin.valueChanged.connect(self._apply_props)
        self.scale_spin.valueChanged.connect(self._apply_props)

    # ------------------------------------------------------------- helpers
    def _rebuild_list(self, keep_row=None):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for ds in self.datasets:
            item = QListWidgetItem()
            row_widget = _RowWidget(ds, self._on_visible_toggled, self._pick_color_for)
            item.setSizeHint(row_widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, row_widget)
        self.list_widget.blockSignals(False)

        if keep_row is not None and 0 <= keep_row < len(self.datasets):
            self.list_widget.setCurrentRow(keep_row)
        elif self.datasets:
            self.list_widget.setCurrentRow(min(keep_row or 0, len(self.datasets) - 1))
        else:
            self._on_selection_changed(-1)

    def _current_dataset(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self.datasets):
            return row, self.datasets[row]
        return -1, None

    # --------------------------------------------------------------- slots
    def _add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择 XRD 数据文件", "", FILE_FILTER)
        if not paths:
            return

        added_any = False
        for p in paths:
            try:
                x, y = load_xrd_txt(p)
            except Exception as e:
                QMessageBox.warning(self, "导入失败", f"{os.path.basename(p)} 解析失败：\n{e}")
                continue
            name = os.path.splitext(os.path.basename(p))[0]
            ds = Dataset(name=name, two_theta=x, intensity=y, path=p, color=next(self._color_cycle))
            self.datasets.append(ds)
            added_any = True

        if added_any:
            self._rebuild_list(keep_row=len(self.datasets) - 1)
            self.dataChanged.emit()

    def _remove_selected(self):
        row, ds = self._current_dataset()
        if ds is None:
            return
        del self.datasets[row]
        self._rebuild_list(keep_row=row)
        self.dataChanged.emit()

    def _move(self, delta):
        row, ds = self._current_dataset()
        if ds is None:
            return
        new_row = row + delta
        if not (0 <= new_row < len(self.datasets)):
            return
        self.datasets[row], self.datasets[new_row] = self.datasets[new_row], self.datasets[row]
        self._rebuild_list(keep_row=new_row)
        self.dataChanged.emit()

    def _on_visible_toggled(self, dataset, checked):
        dataset.visible = checked
        self.dataChanged.emit()

    def _pick_color_for_selected(self):
        _, ds = self._current_dataset()
        if ds is not None:
            self._pick_color_for(ds)

    def _pick_color_for(self, dataset):
        color = QColorDialog.getColor(QColor(dataset.color), self, "选择线条颜色")
        if not color.isValid():
            return
        dataset.color = color.name()
        row = self.datasets.index(dataset)
        self._rebuild_list(keep_row=row)
        self.dataChanged.emit()

    def _on_selection_changed(self, row):
        if not (0 <= row < len(self.datasets)):
            self.prop_group.setEnabled(False)
            return
        ds = self.datasets[row]
        self.prop_group.setEnabled(True)

        for w in (self.name_edit, self.linewidth_spin, self.offset_spin, self.scale_spin):
            w.blockSignals(True)
        self.name_edit.setText(ds.name)
        self.linewidth_spin.setValue(ds.linewidth)
        self.offset_spin.setValue(ds.offset)
        self.scale_spin.setValue(ds.scale)
        for w in (self.name_edit, self.linewidth_spin, self.offset_spin, self.scale_spin):
            w.blockSignals(False)
        self.color_btn.setStyleSheet(f"background-color:{ds.color}; border:1px solid #666;")

    def _apply_props(self):
        row, ds = self._current_dataset()
        if ds is None:
            return
        ds.name = self.name_edit.text().strip() or ds.name
        ds.linewidth = self.linewidth_spin.value()
        ds.offset = self.offset_spin.value()
        ds.scale = self.scale_spin.value()
        # 名称可能变了，刷新列表里的文字，同时保持选中行不变
        self._rebuild_list(keep_row=row)
        self.dataChanged.emit()
