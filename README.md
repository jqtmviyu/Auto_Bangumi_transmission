<p align="center">
    <img src="docs/image/icons/light-icon.svg" width=50%/ alt="">
    <img src="docs/image/icons/tr.png" style="margin-left:20px;" width=8%/ alt="">
</p>
<p align="center">
    <img title="docker build version" src="https://img.shields.io/docker/v/jqtmviyu/auto_bangumi_tr" alt="">
    <img title="release date" src="https://img.shields.io/github/release-date/jqtmviyu/auto_bangumi_tr" alt="">
    <img title="docker pull" src="https://img.shields.io/docker/pulls/jqtmviyu/auto_bangumi_tr" alt="">
    <img title="python version" src="https://img.shields.io/badge/python-3.11-blue" alt="">
</p>

<p align="center">
  <a href="https://www.autobangumi.org">官方网站</a> | <a href="https://www.autobangumi.org/deploy/quick-start.html">快速开始</a> | <a href="https://github.com/jqtmviyu/Auto_Bangumi_TR">github仓库</a> | <a href="https://hub.docker.com/r/jqtmviyu/auto_bangumi_tr">dockerhub仓库</a> | <a href="https://t.me/autobangumi">TG 群组</a>
</p>

#### 与 ***estrellaxd/Auto_Bangumi*** 的区别

* 支持==transmission==
* 企业微信群机器人通知
* webui小改动
* 文档直接看原作者的

==qBittorrent只推荐用原版!!!==(迁移数据理论上兼容, 没有测试过)

#### 为什么有这个fork

* 为什么不用qb:
  * 跑在MT7981B的路由上, qBittorrent-web带不动
  * transmission cpu占用大概的5%-10%, 内存占用大概25-50M
* 为什么不合并到上游: 
  * 刚学python,代码太烂
  * 后面要重构下载器,协程看不懂
* 哪部分代码是你写的:
  * 都是chatgpt写的,我只是代码的搬运工
  * 下载器主体是 `codycjy` 完成的, 但下载了`EstrellaXD:3.2-dev`分支跑不动, 只好开始修bug
  * 从main分支3.1.13开始, 目前合并主分支到3.1.14
  * 不会一直追着主仓库更新,除非自己遇到bug非修不可

#### 项目进度

##### 已测试功能

- [x] mikan 单个rss订阅
- [x] mikan 聚合rss订阅
- [x] 单种子单文件下载完成重命名
- [x] 下载完成企业微信群机器人通知
- [x] webui规则页面: 禁用状态也可设置并更新
- [x] 合集下载重命名
- [x] 开放自定义第三方openaiapi,实侧`grog`的`llama3-70b-8192`模型可以兼容

#### 已知问题

##### 合集重命名

* 合集重命名只支持单层文件夹结构

```
--根文件夹
  |__ 视频
  |__ 字幕
```

* 下载路径必须包含`番剧名/Season X`

* 自己下载的种子添加`label`=`Bangumi`后就能被自动重命名

* 多季合集, 即父文件夹内有多个子文件夹, 暂不支持

#### 安装

##### Transmission安装

* openwrt: 直接安装`luci-app-transmission`
* 其他平台: 自行寻找教程
* RPC `授权验证`需要开启,并设置用户名和密码
* 如果是在openwrt上安装,记得更改`配置文件目录`,默认temp重启会丢失进度
* 企业微信群机器人使用只需设置`Token`(即`webhookkey`)

##### 第三方gui和webui

官方的webui不支持标签和多文件重命名,推荐使用第三方替换[TrguiNG](https://github.com/openscopeproject/TrguiNG)

##### docker-compose 安装 AutoBangumi_TR

* 创建文件夹 `config`, `data`

* 新建`docker-compose.yml`文件, 内容如下:

```yaml
services:
  AutoBangumi:
    image: "jqtmviyu/auto_bangumi_tr:latest"
    container_name: AutoBangumi
    volumes:
      - ./config:/app/config
      - ./data:/app/data
    ports:
      - "7892:7892"
    restart: unless-stopped
    dns:
      - 9.9.9.9
    environment:
      - TZ=Asia/Shanghai
      - PGID=0  # use `id` cmd to get true arg
      - PUID=0
      - UMASK=022
      # - AB_DOWNLOADER_HOST=192.168.0.1:9091
      # - AB_DOWNLOADER_USERNAME=admin
      # - AB_DOWNLOADER_PASSWORD=admin
```

* 启动容器 `docker-compose up -d`

* webui启动地址 `http://localhost:7892`, 默认用户名密码为`admin/admin`

* 需要在设置页面更改`下载器路径`,`用户名`和`密码`

* 后续使用参考 <a href="https://www.autobangumi.org">官方网站</a>

#### 名词解释

* 聚合 RSS: 一条rss里有多部番
* 订阅: 持续追踪rss更新
* 收集: 一次性下载, 后续不再追踪rss更新
