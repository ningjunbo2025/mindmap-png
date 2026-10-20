# -*- coding: utf-8 -*-
"""把 mindmap_data.TREE 渲染成一张横向思维导图 PNG。

布局：根在左，单向往右展开。每个大分支有自己的浅色底纹区 + 专属色。
连线：细虚线贝塞尔曲线。

用法：
    python render_mindmap.py                  # 作业版（不显示真题年份）
    python render_mindmap.py --year           # 私用版（显示真题年份）
"""
import argparse
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch, PathPatch
from matplotlib.path import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mindmap_data import TREE, BRANCH_STYLES, TITLE, SUBTITLE  # noqa: E402

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["mathtext.fontset"] = "dejavusans"

def _first_existing(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


FONT_REG = _first_existing([
    "C:/Windows/Fonts/msyh.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
])
FONT_BOLD = _first_existing([
    "C:/Windows/Fonts/msyhbd.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
])

# ----------------------------------------------------------------- 版面参数
DEPTH_CFG = [
    # fs = 字号(pt)；maxw = 单行文本最大宽度(英寸)
    {"fs": 17.5, "maxw": 1.55},   # 0 根
    {"fs": 12.5, "maxw": 2.10},   # 1 大分支
    {"fs": 10.0, "maxw": 3.00},   # 2
    {"fs": 9.0,  "maxw": 3.35},   # 3
    {"fs": 8.4,  "maxw": 3.60},   # 4
    {"fs": 8.0,  "maxw": 3.80},   # 5
    {"fs": 7.9,  "maxw": 3.80},   # 6
]
MIN_GAP = 0.115         # 同一列内相邻框之间的最小垂直净距（英寸）
COL_GAP = 0.60          # 列与列之间的水平间距
PAD_X = 0.19            # 文字左右内边距（单边）
PAD_Y = 0.085           # 文字上下内边距（单边）
LINE_SPACING = 1.22     # 行高倍数
TITLE_ZONE = 1.45
MARGIN_L, MARGIN_R, MARGIN_B = 0.55, 0.45, 0.45

MATH_RE = re.compile(r"[$^{}_]")


def cfg_for(d):
    return DEPTH_CFG[min(d, len(DEPTH_CFG) - 1)]


def char_w(ch, fs):
    """估算单个字符宽度（英寸）。CJK 按正方形，拉丁/数字按 0.55 方。"""
    return (fs / 72.0) * (1.0 if ord(ch) > 0x2E7F else 0.55)


def tokenize(s):
    """把字符串切成不可分割的单元：$...$ 数学片段整块保留，其余逐字符。"""
    toks, i, n = [], 0, len(s)
    while i < n:
        if s[i] == "$":
            j = s.find("$", i + 1)
            if j == -1:
                toks.append(s[i:])
                break
            toks.append(s[i:j + 1])
            i = j + 1
        else:
            toks.append(s[i])
            i += 1
    return toks


def tok_w(t, fs):
    if len(t) > 1 and t.startswith("$") and t.endswith("$"):
        return sum(char_w(c, fs) for c in MATH_RE.sub("", t)) * 0.88
    return char_w(t, fs)


def wrap_text(text, maxw, fs):
    """按显式换行切段，再按宽度折行；$...$ 视为整体不拆开。"""
    out = []
    for para in text.split("\n"):
        if not para:
            out.append("")
            continue
        cur, cw = "", 0.0
        for t in tokenize(para):
            w = tok_w(t, fs)
            if cur and cw + w > maxw:
                out.append(cur)
                cur, cw = t, w
            else:
                cur += t
                cw += w
        out.append(cur)
    return out


def lighten(hexc, f):
    hexc = hexc.lstrip("#")
    r, g, b = int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16)
    return "#%02X%02X%02X" % (
        int(r + (255 - r) * f), int(g + (255 - g) * f), int(b + (255 - b) * f))


