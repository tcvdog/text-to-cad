# Text-to-CAD 打印工作流

**从命令行创建 3D 模型 → 网页预览 → Bambu 打印机**

> 作者：tcvdog | 打印机：Bambu Lab X2D | 打印机 IP：192.168.3.29

---

## 一、工具链总览

```
┌─────────────────────────────────────────────────────┐
│  ① CAD 建模 (build123d Python)    →  .step / .stl  │
│  ② 生成预览 (ocpsvg / CAD Viewer)  →  .glb / .png  │
│  ③ 切片 (OrcaSlicer CLI)          →  .gcode        │
│  ④ 打包 (Bambu 项目)              →  .gcode.3mf    │
│  ⑤ 局域网打印 (FTPS + MQTT)       →  Bambu X2D     │
└─────────────────────────────────────────────────────┘
```

---

## 二、使用的工具和依赖

### 2.1 核心工具

| 工具 | 版本 | 用途 | 安装方式 |
|------|------|------|----------|
| **Python 3.12** | 3.12.3 | 运行所有建模和工具脚本 | 系统自带 |
| **build123d** | 0.10.0 | Python CAD 库，参数化建模 | `pip install build123d` |
| **cadquery-ocp** | 7.8.1 | build123d 底层 OpenCASCADE 内核 | build123d 依赖自动安装 |
| **OrcaSlicer** | — | 将 STL 切片为 G-code | AppImage |
| **Bambu Studio** | 02.07.01.62 | Bambu 官方切片/管理工具 | AppImage |
| **Node.js** | 18.19.1 | CAD Viewer 网页预览服务器 | 系统安装 |
| **CAD Viewer** | — | 3D 模型网页查看器 | npm 项目 (text-to-cad 配套) |

### 2.2 Python 依赖

```
build123d             0.10.0     CAD 参数化建模
cadquery-ocp          7.8.1      OpenCASCADE 内核
numpy                 2.4.6      数值计算
ocpsvg                0.5.0      SVG 导出
cadpy                 0.2.1      CAD 工具脚本套件 (位于 .hermes/skills/cad/scripts/)
```

所有 Hermes 技能脚本位于：
- `~/.hermes/skills/cad/scripts/` — CAD 建模、切片、预览
- `~/.hermes/skills/gcode/scripts/` — G-code 生成
- `~/.hermes/skills/bambu-labs/scripts/` — Bambu 局域网打印

### 2.3 其他依赖

| 依赖 | 用途 |
|------|------|
| libfuse2 | AppImage 挂载（Ubuntu 24.04 需手动安装） |
| libavcodec.so.61 | Bambu Studio 运行库（AppImage 内自带） |
| FTPS (端口 990) | Bambu 打印机文件上传 |
| MQTT (端口 8883) | Bambu 打印机指令下发 |

### 2.4 打印机配置

文件：`bambu-printers.json`

```json
{
  "printers": {
    "x2d": {
      "host": "192.168.3.29",
      "access_code": "e1a4442f",
      "model": "x2d",
      "serial": "20P6BJ640901645"
    }
  }
}
```

切片配置文件：`x2d_pla_profile.json`

---

## 三、文件格式流转

```
Python 源码 (.py)
    │
    ▼ build123d gen_step()
STEP (.step) ────────── 主 CAD 格式，可编辑、可测量
    │
    ├──▶ GLB (.step.glb) ── CAD Viewer 网页预览
    │
    ├──▶ STL (.stl) ────── 三角网格，供切片使用
    │
    └──▶ PNG (.png) ────── 截图（Hermes 自动生成）
            │
            ▼ OrcaSlicer
        G-code (.gcode) ── 打印机指令
            │
            ▼ bambox 打包
        .gcode.3mf ─────── Bambu 项目文件
            │
            ▼ FTPS + MQTT
        Bambu X2D 打印
```

---

## 四、完整工作流（CLI 到打印）

### 阶段 1：创建 3D 模型

写一个 Python 脚本，用 build123d 定义几何体：

```python
# my_part.py
from build123d import *

def gen_step():
    with BuildPart() as p:
        Box(80, 50, 6)
        fillet(p.edges(), radius=3)
    return p.part
```

生成 STEP 文件：

```bash
python ~/.hermes/skills/cad/scripts/step my_part.py
```

输出：
- `my_part.step` — 主 CAD 文件
- `.my_part.step.glb` — CAD Viewer 预览文件

### 阶段 2：在 CAD Viewer 中预览

启动 CAD Viewer 网页服务器：

```bash
# 启动预览服务器（端口自动分配）
npm --prefix ~/.hermes/skills/cad-viewer/scripts/viewer run agent:start \
  -- --host 127.0.0.1 --shutdown-after 12h
```

在浏览器打开：
```
http://127.0.0.1:<端口>/?dir=/home/tcvdog/桌面/text%20to%20cad&file=my_part.step
```

可预览的文件类型：`.step`, `.stl`, `.3mf`, `.gcode`, `.glb`, `.dxf`

### 阶段 3：切片为 G-code

使用 OrcaSlicer 将 STL 转为打印机指令：

```bash
python ~/.hermes/skills/gcode/scripts/gcode_tool.py slice \
  --input my_part.stl \
  --output /tmp/my_part.gcode \
  --profile x2d_pla_profile.json \
  --backend orcaslicer \
  --execute
```

