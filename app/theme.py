"""整个界面（面板、按钮、控件背景）的配色主题。

刻意不设置任何 font-family：交给 Qt 用系统默认字体渲染，中文才不会
因为字体名对不上而变成方块。工具栏（含 matplotlib 导航工具条）的图标是
黑色线条图，所以工具栏背景在所有主题下都固定用浅色，不跟随主题变深，
保证图标始终看得清楚。
"""

THEMES = {
    "white": {
        "app_bg": "#f4f6fa",
        "panel_bg": "#ffffff",
        "text": "#1f2430",
        "border": "#d7dbe3",
        "accent": "#3568d4",
    },
    "black": {
        "app_bg": "#1c1f26",
        "panel_bg": "#262a33",
        "text": "#e7e9f0",
        "border": "#3a3f4c",
        "accent": "#6c9bff",
    },
    "yellow": {
        "app_bg": "#fbf3d9",
        "panel_bg": "#fff8e6",
        "text": "#4a3a10",
        "border": "#e3d3a0",
        "accent": "#a8790a",
    },
    "green": {
        "app_bg": "#d9e8d3",
        "panel_bg": "#e9f3e2",
        "text": "#2b3a2b",
        "border": "#b7cdac",
        "accent": "#3f7a3d",
    },
}

THEME_LABELS = {
    "white": "白色",
    "black": "黑色",
    "yellow": "黄色",
    "green": "绿色",
}

_TOOLBAR_BG = "#f0f0f0"
_TOOLBAR_FG = "#202020"


def build_qss(theme):
    t = THEMES.get(theme, THEMES["white"])
    return f"""
    QWidget {{
        background-color: {t['app_bg']};
        color: {t['text']};
        font-size: 10pt;
    }}
    QLabel, QCheckBox, QRadioButton {{
        background: transparent;
    }}
    QToolBar, QToolButton {{
        background-color: {_TOOLBAR_BG};
        color: {_TOOLBAR_FG};
        border: none;
    }}
    QDockWidget::title {{
        background: {t['panel_bg']};
        padding: 6px 8px;
        border-bottom: 1px solid {t['border']};
        font-weight: 600;
    }}
    QGroupBox {{
        background-color: {t['panel_bg']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        margin-top: 14px;
        padding: 10px 8px 8px 8px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: {t['accent']};
    }}
    QPushButton {{
        background-color: {t['panel_bg']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        padding: 5px 12px;
        color: {t['text']};
    }}
    QPushButton:hover {{
        border-color: {t['accent']};
        color: {t['accent']};
    }}
    QPushButton:pressed {{
        background-color: {t['accent']};
        color: white;
    }}
    QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {{
        background-color: {t['panel_bg']};
        border: 1px solid {t['border']};
        border-radius: 5px;
        padding: 3px 6px;
        color: {t['text']};
    }}
    QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {t['accent']};
    }}
    QListWidget {{
        background-color: {t['panel_bg']};
        border: 1px solid {t['border']};
        border-radius: 6px;
        color: {t['text']};
    }}
    QListWidget::item:selected {{
        background-color: {t['accent']};
        color: white;
        border-radius: 4px;
    }}
    QScrollArea {{
        border: none;
    }}
    """
