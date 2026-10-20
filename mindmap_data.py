# -*- coding: utf-8 -*-
"""Demo data: a remote-collaboration capability model.

Replace TREE / BRANCH_STYLES / TITLE / SUBTITLE with your own content,
then run:  python render_mindmap.py --out docs/demo.png
"""

TITLE = "远程协作能力模型"
SUBTITLE = "沟通 · 交付 · 工具 · 风险"


def N(text, children=None, year=None, tag=None):
    return {
        "text": text,
        "children": children or [],
        "year": year,
        "tag": tag,
    }


BRANCH_STYLES = [
    {"name": "沟通", "edge": "#1F4E79", "fill": "#EAF1F7"},
    {"name": "交付", "edge": "#2E6DA4", "fill": "#EDF4FA"},
    {"name": "工具", "edge": "#4A89C4", "fill": "#F0F6FB"},
    {"name": "风险", "edge": "#6BA3D6", "fill": "#F3F8FC"},
]


TREE = N("远程协作能力模型", [
    N("沟通", [
        N("异步文档", [
            N("需求先落文档\n再开会讨论"),
            N("结论、决定与变更\n都留下文字记录"),
        ]),
        N("会议与纪要", [
            N("会前发议程\n会后 24h 内出纪要"),
        ]),
        N("边界确认", [
            N("输入、输出、验收标准\n开工前对齐"),
            N("不确定的地方\n先问，不猜"),
        ]),
    ]),
    N("交付", [
        N("里程碑拆分", [
            N("大任务拆成\n可验收的小节点"),
            N("每个节点\n可独立演示"),
        ]),
        N("小样确认", [
            N("关键节点先给样例\n避免方向跑偏"),
        ]),
        N("验收与售后", [
            N("附使用说明\n与样例输出"),
            N("约定范围内\n负责修改"),
        ]),
    ]),
    N("工具", [
        N("Python 自动化", [
            N("重复劳动\n脚本化"),
            N("数据采集、清洗\n与批处理"),
        ]),
        N("文档流水线", [
            N("Markdown → Word\n批量生成"),
            N("生成后实际渲染\n逐页检查"),
        ]),
        N("监控与日志", [
            N("长任务有进度\n异常有告警"),
        ]),
    ]),
    N("风险", [
        N("时区差异", [
            N("约定重叠工作时段\n与响应时限"),
        ]),
        N("网络与设备", [
            N("关键任务准备\n离线/备用方案"),
        ]),
        N("权限管理", [
            N("最小权限原则\n敏感操作需确认"),
            N("密钥不进代码库\n不进聊天记录"),
        ]),
    ]),
])
