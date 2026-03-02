# 360 摄像头直播流解码器

## 概述

本工具可以解码 360 小水滴摄像头的加密 HEVC (H.265) 直播流，无需浏览器即可在本地播放或处理视频帧。

## 系统要求

- **Node.js** >= 14.x
- **ffplay** (来自 FFmpeg，用于播放)
- macOS / Linux / Windows

## 文件说明

```
tools/
├── libffmpeg.js          # 360 官方 WASM 解码器 (Emscripten 编译的 FFmpeg)
├── node_ffmpeg_loader.js # Node.js 环境适配器
├── decoder_service.js    # 完整解码服务
├── play_live.sh          # 一键播放脚本
└── test_decoder.js       # 测试脚本
```

## 快速开始

### 1. 一键播放

```bash
./tools/play_live.sh
```

### 1.1 自动刷新 playKey 后播放（推荐）

当 `STREAM_URL` / `PLAY_KEY` 过期导致 `socket hang up` / `ECONNRESET` 时，使用：

```bash
DEVICE_SN='YOUR_DEVICE_SN' \
Q_COOKIE='YOUR_Q_COOKIE_VALUE' \
T_COOKIE='YOUR_T_COOKIE_VALUE' \
bash tools/play_live_auto.sh
```

说明：
- `DEVICE_SN`：摄像头序列号
- `Q_COOKIE` / `T_COOKIE`：从浏览器登录态中取值（`my.jia.360.cn` 域下）
- 如果接口要求更多 cookie，可直接传完整头：
  `DEVICE_SN=... COOKIE_HEADER='k=v; k2=v2' bash tools/play_live_auto.sh`
- 脚本会先调用 `/app/play` 拉取最新 `relayStream` 和 `playKey`，再启动 `play_live.sh`

### 1.2 只输入账号密码自动登录并播放

先安装 Playwright：

```bash
cd /path/to/yolo_sheep
npm i -D playwright
npx playwright install chromium
```

运行（仅输入 SN/账号/密码）：

```bash
cd /path/to/yolo_sheep
bash tools/play_live_login.sh
```

说明：
- 脚本会自动填充账号密码并提交登录
- 若触发验证码，请在弹出的浏览器里手动完成
- 登录成功后会自动调用 `/app/play` 获取最新 `relayStream` 和 `playKey`
- 登录态会持久化在 `tools/.cache/360-browser-session/`
- 后续通常可直接复用登录态，无需再次输入账号密码

### 2. 手动运行

```bash
# 解码并用 ffplay 播放
node tools/decoder_service.js 2>/dev/null | \
  ffplay -f rawvideo -pixel_format yuv420p -video_size 1920x1080 -framerate 25 -i -
```

### 3. 保存为视频文件

```bash
# 解码并保存为 MP4 (录制 30 秒)
timeout 30 node tools/decoder_service.js 2>/dev/null | \
  ffmpeg -f rawvideo -pixel_format yuv420p -video_size 1920x1080 -framerate 25 -i - \
  -c:v libx264 -preset fast output.mp4
```

### 4. 保存原始 YUV 帧

```bash
# 保存 5 秒的 YUV 数据
timeout 5 node tools/decoder_service.js 2>/dev/null > output.yuv
```

## 配置

编辑 `decoder_service.js` 顶部的配置：

```javascript
// 直播流地址 (从 360 API 获取)
const STREAM_URL = "https://flv-live.jia.360.cn/live_jia_personal/...";

// 解密密钥 (从 360 API 获取)
const PLAY_KEY = "b8626411e2b666c44486d7081a2c04d71ebc0b5ad0be4b18aa042b94767cfd53";
```

## API 获取方法

### 获取流地址和密钥

```bash
curl -c cookies.txt -b cookies.txt \
  'https://my.jia.360.cn/app/play?sn=YOUR_DEVICE_SN&mode=0' \
  -H 'Cookie: YOUR_QHSSO_COOKIE'
```

返回示例：
```json
{
  "errorCode": 0,
  "relayStream": "_LC_RE_non_360170500071134..._BX",
  "playKey": "b8626411e2b666c44486d7081a2c04d71ebc0b5ad0be4b18aa042b94767cfd53"
}
```

构造流地址：
```
https://flv-live.jia.360.cn/live_jia_personal/{relayStream}.flv
```

## 输出格式

解码器输出 **YUV420P** 格式的原始视频帧：

| 参数 | 值 |
|------|-----|
| 格式 | YUV420P (I420) |
| 分辨率 | 1920×1080 |
| 帧率 | ~25 fps |
| 每帧大小 | 3,110,400 bytes |

## 技术原理

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   360 CDN       │────▶│  decoder_service │────▶│    ffplay       │
│ (加密 FLV/HEVC) │     │  (Node.js+WASM)  │     │ (YUV420P 播放)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │ libffmpeg.js │
                        │ (360 解码器) │
                        └──────────────┘
```

1. **获取流** - 从 360 CDN 获取加密的 FLV 流
2. **送入解码器** - 通过 `_sendData()` 送入 WASM 解码器
3. **解密+解码** - libffmpeg.js 使用 playKey 解密并解码 HEVC
4. **回调输出** - 视频帧通过回调函数输出 YUV 数据
5. **管道播放** - YUV 数据通过 stdout 管道到 ffplay

## 常见问题

### Q: 画面卡顿
A: 可能是网络延迟，或 CPU 解码速度不够。尝试降低分辨率或使用更快的机器。

### Q: 打开解码器返回 8
A: 确保在打开解码器前已经发送了足够的初始数据（至少 512KB）。

### Q: playKey 过期
A: playKey 有时效性，需要重新调用 API 获取新的 key。

### Q: 没有声音
A: 当前版本只输出视频，音频被忽略。如需音频，需要修改代码处理 PCM 回调。

## 与 YOLO 集成

输出的 YUV 帧可以用 Python 读取并转换为 NumPy 数组：

```python
import subprocess
import numpy as np

# 启动解码器
proc = subprocess.Popen(
    ['node', 'tools/decoder_service.js'],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL
)

# 读取帧
width, height = 1920, 1080
frame_size = width * height * 3 // 2  # YUV420P

while True:
    raw = proc.stdout.read(frame_size)
    if len(raw) < frame_size:
        break
    
    # 转换为 NumPy
    yuv = np.frombuffer(raw, dtype=np.uint8)
    y = yuv[:width*height].reshape(height, width)
    u = yuv[width*height:width*height*5//4].reshape(height//2, width//2)
    v = yuv[width*height*5//4:].reshape(height//2, width//2)
    
    # TODO: 转 RGB 后送入 YOLO
```

## 许可证

仅供学习研究使用。360 相关代码版权归 360 公司所有。
