# -*- coding: utf-8 -*-
# @Time    : 8/25/2020 7:40 PM
# @Author  : OhiyoX
# @FileName: ClearImgScripts.py
# @Software: PyCharm
# @Blog    ：http://blog.ohiyox.in/
# @Desc    : 用于自动清除typora写作后多余的图片，简介文件夹

import os

def clear():
    article_loc = input("input the file location: ")
    img_loc = input("input the imgs location: ")
    try:
        with open(article_loc,'r',encoding="UTF-8") as f:
            content = f.read()

    except:
        print("Notice! File not found or there is an error")
        os._exit(0)

    print(content)

if __name__ == '__main__':
    clear()



