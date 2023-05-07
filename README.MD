<!-- markdownlint-disable MD033 MD036 MD041 -->

<p align="center">
  <a href="https://v2.nonebot.dev/"><img src="https://v2.nonebot.dev/logo.png" width="200" height="200" alt="nonebot"></a>
</p>

<div align="center">

nonebot-plugin-mahjong-scoreboard
============

_✨ NoneBot 日麻记分器插件 ✨_

</div>

<p align="center">
  <a href="https://raw.githubusercontent.com/ssttkkl/nonebot-plugin-mahjong-scoreboard/master/LICENSE">
    <img src="https://img.shields.io/github/license/ssttkkl/nonebot-plugin-mahjong-scoreboard.svg" alt="license">
  </a>
  <a href="https://pypi.python.org/pypi/nonebot-plugin-mahjong-scoreboard">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-mahjong-scoreboard.svg" alt="pypi">
  </a>
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="python">
</p>

支持适配器：[OneBot V11](https://onebot.adapters.nonebot.dev/)

支持驱动器：[FastAPI](https://v2.nonebot.dev/docs/tutorial/choose-driver)

## 功能

为群友提供日麻对局分数记录。根据马点进行PT精算，统计PT增减，支持对局与榜单查询与导出。

PT精算算法为（点数-返点+马点）/1000，返点和马点在创建赛季时进行设置。

## 常用Workflow

### 开启赛季

```
/新建赛季
```

### 记录半庄对局

```
任何人：/新建对局
A: /结算 25000
B: /结算 25000
C: /结算 25000
D: /结算 25000
```

### 记录东场对局

```
任何人：/新建对局 四人东
A: /结算 25000
B: /结算 25000
C: /结算 25000
D: /结算 25000
```

### 记录未完成对局

```
任何人：/新建对局
任何人：/设置对局进度 东一局0本场
A: /结算 25000 东
B: /结算 25000 南
C: /结算 25000 西
D: /结算 25000 北
```

### 将未完成对局设置为已完成

```
任何人：/设置对局进度 对局23050701 完成
```

### 删除对局

用户无需手动删除错误创建的对局。当对局新建超过24h仍未成功结算时，对局会自动删除。

删除已结算的对局需要管理员权限。

```
/删除对局 对局23050701
```

### 结算后为对局手动设置PT（当自动计算的PT不正确时，或者需要进行处罚时）

```
需要设置PT的人：/设置对局PT -52

或

任何人：/设置对局PT @需要设置PT的人 -52
```

## 指令

### 对局

- `/新建对局 [四人南|四人东]`
    - 别名：`/新对局`
- `/结算对局 <成绩> [对局<编号>] [@<用户>] [<自风>]`
    - 别名：`/结算`
- `/撤销结算对局 [对局<编号>] [@<用户>]`
    - 别名：`/撤销结算`
- `/设置对局PT <PT> [对局<编号>] [@<用户>]`
    - 别名：`/对局PT`
- `/删除对局 [对局<编号>]`
- `/设置对局进度 <东/南x局y本场 或 完成> [对局<编号>]`
    - 别名：`/对局进度`
- `/设置对局备注 [对局<编号>] <对局备注>`
    - 别名：`/对局备注`

与对局相关的指令可以省略对局编号，省略时默认对最近新建的对局进行操作。也可以通过回复Bot发出的对局消息来代替指定对局编号。

对局相关指令在对局完成超过24小时后需要拥有群主或管理员身份才能使用。（`/删除对局`除外，该指令需要拥有群主或管理员身份才能使用）

未完成且未设置进度的对局会在创建24小时后自动删除。赛季结束后，未完成对局会自动删除，所有已完成对局均无法再进行修改。

### 对局查询

- `/查询对局 [<编号>]`
    - 别名：`/对局`
- `/个人最近对局 [@<用户>]`
    - 别名：`/最近对局`
- `/群最近对局`
- `/个人未完成对局 [@<用户>]`
    - 别名：`/未完成对局`
- `/群未完成对局`
- `/导出赛季对局 [<代号>]`
    - 别名：`/导出对局`
- `/导出所有对局`

### 赛季

- `/查询赛季 [<代号>]`
    - 别名：`/赛季`，`/当前赛季`
- `/查询所有赛季`
    - 别名：`/所有赛季`
- `/新建赛季`
    - 别名：`/新赛季`
- `/开启赛季 [<代号>]`
- `/结束赛季`
- `/删除赛季 [<代号>]`

### 赛季查询

- `/查询榜单`
    - 别名：`/榜单`
- `/导出榜单`
- `/查询PT [@<用户>]`
    - 别名：`/PT`
- `/设置PT <PT> [@<用户>]`
    - 别名：`/设置pt`

### 数据统计

- `/对战数据`
- `/赛季对战数据 [<赛季代号>]`
- `/最近走势 [@<用户>]`
    - 别名：`/走势`

与赛季/赛季PT相关的指令均可通过私聊/群聊两种方式使用。当未指定参数时进入问答模式，回复`/q`可退出问答模式。

与赛季/赛季PT相关的指令（查询、导出除外）需要拥有群主或管理员身份才能使用。

## 配置

### mahjong_scoreboard_database_conn_url

数据库连接URL，必须使用异步SQLAlchemy驱动器。

默认值：sqlite+aiosqlite:///mahjong_scoreboard.db

### callback_host

回调HOST，若为非容器环境部署（go-cqhttp与nonebot均运行在同一环境）则保持默认值。若为Docker环境部署则设置为Docker容器名。用于上传文件时让go-cqhttp下载本机文件。

默认值：127.0.0.1

### callback_port

回调端口，保持默认值即可。

默认值：与PORT保持一致即可

## 在线乞讨

<details><summary>点击请我打两把maimai</summary>

![](https://github.com/ssttkkl/ssttkkl/blob/main/afdian-ssttkkl.jfif)

</details>

## LICENSE

> MIT License
>
> Copyright (c) 2022 ssttkkl
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.
> 
