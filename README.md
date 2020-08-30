# SomeAutoScripts
一些自动化脚本，包括结合typora对.md文档剔除无用图片、自动上传图片、替换本地图片url为图床url等。

# Typora + OSS + Python，我实现了一个简单又自由的博文发布流程



## 一、构思

### 1

本来是要先写一篇MacroDroid自动化的博客文章，但一想到要进行繁琐的图片编辑操作，就失去了90%的兴致，于是我想先解决这个繁琐的问题。

是这样的，我习惯用Typora写博客，即先用Typora写一个Markdown文档，再将Markdown文档发布到其他地方。在写作的过程中可能会多次调整图片，Typora支持在插入图片的同时，在本地文档同目录下新建同名加后缀.assets的目录用于保存插入的图片。这样很方便，将图片放在同一个位置管理，以后转移文档的时候就可避免图片丢失的问题了。

但这个功能却有一个很不合理的设计：如果我多次插入不同的图片，最后只保留了一张图片，那么只有一张图片是有效的，而其他图片都是无效的，Typora却不会自己删除这些无效的图片。虽然小新的家里很乱，但对于自己电脑的管理确却非常注重整洁和逻辑性，写作完成后留下大量无效图片占磁盘空间我是非常不能接受的，让有强迫症的我简直不能忍。正好想到我会python，于是连夜写出了个脚本解决这个问题。

### 2

第二天晚上，我应该开始写博客了。但这时我想到又要进行将本地图片单独上传到图床，以便我的博客网站上也能好好看图的繁琐操作，就又失去了90%的兴致，于是我想先再解决这个繁琐的问题。

是这样的，我用阿里云OSS（对象存储）做图床。我不用免费图床，因为我对免费的东西不放心，免费的东西具有不可抗力，可以随时抽离服务，而且自由度非常低。对象存储一般都支持图片处理的Style规则，比如加上自动转webp、图片缩小的规则可以明显省对象存储的流量（当然我的博客从来没有人看，流量都是我自己用掉了），或者自己加水印等，这样在图片URL中我们还需要加入Style规则后缀。

即使是在图床上我也要求用整洁的文件夹分类管理图片。我习惯用日期+文章名字，比如这篇文章写于2020年8月，本地上存储图片的assets文件夹为`Typora_PythonScript.assets`，那么我在OSS上的文件夹路径为`blogimg/2020/08/Typora_PythonScript.assets`，其中`blogimg`是我专门用于存储博客图片的主文件夹，这样，我就能很方便地管理这些图片了，包括以后迁移到别的存储空间等。（读者可能会问，如果一张图片在不同的文章中使用了怎么办，这样就要建立多个副本了，不就冗余了吗？是的，这个问题可能会有，但小新不想解决。）

我曾用过几款图床插件，如PicGo等，但功能都不能使我满意，我想要的上述功能，为什么都不做一下呢？每次上传图片、分类、加样式后缀都要手动去操作，真的很难用。正好小新会python，就想到能否用python解决这个问题，阿里云OSS有python的SDK，这样对图床的操作就可以用脚本一键完成了。

于是连夜在脚本里补充了这个功能。

顺便提一下，阿里云OSS的自带的软件OSS Browser非常好用。

### 3

本来这个晚上可以好好写博客了，但小新又想到了一个新的问题。在写作的插图的过程中，可能会插入网络图片，这样我把写好的Markdown复制粘贴到自己的网站上时，就会因为原图防盗链而无法显示。

其实这个问题可以通过在Typora中开启自动下载网络图片的功能来解决，但如果我不这么做呢？我想让脚本自己去解决这个问题，自动将文档中的网络图片（比如微信公众号、简书的图片）自动转到图床中。

### 4

自动上传图片到图床后，就有必要将原文档中的图片地址（无论是本地图片还是网络图片）统一改为图床上的URL，这个也可以在脚本中添加函数解决。为了安全起见，在对原文档更改时，首先自动进行备份。

在写这个功能的时候我想到应该增加对微信公众号的支持（由于我的OSS使用了防盗链，需要在白名单中添加微信自带的图床域名“https://mmbiz.qpic.cn”），考虑到微信公众号最大只支持5M（现在貌似为10M）的图片，我们可以在替换URL的过程中，特别为原文档生成一个微信版本的文档，其主要是替换样式后缀，此外在阿里云OSS后台我特别添加一个微信公众号图片样式规则，我的是`!xweixin`，规则主要为将图片转为webp格式（这样可以大幅降低图片体积）和缩小尺寸（宽度限制在1920px），这样图片体积就基本控制在5M以内了。

## 二、实现

根据以上构想，我们再整理一下思路。我需要实现的脚本功能包括这些：

