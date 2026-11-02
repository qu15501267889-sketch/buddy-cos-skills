# 显存碎片化：症状、根因与调参（2026-11-02 实测）

> 4060Ti 8G 跑 Qwen-Image-2.1（模型总需求 16.5GB）的必修课。
> 批量处理时速度「一张比一张慢」，答案全在这份文件里。

## 一、症状：三个数字一起看

| 指标 | 健康 | 碎片化/offload | 死锁 |
|---|---|---|---|
| 单步耗时 | 20-30 秒 | 90-140 秒 | 不动 |
| **功耗** | **127-144 W** | **45-75 W** | <40% 上限 |
| 显存余量 | >1.5 GB | <300 MB 且**单调递减** | <100 MB |
| 显存利用率 | 高 | **1-4%（GPU 在等 PCIe）** | ~5% |

**功耗是最灵敏的指标。** 60W 意味着 GPU 七成时间在等数据搬运，不是在算图。

## 二、实测衰减曲线（2026-11-02，同一批图）

```
15:27  剩 563 MB   ← 第 1 张
16:22  剩 291 MB   ← 第 2 张
16:30  剩 172 MB
17:39  剩 137 MB
17:54  剩 110 MB   ← 第 3 张尾部
```

**单调递减，没有回升。** 这是碎片化的签名——不是「随机波动」，也不是「模型太大偶尔慢一下」。

## 三、根因：动态模型加载 + 分配器

ComfyUI 在显存不够时把模型拆层，按需换进换出：

```
loaded partially; 1245.74 MB usable, 1090.88 MB loaded, 6405.00 MB offloaded
```

**6.4GB 被踢到普通内存**，显存里只剩 1.09GB。每层大小不同，反复进出会在显存池里留下大小不一的空洞；跑到后面即使总空闲够，也找不到连续的大块，只能继续 offload → 越跑越慢。

### 为什么「固定工作流」不能解决

碎片来自**层加载模式**，不来自提交方式。常驻画布工作流和 API 提交，底层都是 `graphToPrompt + queuePrompt`，层照样按同样顺序进出，照样切碎。**工作流形态动不了这个变量。**

### 为什么「固定分辨率」也不是药

不同比例的图（4:3 / 9:16）在 `resolution=2048` 下长边固定，短边不同 → latent 尺寸不同 → 分配不同。但真正的祸根是「上一张残留没清」，不是尺寸本身在变。**清空比固定重要。**

## 四、三个启动参数（配套使用）

### `--disable-cuda-malloc`

- **作用**：把分配器从 `cudaMallocAsync` 换回 `native`
- **为什么必须**：PyTorch 的 `expandable_segments` **只认 native 分配器**。`cuda_malloc.py:102-112` 会在 `args.cuda_malloc` 为真时往 `PYTORCH_CUDA_ALLOC_CONF` 追加 `,backend:cudaMallocAsync`，导致前半截设置被静默忽略。
- **验证方法**：`/system_stats` 的 `devices[0].name` 末尾应是 `: native`，不是 `: cudaMallocAsync`
- **风险**：无

### `--disable-smart-memory`

- **作用**：每张执行完主动卸载模型，下一张从干净状态开始
- **为什么必须**：默认的 smart memory 会把模型囤在显存里「复用」，同时中间张量、临时缓冲也在囤。一张跑完留一堆大小不一的残留，下一张只能塞缝。
- **代价**：每张多 1-2 分钟重载模型（对 30 步任务占 ~3%）
- **风险**：无

### `--reserve-vram 0.1`

- **作用**：把 ComfyUI 自扣的 600MB 缓冲压到 100MB，多出 500MB 给模型
- **依据**：`model_management.py:877-884`，`EXTRA_RESERVED_VRAM = 600MB`（Windows 默认）；`minimum_inference_memory() = 0.8GB + EXTRA_RESERVED_VRAM`
- **风险**：留太少，系统图形界面可能卡顿，显存突然不足时可能崩。**不要设 0**，0.1 是下限。

### 配套：环境变量（用户级，永久）

```
HKCU\Environment
PYTORCH_CUDA_ALLOC_CONF = expandable_segments:True
```

设成用户级的好处：不管从哪启动（bat / 快捷方式 / 其他程序拉起），新进程都继承，不依赖启动脚本。

**注意**：`[Environment]::SetEnvironmentVariable(..., "User")` 只写注册表，当前 PowerShell 会话的 `$env:` 不会更新。如果要在本会话里 `Start-Process`，必须先显式 `$env:PYTORCH_CUDA_ALLOC_CONF = "..."` 再启动，否则子进程拿不到。

## 五、完整启动命令（Windows）

```bat
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
.\python_embeded\python.exe -s ComfyUI\main.py ^
  --windows-standalone-build ^
  --disable-cuda-malloc ^
  --disable-smart-memory ^
  --reserve-vram 0.1
```

脚本：`D:\AI\ComfyUI_windows_portable\start_comfyui_novram.bat`

**不要用** `restart_comfyui.cmd` / `start_comfyui_silent.cmd`——它们带 `--reserve-vram 1`（保留 1GB 给系统），在 8G 卡上等于自断一臂。

## 六、实测效果（2026-11-02）

| 任务 | 步数 | 单步 | 配置 | 在该进程里的顺序 |
|---|---|---|---|---|
| 第 1 张 | 30 | 64 秒 | cudaMallocAsync | 第 1 个 |
| 第 2 张 | 30 | 136 秒 | cudaMallocAsync | 第 2 个 |
| 8 步测试 | 8 | **22-32 秒**（前 5 步） | native + expandable | 第 1 个 |
| 第 3 张 | 30 | 98-107 秒 | native + expandable | 第 2 个 |

**结论**：
- `expandable_segments` + native 有效，第 2 张从 136 秒降到 98 秒（1.4x）
- 但**只能延缓不能根治**：同一个进程里第 1 个任务前 5 步能到 22 秒，第 6-7 步开始劣化，第 2 个任务起步就是 98 秒
- 加 `--disable-smart-memory` 后预期每张回到起点，**尚未实测验证**，首次验证后回填本表

## 七、诊断命令

```bash
# 功耗 + 显存余量（最灵敏）
nvidia-smi --query-gpu=power.draw,memory.used,memory.free,utilization.memory --format=csv,noheader

# 队列与在跑任务的参数
curl -s http://127.0.0.1:8188/queue

# 完成记录与真实耗时
curl -s "http://127.0.0.1:8188/history?max_items=5"

# 实时步数（WebSocket，只在 progress 变化时打印）
# 见 scripts/ 下的 ws 监控写法；socket 超时不算失败，约 2 分钟心跳并主动重连
```

**判读顺序**：先看功耗 → 再看步数是否推进 → 再看显存余量趋势。
步数推进 + 功耗低 = offload 慢跑，能出图；步数不动 + 功耗低 + 显存余量 <100MB = 死锁，重启。

## 八、绕不过去的物理天花板

8G 卡要装 16.5GB 的模型，上面全是「让碎片少一点」，不能变出显存。

**唯一治本的是减少外部占用**：

- 剪映、Chrome、ChatGPT、飞书、钉钉、Electron 类应用全都吃显存，8G 卡上合起来能占 2-3GB
- 本机有核显（Intel UHD 770）时，把这些应用在「Windows 图形设置」里强制指定到核显，独显就还给 ComfyUI
- 效果相当于 offload 量从 6.4GB 降到 4.5GB，碎片自然大减

**如果 8K 或高频批量是常驻需求，换 24G 卡是唯一解，不是技巧问题。**
