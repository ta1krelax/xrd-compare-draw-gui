import numpy as np
import matplotlib

LINE_PICK_RADIUS = 6  # 曲线可点击命中的容差（像素），用于双击弹出编辑窗口
LABEL_PICK_RADIUS = 6  # 数据名称标注的点击命中容差（像素）
MAJOR_TICK_LEN_PT = 5.0  # X 轴主刻度长度（点），子刻度按这个长度递减


def _normalize01(y):
    y = np.asarray(y, dtype=float)
    y_min, y_max = np.nanmin(y), np.nanmax(y)
    if y_max - y_min < 1e-12:
        return np.zeros_like(y)
    return (y - y_min) / (y_max - y_min)


def _apply_font(style):
    # 把用户选择的字体放在候选列表最前面，后面跟中/英文兜底字体，
    # 避免选了某些机器上没装的字体时中文/负号显示成方块或 "?"。
    matplotlib.rcParams["font.sans-serif"] = [
        style.font_family, "Microsoft YaHei", "SimHei", "DejaVu Sans",
    ]
    matplotlib.rcParams["font.family"] = "sans-serif"
    matplotlib.rcParams["font.size"] = style.font_size
    matplotlib.rcParams["axes.unicode_minus"] = False


def _prep_y(dataset, style):
    y = _normalize01(dataset.intensity) if style.normalize else np.asarray(dataset.intensity, dtype=float)
    return y * dataset.scale + dataset.offset


def _bisection_submarks(major_ticks, order):
    """按倍分方式递归生成子刻度位置：level=1 是每个主刻度间隔的中点；
    level=2 是把 level 1 产生的每个小段再对半分一次的中点；以此类推。
    返回 [(位置, 层级), ...]，层级越大对应刻度线越短。
    """
    if order <= 0 or len(major_ticks) < 2:
        return []
    result = []
    points = sorted(major_ticks)
    for level in range(1, order + 1):
        new_points = []
        for a, b in zip(points[:-1], points[1:]):
            mid = (a + b) / 2.0
            new_points.append(mid)
            result.append((mid, level))
        points = sorted(points + new_points)
    return result


def _draw_x_submarks(ax, order):
    """在 X 轴主刻度之间画不带数字的子刻度线，长度随层级递减。"""
    if order <= 0:
        return
    xlim = ax.get_xlim()
    major_ticks = [t for t in ax.get_xticks() if xlim[0] <= t <= xlim[1]]
    trans = ax.get_xaxis_transform()  # x: 数据坐标；y: 坐标轴分数坐标 (0=底部)
    for pos, level in _bisection_submarks(major_ticks, order):
        if not (min(xlim) <= pos <= max(xlim)):
            continue
        length_pt = MAJOR_TICK_LEN_PT * (0.5 ** level)
        ax.annotate(
            "", xy=(pos, 0), xycoords=trans,
            xytext=(0, -length_pt), textcoords="offset points",
            arrowprops=dict(arrowstyle="-", color="black", linewidth=0.8, shrinkA=0, shrinkB=0),
            annotation_clip=False,
        )


def render_plot(fig, datasets, style):
    """按当前样式设置，把 datasets 画到给定的 matplotlib Figure 上。

    绘图区始终使用白底黑字（不跟随界面主题），方便截图/打印看得清楚；
    导出图片时另外单独把背景设成透明，见 main_window._export_image。

    返回 {"lines": {Line2D: Dataset}, "labels": {Text: Dataset}}，供主窗口做
    双击/拖拽命中测试（双击曲线或名称标注弹出编辑窗口，拖动名称标注调整位置）。
    """
    _apply_font(style)
    fig.clear()

    visible = [d for d in datasets if d.visible]
    if not visible:
        ax = fig.add_subplot(111)
        ax.text(
            0.5, 0.5, "Import XRD data from the left panel",
            ha="center", va="center", transform=ax.transAxes,
            fontsize=style.font_size + 2, color="gray",
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        return {"lines": {}, "labels": {}}

    if style.mode == "stack":
        return _render_stack(fig, visible, style)
    else:
        return _render_waterfall(fig, visible, style)


def _render_stack(fig, visible, style):
    n = len(visible)
    axes = fig.subplots(n, 1, sharex=False, squeeze=False)[:, 0]
    line_to_dataset = {}
    label_to_dataset = {}
    for i, (ax, d) in enumerate(zip(axes, visible)):
        y = _prep_y(d, style)
        line, = ax.plot(d.two_theta, y, color=d.color, linewidth=d.linewidth, pickradius=LINE_PICK_RADIUS)
        line_to_dataset[line] = d

        ha = "right" if d.label_x >= 0.5 else "left"
        label = ax.text(
            d.label_x, d.label_y, d.name, transform=ax.transAxes,
            fontsize=style.font_size, ha=ha, va="top", picker=LABEL_PICK_RADIUS,
        )
        label_to_dataset[label] = d

        ax.tick_params(axis="x", which="major", length=MAJOR_TICK_LEN_PT, direction="out")
        _draw_x_submarks(ax, style.x_submark_order)
        if style.show_grid:
            ax.grid(True, alpha=0.3)
        if i != n - 1:
            ax.set_xticklabels([])
    axes[-1].set_xlabel(style.x_title)
    fig.supylabel(style.y_title)
    fig.subplots_adjust(
        hspace=style.stack_spacing,
        left=0.12, right=0.97, top=0.95, bottom=0.09,
    )
    return {"lines": line_to_dataset, "labels": label_to_dataset}


def _render_waterfall(fig, visible, style):
    ax = fig.add_subplot(111)
    line_to_dataset = {}
    for i, d in enumerate(visible):
        y = _prep_y(d, style) + i * style.offset_step
        line, = ax.plot(d.two_theta, y, color=d.color, linewidth=d.linewidth,
                         label=d.name, pickradius=LINE_PICK_RADIUS)
        line_to_dataset[line] = d
    ax.set_yticks([])
    ax.set_xlabel(style.x_title)
    ax.set_ylabel(style.y_title)
    ax.tick_params(axis="x", which="major", length=MAJOR_TICK_LEN_PT, direction="out")
    _draw_x_submarks(ax, style.x_submark_order)
    if style.show_grid:
        ax.grid(True, axis="x", alpha=0.3)
    if style.show_legend:
        ax.legend(loc="upper right", fontsize=max(style.font_size - 2, 6), frameon=False)
    fig.tight_layout()
    return {"lines": line_to_dataset, "labels": {}}
