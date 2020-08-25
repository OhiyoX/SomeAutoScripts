# -*- coding: utf-8 -*-
# @Time    : 8/25/2020 7:40 PM
# @Author  : OhiyoX
# @FileName: ClearImgScripts.py
# @Software: PyCharm
# @Blog    ：http://blog.ohiyox.in/
# @Desc    : 用于自动清除typora写作后多余的图片，简介文件夹

import os
import re

test_mode = True


def clear():
    foo = False
    count = 0
    while not foo and count <= 5:
        try:
            if test_mode:
                article_loc = r"D:\Users\OneDrive\WRITINGS\test.md"
            else:
                article_loc = input("input the article location: ")
            with open(article_loc, 'r', encoding="UTF-8") as f:
                content = f.read()
            foo = True
            img_list = re.findall('!\[.*?\]\(.*?/(.*?)\)', content, re.S)
            print(img_list)
        except:
            print("Notice! File not found or there is an error.")
            count += 1
            if count > 5:
                os._exit(0)

    bar = False
    count = 0
    while not bar and count <= 5:
        try:
            if test_mode:
                img_loc = r"D:\Users\OneDrive\WRITINGS\test.assets"
            else:
                img_loc = input("input the imgs location: ")
            for a,b,c in os.walk(img_loc):
                file_list = c
                print(file_list)
            bar = True
        except:
            print(Exception)
            count += 1
            if count > 5:
                os._exit(0)
    flag = False
    for file in file_list:
        if file not in img_list:
            os.remove(img_loc + '\\' + file)
            print(file + " is removed.")
            flag = True
    if flag == False:
        print("Good, no redundant imgs.")



if __name__ == '__main__':
    clear()