# ----------------------------------------------------------------- 1. 布局
def build(show_year):
    nodes = []

    def walk(node, depth, parent, bidx):
        node["_depth"] = depth
        node["_parent"] = parent
        node["_bidx"] = bidx
        nodes.append(node)
        for i, c in enumerate(node["children"]):
            walk(c, depth + 1, node, bidx if depth > 0 else i)

    walk(TREE, 0, None, -1)

    # 先算尺寸（折行依赖字号，字号依赖深度）
    for n in nodes:
        d = n["_depth"]
        fs, maxw = cfg_for(d)["fs"], cfg_for(d)["maxw"]
        lines = wrap_text(n["text"], maxw, fs)
        if show_year and n["year"]:
            lines.append("（%s）" % n["year"])
        n["_fs"] = fs
        n["_lines"] = lines
        n["_w"] = max(sum(tok_w(t, fs) for t in tokenize(ln)) for ln in lines) + PAD_X * 2
        n["_h"] = len(lines) * (fs / 72.0) * LINE_SPACING + PAD_Y * 2

    maxd = max(n["_depth"] for n in nodes)
    colw = [max(n["_w"] for n in nodes if n["_depth"] == d) for d in range(maxd + 1)]
    xleft = [0.0]
    for d in range(maxd):
        xleft.append(xleft[d] + colw[d] + COL_GAP)
    for n in nodes:
        n["_x"] = xleft[n["_depth"]]

    # 纵向：叶子按实际框高依次排开，父节点取子节点中点
    cursor = [0.0]

    def assign_y(node):
        if not node["children"]:
            node["_y"] = cursor[0] + node["_h"] / 2.0
            cursor[0] = node["_y"] + node["_h"] / 2.0 + MIN_GAP
        else:
            for c in node["children"]:
                assign_y(c)
            node["_y"] = (node["children"][0]["_y"] + node["children"][-1]["_y"]) / 2.0

    assign_y(TREE)

    ymin = min(n["_y"] - n["_h"] / 2 for n in nodes)
    ymax = max(n["_y"] + n["_h"] / 2 for n in nodes)
    return nodes, xleft, colw, ymin, ymax


def check_overlaps(nodes):
    """同一列内任何两个框都不应重叠，返回冲突清单。"""
    bad = []
    by_depth = {}
    for n in nodes:
        by_depth.setdefault(n["_depth"], []).append(n)
    for d, group in by_depth.items():
        group.sort(key=lambda x: x["_y"])
        for a, b in zip(group, group[1:]):
            need = (a["_h"] + b["_h"]) / 2.0 + MIN_GAP * 0.5
            if b["_y"] - a["_y"] < need - 1e-9:
                bad.append((d, a["_lines"][0][:18], b["_lines"][0][:18],
                            round(b["_y"] - a["_y"], 3), round(need, 3)))
    return bad