> 1、写作完成后自动清除assets中无效的图片。
>
> 2、自动上传本地图片或网络图片到自建图床中，同时图床文件夹为日期+文章名的规范，以方便管理。
>
> 3、若图片已在图床中，但不符合文件存放规范，则将原位置移动新文件夹下。
>
> 4、自动上传图片后，自动替换原文档中的图片url，同时生成一份微信公众号版本。
>
> 5、通过一个分离的config.json 对以上环节进行调整。

实现的代码我就不放在这里了，请读者移步Github，欢迎反馈加星。

https://github.com/OhiyoX/SomeAutoScripts

关于阿里云OSS权限的信息涉及到安全问题，我在脚本同目录下新建一个名为danger的文件夹，使用`oss_info.json`配置，并用了`.gitignore`忽略。

配置规范为：

> ```json
> {
>   "AccessKeyId": "xxxxxxx",
>   "AccessKeySecret": "xxxxxxxx",
>   "EndPoint": "xxxxxxxxxxx",
>   "Bucket": "xxxxxxxxx"
> }
> ```

## 三、使用

前面说了很多，其实是为了体现使用时的简单。

使用这个脚本只需要三个前提条件：

> 1、安装python，建议大于等于3.7
>
> 2、安装oss2和requests库
>
> 3、Typora里图片保存路径设置为.assets目录，路径使用了unicode-escape，当然没有unicode-escape也行。

在各种配置完成的情况下只需要三个步骤：

> 1、写完文章。
>
> 2、点击运行脚本。
>
> 3、完成

### 实例

以我之前的一篇博文为例，原文档存放在电脑中，并有相应的asset文件夹存放图片：

`D:\Users\OneDrive\WRITINGS\日志\kindle英文阅读实践.md`

`D:\Users\OneDrive\WRITINGS\日志\kindle英文阅读实践.assets\`

**具体操作**：

1、把脚本放在你喜欢的地方，脚本我放在我本地的项目中，名为`MDImgScripts.py`，我创建了一个快捷方式在桌面，以方便打开。

2、配置好`oss_info.json` 和`config.json`(其实这两个可以整合到脚本里，但我不想这么做)。因为这是很久以前的文章，所以需要调整一下文件夹时间。

![image-20200829195116113](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829195116113.png!xwbp)

3、点击脚本打开界面如图：

![image-20200829194703809](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829194703809.png!xwbp)

将需要处理的文档拖放到窗口中，会自动带上文件夹路径，回车：

![image-20200829195308875](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829195308875.png!xwbp)

脚本会提示在文章中发现的图片及数量（用正则表达式实现的，所以如果插入图片语法在代码块中也会被误识别，不过现在没精力搞这个，因为出现的情况很少。）

同时会提示输入图片存放的路径，一般情况下不用输入，直接回车即可，因为.assets和文档在同一目录下，且命名前缀相同。这里我直接回车。

之后脚本自动运行，最后完成：

![image-20200829200625492](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829200625492.png!xwbp)

脚本会提示在assets里发现的文件数量，经过与文章中的图片比较发现没有无效的图片。从提示中还可以看到原文档中有一个网络图片，脚本将图片上传到图床中。

在所有图片上传后，将原文档中的图片url替换为图床的，同时生成了一个用于复制到公众号的文档版本。

在文件管理器中查看是这样的：

![image-20200829201102871](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829201102871.png!xwbp)

打开文档可以看到图片地址均已替换：

![image-20200829201243474](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829201243474.png!xwbp)

在阿里云OSS中同时生成了文件夹和文件：

![image-20200829201354215](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829201354215.png!xwbp)



### 关于微信版本的文档

使用`weixin-edition`这个文档可以直接把文字和图片复制到后台而无需再上传图片，关于Markdown转网页格式，我用的一个GitHub项目，下载到本地，或者放在自己的服务器上，用浏览器就能直接打开了，比如我的：https://lab.ohiyox.in/md/。

![image-20200829202404928](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829202404928.png!xwbp)

点击复制，在公众号后台粘贴即可，省去了上传图片的步骤。

![image-20200829202526885](https://ohiyoxpicalin.oss-cn-shanghai.aliyuncs.com/blogimg/2020/08/Typora_PythonScript.assets/image-20200829202526885.png!xwbp)

### P.S.

其实用Typora就可以直接复制粘贴，在网页模式下可以直接复制到微信公众号或者WordPress博客后台，也可以在代码模式下复制到如Typecho的纯markdown后台。

以上，谢谢各位阅读。

最后再提示一下源码地址，欢迎反馈加星：

https://github.com/OhiyoX/SomeAutoScripts

### PP.S.

把这一套流程通过Python完善后，我好像可以开始写关于MacroDroid自动化的文章了，本篇文章即通过这个流程发布的。好吧，等我看完这期的明日之子第四季就去写。:)

