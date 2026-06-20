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

## 五、3D 提示词工程（Prompt Engineering for 3D）

把自然语言描述转化为可打印的 3D 模型，核心是将"我要什么"翻译成"用什么几何体、多大、在哪"。

### 5.1 提示词金字塔（从模糊到精确）

```
自然语言描述（自然语言）    ← 你想要什么
    │
    ▼
CAD Brief（建模简报）        ← 参数、特征、约束
    │
    ▼
build123d 源码               ← 几何体、布尔运算、标签
    │
    ▼
STEP / STL                   ← 可打印的网格
```

### 5.2 自然语言 CAD Brief 模式（本项目的核心方法论）

这是 Hermes CAD skill 中使用的结构化提示模式，将口语描述转化为可执行的建模简报：

**模板结构：**

```
CAD brief:
- Model: <零件或装配体名称>
- Output: STEP 为主；可选 STL/GLB 为副
- Units: <毫米或英寸>
- Coordinate convention: <原点位置、基准面、拉伸方向>
- Overall dimensions: <长/宽/高或等效尺寸>
- Functional features: <孔、槽、筋、凸台、腔体、文字标注等>
- Positioning/mating: <配合面、基准点、子零件位置、对齐规则>
- Validation targets: <包围盒、实体数量、标签、测量值>
- Assumptions: <未明确但可合理推断的参数>
```

**本项目示例**（见 `pla_fountain_nib_curved_thin_1mm_body10mm_pen.py`）：

```
CAD brief:
- Model: curved fountain-nib teaching pen
- 钢笔式教学笔，总长120mm
- 笔杆 100mm × 10mm宽 × 3.2mm厚
- 笔尖 20mm，从 3.2mm 平滑过渡到 1.0mm
- 笔尖前端开 0.2mm 细缝（仿钢笔尖结构）
- 笔尖加呼吸孔 1.0mm
- 笔杆尾部倒圆角 R5
- Output: STEP + STL + GLB
```

### 5.3 经典提示词案例（行业通用模式）

#### 模式 A：尺寸优先法（最适合结构件）

> "做一个 120mm × 80mm × 6mm 的安装板，四角倒圆角 R5，四角各一个 φ4.5 通孔，离边 10mm"

→ 直接对应 Box + fillet + Hole，是 build123d 最直接的映射。

#### 模式 B：特征堆叠法（最适合复杂零件）

> "以一个 80×50×3mm 的底板开始，在中心加一个 10mm 高的圆柱凸台，凸台中间打一个 φ6 通孔，
> 底板四角各开一个 φ3.5 安装孔，底面挖一个 60×30×1.5mm 的凹槽"

→ 多个布尔运算堆叠：Box → add Cylinder → subtract Cylinder → subtract 4x Cylinder → subtract Box

#### 模式 C：参考对称法（最适合对称件）

> "一个左右对称的支架，总宽 100mm，总高 80mm，壁厚 3mm，底部有 4 个 φ4.5 安装孔呈 60×40mm 分布"

→ 可先做一半再 mirror，或直接用对称约束

#### 模式 D：扫掠/放样法（最适合自由曲面/流线型）

> "一个从 φ20 圆管逐渐过渡到 30×10mm 扁管的接头，长度 50mm，壁厚 2mm"

→ 用 `make_face` + `loft` 或 `sweep`

#### 模式 E：装配体法（最适合多零件）

> "一个两件式外壳：底座 120×80×35mm 中空壁厚 3mm，顶盖是平板且通过 4 个 M3 螺丝柱与底座连接，
> 螺丝柱位于底座四角离边 8mm"

→ 先分别建模 base + lid，再用 Joint 或显式 Location 定位

### 5.4 经典商业文本到 3D 工具提示示例

| 工具 | 模型类型 | 提示词风格 | 经典案例 |
|------|---------|-----------|---------|
| **Meshy** | 三角网格 | 纯文本描述 + 风格关键词 | "A vintage brass compass, steampunk style, intricate details" |
| **Luma AI Genie** | NeRF / 网格 | 简短物体描述 | "A ceramic teapot with blue floral pattern" |
| **Rodin (Deemos)** | 高精度网格 | 文本 + 法线贴图参考 | "A stylized wooden carving of a dragon, PBR materials" |
| **Stable Zero123** | 多视角生成 | 单张图 + 文本转多视角 | 输入一张椅子照片，生成各角度视图 |
| **Point-E / Shap-E** | 点云/隐式 | 短描述 | "A 3D model of a chair that looks like an avocado" |
| **Spline AI** | 参数化几何 | 自然语言 | "Create a rounded cylinder with 24 facets, height 5 units" |
| **Adobe Substance 3D** | 材质/PBR | 文本生成材质贴图 | "Weathered copper with green patina and scratches" |

