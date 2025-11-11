# 项目整合第一版：

## ToDoList：

### 1、Spidering-微博信息爬取：

我添加了截图和视频加载功能。但目前对于视频和图片同时存在的情况似乎不太行（ex. wid="Qd3DYD8go"）

可以用网页版微博找微博样例（受限于目前程序性能，样例中所含视频最好不要超过30s），然后将网址最后的16位数字使用WebUI/test_mid2wid.py程序转换为9位的wid。

如 https://weibo.com/6700634492/5231122749326560 最后的 5231122749326560 转换为 wid 后为 Qd3DYD8go。对应的页面是 https://weibo.cn/comment/Qd3DYD8go 。

### 2、Reading-视频内容分析：

我把cli.py文件里main()函数改名为video_main了，然后把输入视频文件地址从命令行参数里提出来了。

目前分析有点慢，最好再整快一点，看看能不能换个模型之类的。

### 3、Picturing-微博用户画像：

我改了main函数所在文件的名字，改成了weibo_user_picture.py，然后改了输出。读微博所需cookies改为从Spidering/.env文件中读取。

需要整个热词图和简洁一点的总结文字出来，作为最终输出。【然后添加一个机器人判别功能，判定一下哪些评论用户有可能是水军】11/11新增


### 给我自己的一点备忘：

1、添加运行后清空static中除progress.js文件以外所有文件功能

2、修改页面显示效果

3、情感分析部分功能添加

## 使用说明：

项目运行主函数在WebUI/WebUI-Test.py文件里，直接运行这个文件，等待控制台输出http://localhost:8080（全名应该是这个，反正找这个8080监听端口就行）。

点进去后就进入运行界面，搜索框下方蓝字部分为样例，可以直接点击运行。也可以在输入框里面输wid后点确定（wid是什么参照上文ToDoList的1）。

运行完成后的结果页面中显示的图片和视频都在WebUI/static文件夹中。


环境基本上都在requirements.txt（根目录下面和GetOutput.py文件挨着的那个）里面，但是没怎么改诸位的环境，所以理论上直接把自己那部分的文件夹中内容copy下来，自己那部分还是能在原来的自己的环境里运行的，所以如果不想配置整个项目的环境，也可以就这么只改自己的部分后再给我。

除上述requirements.txt文件中依赖项外，若希望运行整个项目，还需要pip install ffmpeg和ollama pull llama3.2-vision（ollama从https://ollama.com/download这个界面下载）

读微博所需cookies需要在Spidering/.env文件自行修改适配。
