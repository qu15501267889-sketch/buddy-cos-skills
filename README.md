# 你好cos · COS 修图管线 v3.0

真人 coser 写真后期流水线技能。说「**你好cos**」四个字启用，直接问图片路径，走七步管线出 2K 编辑版。

本机 ComfyUI + Qwen-Image-2.1 执行，走 API 提交，不碰活画布。**交付止步 2K，不做超分。**

## 触发

- **「你好cos」** → 进七步管线，第 2 步问路径
- 「帮我建工作流」 → 派生活画布任务，走 `duddy-comfyui` 协作，不碰队列
- 给图 + 后期意图（修图 / 换场景 / 加特效 / 保留原背景清杂物）→ 直接进管线
- 「这个效果怎么做 / 反推提示词」 → 反推模式

## 七步管线

```
启用 → 收路径 → 识图认定 → 定改法 → 定参数 → 生图 → 交付
```

每步有完成标准，达标才进下一步。**每一步结束必须停下问，「继续」= 只推进一步。**

## 九条铁律（最高优先级）

| # | 铁律 |
|---|---|
| 一 | 每步必停，不挑步/跳步/合并步/替他拍板 |
| 二 | 全程禁调 memory 工具，记忆只走 `preferences.md` 与 SKILL.md |
| 三 | 提示词逐张全文过目，禁「同上 + 差异」省略式 |
| 四 | 模型/档位/步数/参数他拍板才跑，不宣布默认参数 |
| 五 | 方案讨论期不动手，等「动手/来吧/可以」 |
| 六 | 内容原封不动，不总结不省略 |
| 七 | 不删他已恢复的文件，删前先问 |
| 八 | 发现污染词当轮同步进 `scripts/clean.py` |
| 九 | 测试期他报缺点时不过度整活 |

## 目录

```
hello cos/
├── SKILL.md                    技能主体（九章 + 引用表 + Pitfalls + Checklist）
├── README.md
├── skill-card.md
├── references/
│   ├── portrait.md             修脸措辞（唯一权威源）
│   ├── effects.md              特效措辞库
│   ├── scenes.md               换场景三铁律 + 场景库
│   ├── bg-keep-original.md     保留原背景清杂物专项模板
│   ├── preferences.md          口味档案（跨会话记忆，读写规则见 SKILL.md §8）
│   ├── qwen21.md               Qwen2.1 规范 / 黑图根因 / 节点接法
│   ├── qwen21-prompt-obedience.md  服从性缺陷与修复（写词必读）
│   ├── template.json           字段结构示例（非措辞来源）
│   ├── teaching-and-transcript.md  教学式回答 + 聊天记录格式
│   ├── *-case-*.md             历史单实录（大乔/妲己/甘雨/云缨/少司缘）
│   ├── clawhub-origin/         原始版素材归档（JSON 信封那一套，未启用）
│   └── ...
├── scripts/
│   ├── cos_batch.py            批量执行（串行 + 每张释放显存）
│   ├── clean.py                污染词清洗词表
│   └── cos-preflight.py        输入预检
└── _legacy/                    本技能前身（clawhub cos-effect-prompt-main）的 README 归档
```

## 安装（Windows）

技能必须在 `~/.workbuddy/skills/` 下才会被加载。本目录是开发主目录，用目录符号链接挂进去：

```bat
mklink /D "%USERPROFILE%\.workbuddy\skills\hello-cos" "D:\github\wuddy\hello cos"
```

跟 `duddy-comfyui` 同一套做法：D 盘改，链接指过去，不用来回拷。

## 运行

```bat
REM 批量出图（路径和任务清单在脚本头部改）
D:\AI\ComfyUI_windows_portable\python_embeded\python.exe scripts\cos_batch.py edit

REM 污染词自检（返回 1 = 有污染）
python scripts\clean.py check -f cos_jobs.json
```

## 版本

- **v3.0.0**（2026-11-02）重新定制：九条流程铁律入正文、OC 与直报角色名纳入范围、活画布派生任务、反推模式、存在性锚定、丝袜逐腿锁定、美白排除区、涂鸦不遮脸、教学式回答与聊天记录格式、`bg-keep-original.md`、`clean.py` **新建**；默认档位 Q8_0 **20 步**（原 40）；模板维持四段不写负面段。
- 血脉：`clawhub.ai/aleaaaan/skills/cos-effect-prompt-main`（原始）→ `cos-retouch-pipeline` v2.5.0（中间版，已弃）→ 本仓。

## License

MIT
