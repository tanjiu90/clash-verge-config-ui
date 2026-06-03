# Clash Verge 可视化增强配置编辑器

一个给 Clash Verge Rev 使用的本地网页工具，用来可视化编辑订阅的增强配置。适合不想手写 YAML、但又经常需要调整规则、代理组、链式代理节点的用户。

新手建议先看：[图文教程：从下载安装到保存生效](docs/图文教程.md)

## 它能做什么

- 可视化编辑 `代理组` 增强配置：前置、后置、删除。
- 可视化编辑 `代理节点` 增强配置：添加 SOCKS5、HTTP、Trojan、Vmess、Vless、Shadowsocks 等常见节点字段。
- 可视化编辑 `规则` 增强配置：例如 `DOMAIN`、`DOMAIN-SUFFIX`、`DOMAIN-KEYWORD` 等。
- 读取当前订阅里的代理组和节点，添加代理组成员时可以直接点击选择。
- 规则策略支持选择 `DIRECT`、`REJECT`、`PASS`、订阅代理组、订阅节点。
- 支持把项目从 `前置` 移到 `后置`，或从 `后置` 移到 `前置`。
- 每次保存前自动创建 `.bak-YYYYmmdd-HHMMSS` 备份。
- 只在本机运行，不上传订阅、节点、密钥或配置内容。
- 默认空闲 30 分钟后自动退出，避免长期后台占用。

## 重要说明

这个工具不是 Clash Verge Rev 官方插件，也不会修改 Clash Verge Rev 程序本体。它只是读取并修改 Clash Verge Rev 已经创建好的增强配置文件。

Clash Verge Rev 目前没有开放可以把这个编辑器嵌入内置界面的插件接口，所以本工具采用“本地网页编辑器”的方式运行。

## 适用环境

- Windows 10 或 Windows 11。
- 已安装 Clash Verge Rev。
- 已安装 Python 3.10 或更高版本。

安装 Python 时建议勾选：

```text
Add python.exe to PATH
```

## 第一次安装

### 方式一：下载 GitHub ZIP

1. 打开本仓库页面。
2. 点击 `Code`。
3. 点击 `Download ZIP`。
4. 解压到一个固定目录，例如：

```text
C:\Tools\clash-verge-config-ui
```

5. 在解压后的目录空白处按住 `Shift`，点击鼠标右键，选择 `在终端中打开` 或 `在 PowerShell 中打开`。
6. 运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

安装完成后，桌面会出现：

```text
Clash Verge Config UI
```

### 方式二：使用 Git

```powershell
git clone https://github.com/你的用户名/clash-verge-config-ui.git
cd clash-verge-config-ui
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

## 日常使用

1. 打开 Clash Verge Rev。
2. 确认你的订阅已经正常导入。
3. 如果某个订阅从来没有创建过增强配置，请先在 Clash Verge Rev 的订阅页面右键该订阅，分别打开一次：

```text
编辑代理组
编辑代理节点
编辑规则
```

这样 Clash Verge Rev 会生成对应的增强配置文件。

4. 双击桌面的：

```text
Clash Verge Config UI
```

5. 浏览器会打开：

```text
http://127.0.0.1:8787
```

6. 在左侧选择订阅。
7. 在顶部选择 `代理组`、`代理节点` 或 `规则`。
8. 选择 `前置`、`后置` 或 `删除`。
9. 点击 `添加前置`、`添加后置` 或选择已有项目进行修改。
10. 修改完成后点击 `保存`。
11. 回到 Clash Verge Rev，重新应用对应订阅或切换一次 Profile，让配置生效。

## 常见使用场景

### 添加一条通用直连规则

1. 进入 `规则`。
2. 选择 `前置`。
3. 点击 `添加前置`。
4. 类型选择 `DOMAIN-SUFFIX`。
5. 内容填写：

```text
example.com
```

6. 策略选择：

```text
DIRECT
```

7. 点击 `保存`。

保存后的效果类似：

```yaml
prepend:
  - DOMAIN-SUFFIX,example.com,DIRECT
append: []
delete: []
```

### 添加家宽链式代理节点

如果你的家宽 SOCKS5 节点必须通过境外节点访问，可以在 `代理节点` 中添加节点，并把 `dialer-proxy` 设置为你的境外前置代理组，例如：

```text
节点选择
```

最终链路效果是：

```text
电脑 -> 节点选择 -> 家宽 SOCKS5 -> 目标网站
```

### 给代理组添加节点或其它代理组

1. 进入 `代理组`。
2. 新建或选择一个代理组。
3. 在右侧候选区点击需要加入的节点或代理组。
4. 已加入的项目会显示为已添加状态。
5. 再次点击可以移除。
6. 点击 `保存`。

## 启动和停止

正常启动：

```powershell
.\start-ui.ps1
```

或双击：

```text
start-ui.bat
```

手动停止：

```powershell
.\stop-ui.ps1
```

默认端口是 `8787`。如果端口被占用，可以临时换一个端口：

```powershell
$env:CLASH_VERGE_CONFIG_UI_PORT=8788
.\start-ui.ps1
```

默认空闲 30 分钟后自动退出。如果想改成 10 分钟：

```powershell
$env:CLASH_UI_IDLE_TIMEOUT=600
.\start-ui.ps1
```

## Clash Verge 配置目录

默认读取：

```text
%APPDATA%\io.github.clash-verge-rev.clash-verge-rev
```

如果你的 Clash Verge Rev 配置目录不在默认位置，可以指定：

```powershell
$env:CLASH_VERGE_APP_DIR="D:\Your\ClashVergeData"
.\start-ui.ps1
```

## 能不能从 Clash Verge 的网页界面启动

Clash Verge 的 `设置 -> 网页界面` 只能保存和打开 URL，不能启动本地程序。

你可以添加：

```text
http://127.0.0.1:8787
```

但它只能在本工具已经启动时打开页面，不能负责启动本工具。

## 常见问题

### 打开后提示找不到 Clash Verge 配置

先确认 Clash Verge Rev 已经安装并运行过一次。如果使用的是便携版或自定义数据目录，请使用 `CLASH_VERGE_APP_DIR` 指定配置目录。

### 某个订阅显示没有绑定增强文件

在 Clash Verge Rev 的订阅页面右键该订阅，先打开一次 `编辑代理组`、`编辑代理节点` 或 `编辑规则`。Clash Verge Rev 创建文件后，本工具才能编辑。

### 保存后没有生效

保存后需要回到 Clash Verge Rev，重新应用对应订阅或切换一次 Profile。增强配置不是浏览器保存后立即注入内核的。

### 订阅更新后会不会丢失

本工具编辑的是 Clash Verge Rev 的增强配置文件，不是订阅原文。正常情况下订阅更新不会覆盖增强配置。

### 会不会泄露节点信息

不会。工具只监听本机地址 `127.0.0.1`，数据读取和保存都在本机完成。

## 项目文件说明

```text
app.py                 主程序，本地网页服务和可视化界面
requirements.txt       Python 依赖
start-ui.ps1           Windows 启动脚本
start-ui.bat           双击启动入口
stop-ui.ps1            停止本工具
install-windows.ps1    安装依赖并创建桌面快捷方式
README.md              使用说明
LICENSE                开源许可证
```

## 上传到 GitHub

如果你是项目维护者，可以这样上传：

```powershell
git init
git add .
git commit -m "Initial release"
git branch -M main
git remote add origin https://github.com/你的用户名/clash-verge-config-ui.git
git push -u origin main
```

如果没有命令行经验，也可以打开 GitHub Desktop，选择 `Add local repository`，选中本项目目录，然后点击 `Publish repository`。
