# AutoBangumi_TR

> transmission资源占用比较小
> 
> 在MT7981B的路由上,cpu占用大概的5%-10%, 内存占用大概25-50M

## 区别

* 支持transmission
* 企业微信群机器人通知
* webui小改动

===[qb只推荐用原版!!!](https://www.autobangumi.org)===

## 项目进度

### 已测试功能

- [x] mikan 单个rss订阅
- [x] mikan 聚合rss订阅
- [x] 单种子单文件下载完成重命名
- [x] 下载完成企业微信群机器人通知
- [x] webui规则页面: 禁用状态也可设置并更新
- [x] 合集下载重命名

### 已知问题

#### 合集重命名

* 合集重命名只支持单层文件夹结构

```
--根文件夹
  |__ 视频
  |__ 字幕
```

* 下载路径必须包含`番剧名/Season X`

* 自己下载的种子添加`label:` `Bangumi`后就能被自动重命名

## 安装

### docker 安装 AutoBangumi_TR

docker: https://hub.docker.com/r/jqtmviyu/auto_bangumi_tr

### 源码运行

* 后端为python3, 路径为`backend/src`
* 前端为vite+vue3, 路径为`webui`, 须打包`dist`
* 需创建`config`, `data`文件夹放在`src`下

### Transmission安装

* openwrt: 直接安装`luci-app-transmission`

* docker: ...

## 扩展

### 设置相关

* RPC `授权验证`需要开启
* 如果是在openwrt上安装TR,记得更改`配置文件目录`,默认temp重启会丢失进度
* 企业微信群机器人使用只需设置`Token`(即`webhookkey`)

### 名词解释

* 聚合 RSS: 一条rss里有多部番
* 订阅: 持续追踪rss更新
* 收集: 一次性下载, 后续不再追踪rss更新

### TR 第三方gui和webui

官方的webui不支持标签和多文件重命名,推荐使用第三方替换

https://github.com/openscopeproject/TrguiNG