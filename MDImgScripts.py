# -*- coding: utf-8 -*-
# @Time    : 8/25/2020 7:40 PM
# @Author  : OhiyoX
# @FileName: MDImgScripts.py
# @Software: PyCharm
# @Blog    ：https://blog.ohiyox.in/
# @Desc    : 用于自动清除typora写作后多余的图片，简介文件夹

import os
import re
import json
import sys
import time
import urllib

import oss2

test_mode = True


class ImgMD:
    """MD图片处理类"""

    def __init__(self):
        # 与MD文档有关的
        self.article_loc = r"D:\Users\OneDrive\WRITINGS\test.md"  # default for testing
        self.assets_loc = r"D:\Users\OneDrive\WRITINGS\test.assets"  # default for testing
        self.content = ""
        self.imgs_list = []
        self.assets_list = []
        self.get_imgs_list()
        self.get_assets_list()

        # 与图床有关的
        with open('danger/oss_info.json') as f:
            self.oss_info = json.load(f)

        # 设置远端时间文件夹，如2020/08的格式
        localtime = time.localtime()
        year = str(localtime.tm_year)
        mon = localtime.tm_mon
        if mon < 10:
            mon = '0' + str(localtime.tm_mon)
        dir_name = re.search('.*\\\(.*)', self.assets_loc, re.S).group(1)
        self.remote_dir_loc = 'blogimg/' + year + '/' + mon + '/' + dir_name

    def get_content(self, article_loc="", force=False):
        """获得文本内容"""
        if self.content and not force:
            return self.content
        else:
            foo = False
            count = 0
            while not foo and count <= 5:
                try:
                    if not test_mode:
                        if not article_loc:
                            self.article_loc = input("input the article location: ")
                            article_loc = self.article_loc
                    else:
                        article_loc = self.article_loc
                    with open(article_loc, 'r', encoding="UTF-8") as f:
                        self.content = f.read()
                    foo = True
                    return self.content
                except:
                    print("Notice! File not found or there is an error, retry.")
                    count += 1
                    if count > 5:
                        os._exit(0)
                        return None

    def get_imgs_list(self, url=False, force=False):
        """获得文档中的图片列表"""
        if self.imgs_list and not url and not force:
            return self.imgs_list
        else:
            content = self.get_content(force=force)
            if not url:
                imgs_list = re.findall('!\[.*?\]\(.*?/(.*?)\)', content, re.S)
                print("Done, %s img(s) found in article." % len(imgs_list))
                print('===', end='')
                print(imgs_list)
                self.imgs_list = imgs_list
                return imgs_list
            else:
                imgs_url_list = re.findall('!\[.*?\]\((.*?)\)', content, re.S)
                return imgs_url_list

    def get_assets_list(self):
        """获得图片文件夹中的图片列表"""
        bar = False
        count = 0
        while not bar and count <= 5:
            try:
                if not test_mode:
                    self.assets_loc = input("input the imgs location（Leave it empty to use default folder）: \n")
                    if self.assets_loc == "":
                        img_loc = self.article_loc.replace('.md', '.assets')
                for a, b, c in os.walk(self.assets_loc):
                    assets_list = c
                    print("Done, %s img(s) found in folder." % len(assets_list))
                    print('===',end='')
                    print(assets_list)
                    self.assets_list = assets_list
                    return assets_list
                bar = True
            except:
                print(Exception)
                count += 1
                if count > 5:
                    os._exit(0)
                    return None

    def clear_img(self):
        """用于清除文件夹中无用的图片"""
        flag = False
        for file in self.assets_list:
            # typora中使用了自动转url
            u_file = urllib.parse.quote(file)
            if u_file not in self.imgs_list:
                os.remove(self.assets_loc + '\\' + file)
                print(file + " is removed.")
                flag = True
        if flag == False:
            print("Good, no redundant imgs.")

    def change_img_url(self, remote_dir_loc=''):
        """用于更换文章中的图片地址"""
        # 判断图片是否已在图床中
        if remote_dir_loc == '':
            remote_dir_loc = self.remote_dir_loc
        imgs_url_list = self.get_imgs_list(force=True, url=True)
        remote_url_prefix = 'https://' + self.oss_info['EndPoint'].replace('https://', self.oss_info['Bucket'] + '.') +'/'+ remote_dir_loc
        flag = False
        content = self.content
        for img_url in imgs_url_list:
            img = re.search('.*/(.*)', img_url).group(1)
            remote_img_url = remote_url_prefix + '/' + img

            if re.search(remote_img_url, img_url, re.S):
                print("Remote img is found, pass.")
                continue

            # 替换图片url
            # 建立远端连接
            auth = oss2.Auth(self.oss_info['AccessKeyId'], self.oss_info['AccessKeySecret'])
            bucket = oss2.Bucket(auth, self.oss_info['EndPoint'], self.oss_info['Bucket'])
            exist = bucket.object_exists(remote_dir_loc + '/'+ img)
            if exist:
                self.content = self.content.replace(img_url, remote_img_url+'!xwbp')
                flag = True
                # self.upload(img,self.assets_loc)
        if flag:
            with open(self.article_loc + '.original', 'w', encoding="UTF-8") as bk:
                bk.write(content)
            with open(self.article_loc, 'w', encoding='UTF-8') as f:
                f.write(self.content)

    def upload(self, imgs_list, assets_loc, dir_name=''):
        """用于上传图片"""
        # 建立远端连接
        auth = oss2.Auth(self.oss_info['AccessKeyId'], self.oss_info['AccessKeySecret'])
        endpoint = "https://oss-cn-shanghai.aliyuncs.com"
        bucket = oss2.Bucket(auth, endpoint, self.oss_info['Bucket'])

        # 设置上传的文件夹名字
        if not dir_name:
            dir_name = re.search('.*\\\(.*)', assets_loc, re.S).group(1)

        # 上传文件夹计数
        imgs_total = len(imgs_list)
        img_count = 0
        for img in imgs_list:
            if re.search('aliyuncs\.com',img,re.S):
                continue
            else:
                img_loc = assets_loc + '/' + img
                remote_img_loc = self.remote_dir_loc + '/' + img
                if not bucket.object_exists(remote_img_loc):  # 判断远端文件是否存在
                    oss2.resumable_upload(bucket,
                                          remote_img_loc,
                                          img_loc,
                                          multipart_threshold=200 * 1024,
                                          part_size=100 * 1024,
                                          num_threads=3,
                                          progress_callback=self.percentage)
                    print(', ' + img + ' is uploaded successfully')
                else:
                    print(img + " already exists, next...")
            img_count += 1

        if img_count == imgs_total:
            print("All imgs are uploaded.")
            return 0

    # progress_callback为可选参数，用于实现进度条功能
    def percentage(self, consumed_bytes, total_bytes):
        if total_bytes:
            rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
            print('\r{0}% '.format(rate), end='')
            sys.stdout.flush()


if __name__ == '__main__':
    md = ImgMD()
    md.clear_img()
    u = input('upload?')
    if u == 'y':
        md.upload(md.imgs_list,md.assets_loc)
    md.change_img_url()