### 5.5 本项目 vs 商业工具 —— 优劣对比

| 维度 | 本方案 (build123d) | 商业 AI 工具 (Meshy/Luma) |
|------|-------------------|--------------------------|
| **精确度** | 毫米级精确，无偏差 | 近似形状，尺寸不可控 |
| **可编辑性** | Python 源码，随时改参数 | 导出的网格难以参数化修改 |
| **工程适配** | 可定义孔距、公差、配合 | 只适合视觉原型 |
| **打印适配性** | 输出直接可切片 | 可能需要修复（watertight、法线） |
| **学习曲线** | 需 Python + CAD 概念 | 零门槛，打字即可 |
| **最佳场景** | 功能件、结构件、配合件 | 概念设计、艺术模型、游戏资产 |
| **提示词方式** | 结构化 CAD Brief | 纯自然语言描述 |

### 5.6 本项目的提示词实战经验

从已有项目文件中总结的实用模式：

**模式 1：带过渡的曲面（钢笔尖 v4）**
```
"笔杆 100mm × 10mm × 3.2mm，笔尖 20mm 从 3.2mm 平滑过渡到 1.0mm"
```
→ 实现方式：多个截面分段 loft，每段逐步缩窄
→ 文件：`pla_fountain_nib_curved_thin_1mm_body10mm_pen_v2.py`

**模式 2：底部刻字（牛顿第一定律实验）**
```
"底部凹陷雕刻 + 文字反刻（模具用）"
```
→ 实现方式：FreeCAD 脚本布尔运算提取文字轮廓

**模式 3：齿轮参数化（gear_31t）**
```
"31齿齿轮，模数2，压力角20°，中心孔φ8"
```
→ 实现方式：渐开线曲线 + revolve + subtract
→ 文件：`gear_31t.py`

**模式 4：实用教学工具（蘸水笔系列）**
```
"PLA 材料教学用蘸水笔，笔尖可夹钢笔尖，带墨水导流槽"
```
→ 实现方式：多段 loft + 布尔减操作
→ 文件：`pla_teaching_dip_pen.py`

### 5.7 撰写 3D 提示词的实用建议

**DOS：**
- 先定**全局尺寸**（长宽高），再定**特征位置**（孔距、边距）
- 明确**对称性**（左右对称、圆周阵列）——可大幅减少提示词长度
- 说清楚**布尔操作**（"加一个圆柱" vs "挖一个孔"）
- 对壁厚敏感件（外壳、容器）先说明**壁厚**

**DON'TS：**
- 不要只说"做一个好看的中国风花瓶"——要给出高度、口径、壁厚
- 不要在同一个提示词里混入无法同时满足的约束
- 对 3D 打印件，避免：
  - 悬垂 >45° 没有支撑
  - 壁厚 <0.8mm（PLA）
  - 孔直径 <2mm（打印精度限制）

---

## 六、各环节对应文件

### 6.1 CAD 建模脚本

| 文件名 | 模型 | 说明 |
|--------|------|------|
| `gear_31t.py` | 31齿齿轮 | build123d 齿形参数示例 |
| `cad_probe.py` | 探针模型 | 基础零件验证 |
| `pla_teaching_dip_pen.py` | 蘸水笔 v1 | 教学用 3D 打印笔 |
| `pla_fountain_nib_teaching_pen.py` | 钢笔尖 v1 | 曲线钢笔尖练习 |
| `pla_fountain_nib_curved_fine_pen.py` | 钢笔尖 v2 | 优化曲线 |
| `pla_fountain_nib_curved_thin_1mm_body10mm_pen.py` | 钢笔尖 v3 | 1mm 笔尖，10mm 杆 |
| `pla_fountain_nib_curved_thin_1mm_body10mm_pen_v2.py` | 钢笔尖 v4 | 平滑过渡版本 |

### 6.2 辅助脚本

| 文件名 | 用途 |
|--------|------|
| `inspect_stl_mesh.py` | 检查 STL 网格质量 |
| `check_stl_freecad.py` | FreeCAD 格式检查 |
| `engrave_bottom_text_freecad.py` | STL 底部刻字 |
| `engrave_bottom_text_reversed_freecad.py` | STL 底部反向刻字 |

### 6.3 静态配置文件

| 文件 | 用途 |
|------|------|
| `bambu-printers.json` | 打印机连接信息（IP、密码、序列号） |
| `x2d_pla_profile.json` | X2D 打印机 PLA 切片参数 |
| `result.json` | 切片结果报告 |

### 6.4 输出文件类型

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

## 七、技能文件结构

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

## 八、常见问题

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
