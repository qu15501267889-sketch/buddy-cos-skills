---
name: hello-cos
title: 你好cos
version: 3.0.0
summary: 真人 coser 写真后期七步管线，本机 Qwen-Image-2.1 出 2K 编辑版，交付止步 2K。
owner: 🐭🐭
platforms: [windows]
---

# 你好cos · Skill Card

## 干什么

把用户「这张 cos 图我要改成 XX」的想法，变成 Qwen-Image-2.1 吃得进去的四段纯文本提示词，丢进本机 ComfyUI 跑出 2K 成品，落盘报清单。

## 什么时候触发

- 「你好cos」四字
- 给图 + 后期意图（修图 / 换场景 / 加特效 / 修脸塑形 / 保留原背景清杂物）
- 「帮我建工作流」→ 转活画布，走 duddy-comfyui
- 「这个效果怎么做 / 反推提示词」→ 反推模式

## 七步

启用 → 收路径 → 识图认定 → 定改法 → 定参数 → 生图 → 交付

每步有完成标准，**每步结束必须停下问**。

## 口径速查

| 项 | 口径 |
|---|---|
| 提示词结构 | **四段**纯文本（定位 / 保持不变 / 处理内容 / 一致性），**无负面段** |
| 质感 | 高P瓷感默认，禁写毛孔 |
| 特效 | 默认禁法阵/符文/光环，全稿连名字都不出现 |
| 性感向 | 不默认，当单指定，落点氛围级不减衣服 |
| 交付 | 止步 2K，不做任何超分 |
| 参数 | 全部用户拍板，不宣布默认值 |

## 依赖

- ComfyUI `http://127.0.0.1:8188`（Qwen-Image-2.1 GGUF Q8_0 / turbo）
- 显存 8G 必须串行 + 每张 `/free`
- 协作技能：`duddy-comfyui`（仅活画布任务）

## 权威源

| 写什么 | 看哪 |
|---|---|
| 修脸/头发/皮肤 | `references/portrait.md` |
| 特效 | `references/effects.md` |
| 换场景 | `references/scenes.md` |
| 保留原背景 | `references/bg-keep-original.md` |
| 口味 | `references/preferences.md` |
| 污染词 | `scripts/clean.py` |
