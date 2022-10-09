# yande-cli
## 简介
本命令行工具主要用于下载和管理来自yande.re上的文件，支持以下操作
1. 多种下载方式，包括按时间，tag，和id为依据下载
2. (仅)支持将图片从电脑导入手机观看
3. 简易的图片打分方法

主要用到的工具和库有
- adb 实现和手机的文件传输
- IDM 好用的第三方下载工具
- click 构建命令行
- sqlalchemy 用于操作数据库
- inquirer 用于命令行交互
- grequests 异步请求

## 安装和使用
使用前请确保 `IDM`和 `adb` 已安装且加入环境变量。

使用 `git clone https://github.com/slqy123/yande-cli.git` 克隆仓库到本地，安装必要的库，再运行`python app.py `即可。
推荐将此工具加入环境变量，具体做法为，在某个已经加入环境变量的文件夹下创建一个批处理文件，如`yande.cmd`，写入以下命令
```
@python "/your/path/to/app.py" %*
```
将里面的路径换成自己`app.py`的路径。
按上述方法执行后，在命令行执行 `yande --help` 即可查看各命令及其使用方法

## 使用前的一些配置
### IDM
本工具使用IDM进行下载，使用前需要对IDM进行以下设置
- 在 `下载-选项-代理服务器` 中设置代理
- 在 `下载-选项-连接-例外` 新建一个项目 `https://files.yande.re` 最大连接数为1
- 在左侧 `队列-主要下载队列` 右键选择`编辑队列` 在`队列中的文件`中选择同时下载文件为2-3个(自行决定，不要太多)

### settings.py
见 `settings.py` 内的注释

> 如果你是第一次运行，请首先添加一些图片，
> 运行 `yande update --mode tag --tag "your tag" `引号里放你要的tag。
> 然后运行 `yande dl [AMOUNT]` 下载这些图片，等待IDM图片下载完成后运行 `yande add` 添加下载的图片即可
> ，然后就可以通过 `yande push [AMOUNT]` 来导入手机了

## 关于图片的打分
数据库中用star的存放图片的分数，刚下载的图片分数为0。
每个被push的图片，在浏览时可以选择不喜欢的图片删除，所有图片在pull时，都会count+1，然后分两种情况
- 图片存在，star+1，此时图片的star=count
- 图片被删除，star不变，此时图片star != count，若star为0，则将状态改为删除。

也就是说，图片评分大致可分为三种
- star=count，每次push都没被删除，push时也只会选择这样的图片push，若其在某次push中被删除了，则变为下面两种状态
- star=0,count=1，第一次就被删除，说明质量很差，删除本地文件
- star>0, count=star+1，图片被定格在了这个star，因为不会再被push了