验证 G-code：

```bash
python ~/.hermes/skills/gcode/scripts/gcode_tool.py validate \
  --gcode /tmp/my_part.gcode \
  --profile x2d_pla_profile.json
```

### 阶段 4：打包 Bambu 项目

```bash
python ~/.hermes/skills/bambu-labs/scripts/bambu_lan_print.py send \
  --printer x2d \
  --gcode /tmp/my_part.gcode \
  --handoff bambox-project \
  --action upload-only
```

### 阶段 5：打印到 Bambu X2D

先检查打印机状态：

```bash
python ~/.hermes/skills/bambu-labs/scripts/bambu_lan_print.py status \
  --printer x2d \
  --push-all \
  --wait-seconds 10
```

确认无误后发送打印任务：

```bash
python ~/.hermes/skills/bambu-labs/scripts/bambu_lan_print.py send \
  --printer x2d \
  --gcode /tmp/my_part.gcode \
  --handoff bambox-project \
  --action upload-start \
  --execute \
  --confirm-start-print
```

取消正在打印的任务：

```bash
python ~/.hermes/skills/bambu-labs/scripts/bambu_lan_print.py cancel \
  --printer x2d \
  --execute \
  --confirm-cancel-print
```

---

## 五、各环节对应文件

### 5.1 CAD 建模脚本

| 文件名 | 模型 | 说明 |
|--------|------|------|
| `gear_31t.py` | 31齿齿轮 | build123d 齿形参数示例 |
| `cad_probe.py` | 探针模型 | 基础零件验证 |
| `pla_teaching_dip_pen.py` | 蘸水笔 v1 | 教学用 3D 打印笔 |
| `pla_fountain_nib_teaching_pen.py` | 钢笔尖 v1 | 曲线钢笔尖练习 |
| `pla_fountain_nib_curved_fine_pen.py` | 钢笔尖 v2 | 优化曲线 |
| `pla_fountain_nib_curved_thin_1mm_body10mm_pen.py` | 钢笔尖 v3 | 1mm 笔尖，10mm 杆 |
| `pla_fountain_nib_curved_thin_1mm_body10mm_pen_v2.py` | 钢笔尖 v4 | 平滑过渡版本 |

### 5.2 辅助脚本

| 文件名 | 用途 |
|--------|------|
| `inspect_stl_mesh.py` | 检查 STL 网格质量 |
| `check_stl_freecad.py` | FreeCAD 格式检查 |
| `engrave_bottom_text_freecad.py` | STL 底部刻字 |
| `engrave_bottom_text_reversed_freecad.py` | STL 底部反向刻字 |

### 5.3 静态配置文件

| 文件 | 用途 |
|------|------|
| `bambu-printers.json` | 打印机连接信息（IP、密码、序列号） |
| `x2d_pla_profile.json` | X2D 打印机 PLA 切片参数 |
| `result.json` | 切片结果报告 |

### 5.4 输出文件类型

| 扩展名 | 生成阶段 | 说明 |
|--------|----------|------|
| `.step` | CAD 建模 | 主 CAD 格式（可编辑、可测量） |
| `.stl` | CAD 建模 | 三角网格（供切片用） |
| `.glb` | CAD 建模 | Web 预览用 3D 格式 |
| `.png` | CAD 建模 | 截图预览 |
| `.gcode` | 切片 | 打印机指令 |
| `.3mf` | 切片/打包 | Bambu 项目文件 |
| `.gcode.3mf` | 打包 | Bambu 可打印项目 |

---

## 六、技能文件结构

所有流程由 Hermes Agent 技能驱动，位于：

```
~/.hermes/skills/
├── cad/             CAD 建模（build123d → STEP）
│   ├── SKILL.md     技能主文档
│   ├── scripts/     工具脚本
│   │   ├── step      STEP 生成器
│   │   ├── snapshot  屏幕截图
│   │   ├── inspect   几何检查
│   │   └── dxf       DXF 导出
│   └── references/  参考文档
├── cad-viewer/      网页 3D 预览
│   ├── SKILL.md
│   └── scripts/viewer/  Node.js 预览服务器
├── gcode/           STL → G-code 切片
│   ├── SKILL.md
│   └── scripts/gcode_tool.py
└── bambu-labs/      Bambu 局域网打印
    ├── SKILL.md
    └── scripts/bambu_lan_print.py
```

---

## 七、常见问题

### Q: Bambu Studio 打不开？
原因 1：缺少 libfuse2
```bash
sudo apt install libfuse2
```
原因 2：缺少 libavcodec.so.61
→ 用包装脚本启动：`~/Applications/BambuStudio/start.sh`

### Q: OrcaSlicer 找不到？
确认 AppImage 已安装并在 PATH 中，或运行 `discover` 命令：
```bash
python ~/.hermes/skills/gcode/scripts/gcode_tool.py discover
```

### Q: 打印机连接不上？
- 确认打印机和电脑在同一局域网
- 在打印机触摸屏打开 **LAN Only** 和 **Developer Mode**
- 重启打印机后重试
- 检查 `bambu-printers.json` 中的 IP 和 access_code

### Q: 打印任务发送后没反应？
- 用 `status` 命令检查打印机状态
- 检查 SD 卡是否正常
- 清除错误：`bambu_lan_print.py clear-error --printer x2d --execute`
- 重启打印机后重试
