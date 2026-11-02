# -*- coding: utf-8 -*-
r"""
COS 提示词污染词清洗
==============================================================================
铁律八（SKILL.md §1）：提示词里发现的污染词，**当轮就同步进本文件的词表**，
不许攒着。加词的方式就是直接编辑下面对应的列表——这是唯一权威词表。

用法：
  python clean.py check "提示词全文"
  python clean.py check -f jobs.json
  python clean.py words                  # 列出全部词表
  python clean.py words negative         # 只看某一类

退出码：0 = 干净，1 = 有污染。

⚠ 只报不改。--fix 仅对「抽象泛词」生效（整句保留，只删那个词），
   其余类别必须人工判断——自动删「不」字会把保真句一起废掉。
"""
import sys
import io
import json
import re

# ───────────────────────── 词表 ─────────────────────────
# 新增污染词：直接往对应列表里加，并在列表尾部注明来源与日期。

# 1. 质感污染词：高P口径下禁出现的措辞（2026-10-28 用户明令「毛孔都不要」）
QUALITY_BANNED = [
    "毛孔", "细腻起伏", "皮肤纹理", "皮肤细节", "皮肤颗粒感",
    "不磨成瓷娃娃", "保留皮肤瑕疵", "真实皮肤质感",
]

# 2. 抽象泛词：模型吃不进去的形容词堆砌（词飘源头）
ABSTRACT_WEAK = [
    "绝美", "惊艳", "质感拉满", "氛围感十足", "氛围感满满",
    "高级感爆棚", "唯美到极致", "电影级质感", "大师级作品",
    "顶级画质", "8K超清", "超高清", "极致细节", "完美无瑕的肌肤",
    "如同艺术品", "令人惊叹", "视觉盛宴", "极致唯美",
]

# 3. 默认禁用元素：全稿连名字都不许出现（2026-10-28 拍板，写了反而给落点）
ELEMENT_BANNED = [
    "法阵", "魔法阵", "符文", "光环阵列", "魔法环", "咒文",
]

# 4. 弱句式：会让物件消失或两个都画（改用存在性锚定，见 SKILL.md §4）
WEAK_PATTERN = [
    "替换成", "替换为", "换成", "改为", "改造成", "变成",
    "把.{0,12}变",
]

# 5. 绝对词：堆砌反而抽风（2026-10 拍板「词精简，勿绝对词」）
ABSOLUTE = [
    "绝不", "必须", "所有", "唯一", "完全", "绝对", "务必", "一定要",
]

# 6. 负词：cfg=1 下无效，且给模型落点（本技能不写负面段）
NEGATIVE = [
    "不要", "禁止", "严禁", "避免", "不准", "不能", "别让", "千万别",
    "不可以", "切勿",
]

# 白名单：这些标准短语本身含敏感词但必须保留（保真四件 / 穿着状态句 / 模板固定句）
# 检查前先把它们抠成占位符，对所有类别生效——否则「五官与参考图完全一致」会被绝对词误杀。
WHITELIST = [
    "形制完整连贯，不断裂不溶解不变形",
    "服装完整穿着，不脱衣、不减少任何衣物层",
    "不变成另一个人",
    "不做缩放、旋转、平移",
    "未提及的部分一律保持原样",
    "人物五官与参考图完全一致",
    "眼型/双眼皮/唇/鼻/下巴轮廓逐项复制",
]

CATEGORIES = {
    "quality":   ("质感污染词（高P口径禁用）", QUALITY_BANNED, False),
    "abstract":  ("抽象泛词（模型吃不进）", ABSTRACT_WEAK, True),
    "element":   ("默认禁用元素（连名字都不写）", ELEMENT_BANNED, False),
    "weak":      ("弱句式（物件会消失）", WEAK_PATTERN, False),
    "absolute":  ("绝对词（堆砌抽风）", ABSOLUTE, False),
    "negative":  ("负词（cfg=1 无效且给落点）", NEGATIVE, False),
}


def _mask_whitelist(text):
    """把白名单短语抠成占位符，避免误报标准句里的敏感字。"""
    masked = text
    for i, phrase in enumerate(WHITELIST):
        masked = masked.replace(phrase, "\u0000W%d\u0000" % i)
    return masked


def check(text):
    """返回 [(类别key, 类别名, 命中词)]。"""
    hits = []
    target = _mask_whitelist(text)
    for key, (label, words, _) in CATEGORIES.items():
        for w in words:
            if w.startswith("把") and ".{0,12}" in w:
                if re.search(w, target):
                    hits.append((key, label, w + "（句式）"))
            elif w in target:
                hits.append((key, label, w))
    return hits


def report(hits):
    if not hits:
        print("✓ 干净，未命中污染词")
        return 0
    print("✗ 命中 %d 处污染：" % len(hits))
    cur = None
    for key, label, w in hits:
        if label != cur:
            print("\n  [%s]" % label)
            cur = label
        print("    - %s" % w)
    return 1


def load_text(argv):
    if argv and argv[0] == "-f":
        if len(argv) < 2:
            sys.exit("用法: clean.py check -f <文件>")
        with io.open(argv[1], encoding="utf-8-sig") as f:
            raw = f.read()
        try:                                    # jobs.json → 逐条 prompt 拼起来查
            data = json.loads(raw)
            jobs = data.get("jobs", data) if isinstance(data, dict) else data
            if isinstance(jobs, list):
                return "\n".join(str(j.get("prompt", "")) for j in jobs)
        except Exception:
            pass
        return raw
    return " ".join(argv)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 0
    cmd = sys.argv[1]

    if cmd == "words":
        pick = sys.argv[2] if len(sys.argv) > 2 else None
        for key, (label, words, _) in CATEGORIES.items():
            if pick and pick != key:
                continue
            print("\n%s  (%s)" % (label, key))
            for w in words:
                print("  - %s" % w)
        return 0

    if cmd == "check":
        return report(check(load_text(sys.argv[2:])))

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
