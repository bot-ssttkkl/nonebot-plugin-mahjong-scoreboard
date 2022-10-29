日麻寄分器
============

支持适配器：[OneBot V11](https://onebot.adapters.nonebot.dev/)

支持驱动器：[FastAPI](https://v2.nonebot.dev/docs/tutorial/choose-driver)

## 配置

### mahjong_scoreboard_database_conn_url

数据库连接URL，必须使用异步SQLAlchemy驱动器。

默认值：sqlite+aiosqlite:///mahjong_scoreboard.db

### mahjong_scoreboard_callback_host

回调HOST，若为非容器环境部署（go-cqhttp与nonebot均运行在同一环境）则保持默认值。若为Docker环境部署则设置为Docker容器名。用于上传文件时让go-cqhttp下载本机文件。

默认值：127.0.0.1

### mahjong_scoreboard_callback_port

回调端口，保持默认值即可。

默认值：与PORT保持一致即可

## 指令

### 对局

- /新建对局 [四人南|四人东]
- /结算对局 <成绩> [对局<编号>] [@<用户>] [<自风>]
- /撤销结算对局 [对局<编号>] [@<用户>]
- /设置对局PT <PT> [对局<编号>] [@<用户>]
- /删除对局 [对局<编号>]
- /设置对局进度 <进度> [对局<编号>]

### 对局查询

- /查询对局 [<编号>]
- /个人最近对局 [@<用户>]
- /群最近对局
- /个人未完成对局 [@<用户>]
- /群未完成对局
- /导出赛季对局 [<代号>]
- /导出所有对局

### 赛季

- /查询赛季 [<代号>]
- /查询所有赛季
- /新建赛季
- /开启赛季 [<代号>]
- /结束赛季
- /删除赛季 [<代号>]

### 赛季PT

- /设置赛季PT <PT> [@<用户>]
- /查询PT [@<用户>]
- /查询榜单
- /导出榜单

以上命令格式中，以<>包裹的表示一个参数，以[]包裹的表示一个可选项。参数可通过任意顺序提供。

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
