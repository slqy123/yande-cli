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
推荐将此工具加入环境变量，具体做法为，在某个加入的环境变量的文件夹下创建一个批处理文件，如`yande.cmd`，写入以下命令
```
@python "/your/path/to/app.py" %*
```
将里面的路径换成自己的`app.py`的路径。
如按上述方法执行后，在命令行执行 `yande --help` 即可查看各命令及其使用方法

## 使用前的一些配置
### IDM
本工具使用IDM进行下载，使用前需要对IDM进行以下设置
- 在 `下载-选项-代理服务器` 中设置代理
- 在 `下载-选项-连接-例外` 新建一个项目 `https://files.yande.re` 最大连接数为1
- 在左侧 `队列-主要下载队列` 右键选择`编辑队列` 在`队列中的文件`中选择同时下载文件为2-3个(自行决定，不要太多)

### settings.py
见 `settings.py` 内的注释