# ----------------------------------------------------------------- 2. 绘制
def render(show_year, out_png, dpi=200):
    nodes, xleft, colw, ymin, ymax = build(show_year)

    content_w = xleft[-1] + colw[-1]
    content_h = ymax - ymin
    fw = MARGIN_L + content_w + MARGIN_R
    fh = TITLE_ZONE + content_h + MARGIN_B

    def SX(x):
        return MARGIN_L + x

    def SY(y):
        # 原始 y 越小越靠上；换算到 matplotlib 的「向上为正」坐标
        return fh - MARGIN_B - (y - ymin)

    fig = plt.figure(figsize=(fw, fh))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, fw)
    ax.set_ylim(0, fh)
    ax.axis("off")

    # ---- 顶部标题
    ax.text(MARGIN_L + 0.05, fh - 0.60, TITLE,
            fontproperties=FontProperties(fname=FONT_BOLD, size=19),
            color="#1B3A57", va="center", ha="left")
    ax.text(MARGIN_L + 0.07, fh - 1.02, SUBTITLE,
            fontproperties=FontProperties(fname=FONT_REG, size=10.5),
            color="#7A8A99", va="center", ha="left")

    # ---- 大分支底纹区
    for i, style in enumerate(BRANCH_STYLES):
        sub = [n for n in nodes if n["_bidx"] == i]
        if not sub:
            continue
        x0 = SX(xleft[1]) - 0.28
        x1 = SX(xleft[-1] + colw[-1]) + 0.20
        sy0 = SY(max(n["_y"] + n["_h"] / 2 for n in sub)) - 0.13
        sy1 = SY(min(n["_y"] - n["_h"] / 2 for n in sub)) + 0.13
        ax.add_patch(FancyBboxPatch(
            (x0, sy0), x1 - x0, sy1 - sy0,
            boxstyle="round,pad=0,rounding_size=0.22",
            facecolor=style["fill"], edgecolor="none", zorder=1))

    # ---- 连线（压在框底下）
    for n in nodes:
        p = n["_parent"]
        if p is None:
            continue
        c = BRANCH_STYLES[n["_bidx"]]["edge"]
        x1, y1 = SX(p["_x"] + p["_w"]), SY(p["_y"])
        x2, y2 = SX(n["_x"]), SY(n["_y"])
        mx = x1 + (x2 - x1) * 0.52
        ax.add_patch(PathPatch(
            Path([(x1, y1), (mx, y1), (mx, y2), (x2, y2)],
                 [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4]),
            facecolor="none", edgecolor=c,
            lw=1.05 if n["_depth"] == 1 else 0.75,
            linestyle=(0, (3.2, 2.2)), alpha=0.85, zorder=2, capstyle="round"))

    # ---- 节点框 + 文字
    cache = {}
    drawn = []
    for n in nodes:
        d = n["_depth"]
        st = BRANCH_STYLES[n["_bidx"]] if n["_bidx"] >= 0 else None
        if d == 0:
            fc, ec, tc, lw, bold = "#1B3A57", "#1B3A57", "#FFFFFF", 0.0, True
        elif d == 1:
            fc, ec, tc, lw, bold = st["edge"], st["edge"], "#FFFFFF", 0.0, True
        elif d == 2:
            fc, ec, tc, lw, bold = st["fill"], st["edge"], "#16324A", 1.15, True
        else:
            fc, ec, tc, lw, bold = "#FFFFFF", lighten(st["edge"], 0.42), "#243B4A", 0.8, False

        bx = SX(n["_x"])
        by = SY(n["_y"]) - n["_h"] / 2.0
        ax.add_patch(FancyBboxPatch(
            (bx, by), n["_w"], n["_h"],
            boxstyle="round,pad=0,rounding_size=%.3f" % min(0.11, n["_h"] / 2.4),
            facecolor=fc, edgecolor=ec, linewidth=lw, zorder=3))

        key = (n["_fs"], bold)
        if key not in cache:
            cache[key] = FontProperties(fname=FONT_BOLD if bold else FONT_REG, size=n["_fs"])
        t = ax.text(bx + n["_w"] / 2.0, SY(n["_y"]), "\n".join(n["_lines"]),
                    fontproperties=cache[key], color=tc,
                    ha="center", va="center", linespacing=LINE_SPACING, zorder=4)
        drawn.append((n, bx, by, t))

    # ---- 渲染后自查：文字是否溢出所在框 / 是否超出画布
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    overflow = []
    for n, bx, by, t in drawn:
        tb = t.get_window_extent(rend)
        p0 = ax.transData.transform((bx, by))
        p1 = ax.transData.transform((bx + n["_w"], by + n["_h"]))
        l, r = min(p0[0], p1[0]), max(p0[0], p1[0])
        b, tp = min(p0[1], p1[1]), max(p0[1], p1[1])
        dx = max(l - tb.x0, tb.x1 - r)
        dy = max(b - tb.y0, tb.y1 - tp)
        if dx > 1.0 or dy > 1.0:      # 容差 1px
            overflow.append((n["_depth"], n["_lines"][0][:16], round(dx, 1), round(dy, 1)))

    fig.savefig(out_png, dpi=dpi, facecolor="white")
    plt.close(fig)

    bad = check_overlaps(nodes)
    root = next(n for n in nodes if n["_depth"] == 0)
    print("画布 %.2f x %.2f 英寸   比例 %.3f   %d x %d px"
          % (fw, fh, fw / fh, int(fw * dpi), int(fh * dpi)))
    print("节点数 %d（叶子 %d）" % (len(nodes), sum(1 for n in nodes if not n["children"])))
    print("根节点纵向位置：%.1f%%（50%% 为正中）"
          % (100.0 * (root["_y"] - ymin) / (ymax - ymin)))
    print("同列重叠冲突：%d 处" % len(bad))
    for b in bad[:8]:
        print("   depth%d  %s | %s  (实际 %.3f < 需要 %.3f)" % b)
    print("文字溢出框：%d 处" % len(overflow))
    for o in overflow[:15]:
        print("   depth%d  %-18s 横溢 %.1fpx 纵溢 %.1fpx" % o)
    print("-> %s" % out_png)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", action="store_true", help="显示真题年份（私用版）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args()
    out = a.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "第一章-绪论-思维导图%s.png" % ("-含真题年份" if a.year else ""))
    render(a.year, out, a.dpi)
