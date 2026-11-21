<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md">日本語</a> &nbsp;·&nbsp;
  <a href="README.zh.md"><img src="docs/flags/cn.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.zh.md"><b>中文</b></a> &nbsp;·&nbsp;
  <a href="README.ru.md"><img src="docs/flags/ru.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ru.md">Русский</a>
</p>

# Pixtuoid para Orca

一个适用于 Windows 的 Orca 插件。它打开一个悬浮的像素风窗口，把你本机的 Orca 智能体、它们的 worker 和子智能体显示为角色，每个都标有提供方、角色和项目。你可以选择窗口显示什么：

- **官方办公室**（`oficina`，默认）：Ivan Wang 的 [Pixtuoid](https://github.com/pixtuoid/pixtuoid) v0.23.0，与发布版一致。
- **Dungeons & Agents**（`dungeon`）：[Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents)，Pixtuoid 的奇幻模组。办公室变成营地和地下城楼层，每个智能体都是一名冒险者，其职业表示它的角色；点击冒险者会在 Orca 中打开它的会话。

![演示工作区：两个编排者，带有 Codex、Antigravity 和 Claude Code 的 worker 以及一个 Explore 子智能体](docs/office-roles.png)

## 各模式的功能

| 功能 | 官方办公室 | Dungeons & Agents |
|---|---|---|
| 智能体、worker 和子智能体显示为角色，标有提供方、角色和项目 | 是 | 是 |
| 智能体需要你时的通知和状态栏计数 | 是 | 是 |
| Orca 命令面板中的命令；从 Orca 安装和更新 | 是 | 是 |
| 在 Orca 报告智能体变化时读取 Orca，而不是靠快速定时器 | 是 | 是 |
| 团队颜色 | 按项目 | 按队伍：一个编排者、它的 worker 及其子智能体 |
| 表示角色（companion、orchestrator、worker、subagent）的职业 | 否 | 是 |
| 工具显示为技能（`Spell (Bash)`、`Scry (Grep)` 等）；Orca CLI 调用显示为 `Sending (Orca)` | 否（显示为工具 `Orca`） | 是 |
| 点击智能体，或在 `Tab` 树中对它按 `Enter`，在 Orca 中打开它的会话 | 否 | 是 |

## 系统要求

- 支持 DirectX 12 的 Windows x64
- 带 `py` 启动器的 Python 3.11+（64 位）
- Orca 1.4.265 或更高版本，并至少安装一个受支持的智能体。比已验证版本更新的 Orca 会显示一次性提示，应能继续工作。
- Claude Code、Codex 或 Antigravity 来源需要 `PATH` 中有 `claude`、`codex` 或 `agy`

## 从 Orca 安装

1. 在 Orca 中打开 **Settings → Plugins**，选择 **From a Git URL…** 并输入 `https://github.com/icaceresc/pixtuoid-orca-windows`，或运行 `orca plugin install icaceresc/pixtuoid-orca-windows`。安装前，Orca 会显示插件请求的访问权限（见下文）。
2. 在命令面板中，运行 **Pixtuoid: Install or update the office app** 安装官方办公室，或运行 **Pixtuoid: Use Dungeons & Agents**。它会下载构建、校验其固定的 SHA-256，并连接 Orca 报告的智能体。
3. 运行 **Pixtuoid: Open office window**，或点击 Orca 状态栏中的 **Pixtuoid**。

| 命令 | 作用 |
|---|---|
| Pixtuoid: Open office window | 打开窗口；同一时间只运行一个 |
| Pixtuoid: Close office window | 关闭窗口并保留其大小和位置 |
| Pixtuoid: Install or update the office app | 安装或更新最近所选模式的构建 |
| Pixtuoid: Use the official Pixtuoid office | 切换到官方办公室 |
| Pixtuoid: Use Dungeons & Agents | 切换到 Dungeons & Agents |
| Pixtuoid: Remove downloaded app and local data | 删除应用、隔离的智能体配置和日志 |

| 插件请求的访问权限 | 用途 |
|---|---|
| `agent:read` | 得知智能体状态何时变化：办公室此时读取 Orca，通知和状态栏计数也随之更新 |
| `workspace:read` | 按文件夹找到被点击智能体的工作区 |
| `workspace:write` | 把该智能体的会话带到前台 |
| `notifications:show` | 在智能体需要你时提醒你 |

**更新。** 插件由 Orca 更新（**Settings → Plugins**，或 `orca plugin update icaceresc.pixtuoid-office`）。**Pixtuoid: Install or update the office app** 会把办公室应用更新到插件为其模式固定的构建，并在窗口原本打开时重新打开它。本仓库的每日工作流会查找 Pixtuoid 新的稳定版本，校验其 SHA-256，运行测试，并提出新的固定版本供审查；它从不自行合并。

## 显示内容

Orca 在这台机器上识别出的每个智能体对应一个角色。子级穿着团队的颜色，并随父级一起离开。按 `Tab` 查看智能体树。

![智能体树：每个编排者及其 worker 和子智能体、它们的工具和状态](docs/office-dashboard.png)

| 在 Orca 中 | 在办公室中的名称 |
|---|---|
| Orca 机器人自己的会话（其 Strategic Companion） | `cc·punky · companion` |
| 顶层智能体 | `cc·my-repo · agent` |
| 派发 worker 的智能体（包括 worker 本身） | `cc·my-repo · orchestrator` |
| 编排 worker（任意层级） | `cx·worker · my-repo` |
| 与父级提供方不同的 worker | `cx·claude worker · my-repo` |
| Orca 在会话中观察到的子智能体 | `cc·Explore subagent · my-repo` |
| Antigravity 智能体的 worker | `cx·worker of antigravity · my-repo` |
| 后台命令、监视器或工具调用 | 无角色 |

前缀是提供方（`cc` Claude Code、`cx` Codex、`oc` OpenCode、`ag` Antigravity），项目是 Orca 工作区的文件夹。桌牌只显示名称的前几个字符；将指针悬停在角色上或按 `Tab`，可查看完整名称、父级和当前工具。

| 提供方 | 作为智能体 | 作为 worker | 原生子智能体 |
|---|---|---|---|
| Claude Code | 是 | 是 | 是 |
| Codex | 是 (1.4.263) | 是 | 未验证 |
| OpenCode | 是 (1.4.263) | 是 (1.4.263) | 未验证 |
| Antigravity | 是 (1.4.263) | 是 | Orca 未报告 |

已在 Orca 1.4.265 和 1.4.266（注明处为 1.4.263）上实际验证。全部四个提供方还使用录制的 Orca 响应，针对真实的 Pixtuoid 做了检查。

## 操作

| 操作 | 输入 |
|---|---|
| 移动 | 拖动空白区域 |
| 调整大小 | 拖动右下角 |
| 缩放 | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| 智能体树 | `Tab` |
| 智能体的名称、父级、文件夹和工具 | 将指针悬停在其上 |
| 在 Orca 中打开智能体的会话（Dungeons & Agents） | 点击它，或在 `Tab` 树中对它按 `Enter` |
| 帮助 · 暂停 · 主题 | `?` · `P` · `T` |
| 关闭并保存大小和位置 | `Q`，或 **Pixtuoid: Close office window** |

## 可见状态

| Orca 状态 | 在办公室中 |
|---|---|
| `working` | 在办公桌前；Orca 报告的工具（如 `Bash`、`Edit`、`shell`）显示在显示器、提示框和底部统计中 |
| `waiting` / `blocked` | 请求权限（`!`），计为“需要你”；办公室打开时会有桌面通知，Orca 状态栏也会计数 |
| `done` / `idle` | 休息或闲逛 |
| 会话关闭、子智能体完成或取消 | 从门口离开；其子级先离开 |

## 限制

- **点击智能体**只在 Dungeons & Agents 中打开其会话。终端智能体会聚焦到它的窗格。Orca 聊天没有终端，因此会显示它的工作区：当一个工作区有多个聊天时（例如机器人的主目录），Orca 显示的是该处最后打开的那个，不一定是被点击的那个。子智能体会打开它所运行的会话。
- Pixtuoid 只会把子级关联到同一提供方的父级。其他提供方的 worker 位于父级之下，使用父级的前缀，其名称写明它自己的提供方（`cx·claude worker`）。在 Claude Code 树中，前缀也是 worker 自己的。
- Pixtuoid 无法在顶层 Antigravity 智能体下绘制子级：它的 worker 显示为名为 `worker of antigravity` 的独立同事。
- Pixtuoid 保留同事首次出现时的名称，因此之后才开始派发的智能体会先离开，再以 orchestrator 身份回来。角色不会被收回。
- Orca 只报告工具名称，不报告模型、推理强度或 token 用量，因此办公室不显示模型、推理强度或 token 计量。
- 使用插件时，Orca 一报告智能体变化，办公室就读取 Orca；否则在有智能体工作时每 6 秒读取一次，没有时每 30 秒一次，因此子智能体可能要等这么久才出现，非常短的工具也可能被漏掉。从克隆运行时，每 1.5 到 10 秒读取一次。
- 通知和状态栏计数跟随插件启动后 Orca 报告的状态变化。
- 只显示 Orca 自己观察到的子智能体。打开办公室时已经结束的智能体不会显示。
- 仅限本地 Orca 主机。远程 Orca 环境会被忽略。

## 隐私

- 办公室只从 `orca worktree ps`（以及作为后备的 `orca agent list`）读取 ID、父级链接、提供方、子智能体类型、状态、工具名称、工作区文件夹以及该工作区是否为机器人的主目录。它查看 shell 工具的命令，仅为判断其是否运行 Orca CLI；提示词、回复和工具输入从不转发或存储。
- 插件运行期间，会在内存中保存每个智能体的状态及其窗格、终端和工作区的 ID。通知显示 Orca 提供的会话标题，仅在本机上。
- 适配器唯一的网络访问是从 GitHub 下载固定的构建。
- 应用、隔离的智能体配置和日志都保存在 `%LOCALAPPDATA%\PixtuoidOrca`（从克隆运行时则在克隆中）。为了标明 worker 的提供方，办公室会在隔离配置中写入一行卡片（名称和文件夹），并在 worker 离开或办公室关闭时删除它。点击会在那里写入被点击会话的 ID，供插件读取。
- 不修改智能体和 Orca 的全局设置。

## 从克隆运行

插件是受支持的方式。若要开发适配器，或安装你自己的构建：

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py                     # 官方办公室；Dungeons & Agents 用 --modo dungeon
py -3 -m unittest -v test_oficina test_instalar
```

用 **`Abrir oficina.lnk`** 打开办公室，用 `Q` 或 `py -3 oficina.py --stop` 关闭。点击智能体需要插件。限制来源：`py -3 instalar.py --sources claude-code codex`。

**你自己的构建。** 在办公室关闭时，`py -3 instalar.py --modo dungeon --local C:\path\to\dungeons-and-agents\target\release` 会从本地构建安装 `pixtuoid.exe` 和 `pixtuoid-hook.exe`，以及在它们旁边或其仓库根目录找到的 `LICENSE`。`--url https://... --sha256 <64 位十六进制>` 安装与 Pixtuoid Windows zip 结构相同的 zip。`app/origen.json` 记录已安装的内容及其模式：之后的普通运行会保留你的构建并加以说明，`--pinned` 回到该模式的固定构建，`--modo` 切换模式。插件的命令在 `%LOCALAPPDATA%\PixtuoidOrca` 中做同样的事。

## 卸载

运行 **Pixtuoid: Remove downloaded app and local data**，然后在 **Settings → Plugins** 中卸载插件。克隆只需删除其文件夹。

## 致谢与许可证

- 本插件：[MIT 许可证](LICENSE)。
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid)，作者 Ivan Wang，MIT 许可证。在安装时下载，不再分发。
- [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents)，Pixtuoid 的模组，MIT 许可证。在安装时下载，不再分发。
- 旗帜图标：[lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3，[MIT 许可证](docs/flags/LICENSE)。
- Orca 是独立产品，不包含在内。这是一个独立的插件，不是 Pixtuoid 或 Orca 的官方项目。
