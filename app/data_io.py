import numpy as np

# 依次尝试的文件编码：多数国产/进口衍射仪导出的文本要么是 utf-8，要么是 gbk 或纯 ascii。
ENCODINGS_TO_TRY = ("utf-8", "gbk", "latin-1")


def load_xrd_txt(path):
    """从 XRD 原始文本文件中解析出 (2theta, intensity) 两列数据。

    对格式很宽容：会自动跳过表头/注释等无法解析成两个数字的行，
    支持空格、制表符或逗号分隔，并按 2theta 升序排序后返回。
    """
    text = None
    last_err = None
    for enc in ENCODINGS_TO_TRY:
        try:
            with open(path, "r", encoding=enc) as f:
                text = f.read()
            break
        except (UnicodeDecodeError, UnicodeError) as e:
            last_err = e
            continue
    if text is None:
        raise ValueError(f"无法解码文件（尝试了 {ENCODINGS_TO_TRY}）：{last_err}")

    xs = []
    ys = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.replace(",", " ").split()
        if len(parts) < 2:
            continue
        try:
            x = float(parts[0])
            y = float(parts[1])
        except ValueError:
            continue
        xs.append(x)
        ys.append(y)

    if len(xs) < 2:
        raise ValueError("未能从文件中解析出有效的两列数值数据（2theta / 强度）")

    x_arr = np.asarray(xs, dtype=float)
    y_arr = np.asarray(ys, dtype=float)
    order = np.argsort(x_arr)
    return x_arr[order], y_arr[order]
