"""生成几套合成的 XRD 样例数据，方便试用本工具的各项功能。

格式模仿用户提供的原始文件：第一行是表头占位符，后面是
"2theta<空格>intensity" 两列，2theta 从 10 到 60 度，步长 0.02。
"""
import os

import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")


def gaussian(x, center, height, width):
    return height * np.exp(-0.5 * ((x - center) / width) ** 2)


def make_pattern(two_theta, peaks, background=8.0, noise=3.0, seed=0):
    rng = np.random.default_rng(seed)
    y = np.full_like(two_theta, background, dtype=float)
    for center, height, width in peaks:
        y += gaussian(two_theta, center, height, width)
    y += rng.normal(0, noise, size=two_theta.shape)
    y = np.clip(y, 0, None)
    return y


def write_file(path, two_theta, intensity):
    with open(path, "w", encoding="utf-8") as f:
        f.write("?\n")
        for x, y in zip(two_theta, intensity):
            f.write(f"{x:.2f}\t{y:.1f}\n")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    two_theta = np.arange(10.0, 60.0, 0.02)

    samples = {
        "Sample_A_anatase_like.txt": [
            (25.3, 400, 0.15), (37.8, 90, 0.15), (48.0, 150, 0.15), (54.0, 80, 0.2),
        ],
        "Sample_B_rutile_like.txt": [
            (27.4, 500, 0.12), (36.1, 200, 0.15), (41.2, 120, 0.15), (54.3, 130, 0.18),
        ],
        "Sample_C_mixed_phase.txt": [
            (25.3, 220, 0.15), (27.4, 260, 0.13), (37.8, 60, 0.15), (36.1, 100, 0.15),
            (48.0, 90, 0.15), (54.0, 70, 0.2),
        ],
        "Sample_D_low_crystallinity.txt": [
            (25.3, 60, 0.4), (27.4, 50, 0.4), (37.8, 20, 0.4),
        ],
    }

    for i, (fname, peaks) in enumerate(samples.items()):
        y = make_pattern(two_theta, peaks, seed=i)
        write_file(os.path.join(OUT_DIR, fname), two_theta, y)
        print(f"wrote {fname}")


if __name__ == "__main__":
    main()
