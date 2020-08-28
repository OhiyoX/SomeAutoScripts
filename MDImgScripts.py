# -*- coding: utf-8 -*-
# @Time    : 8/25/2020 7:40 PM
# @Author  : OhiyoX
# @FileName: MDImgScripts.py
# @Software: PyCharm
# @Blog    ：https://blog.ohiyox.in/
# @Desc    : 用于自动清除typora写作后多余的图片，简洁文件夹，也可以自动上传图片到图床，同时修改文档中的图片链接

import os
import re
import json
import sys
import time
from urllib.parse import quote, unquote

# 阿里云OSS的SDK
try:
    import oss2
except ModuleNotFoundError:
    print('Oss2 Module not found, try "pip install oss2". ')
    os._exit(0)

# 配置
config = {
    "test_mode": True,  # 调试模式
    "date": {'year': '',  # 设置图床日期
             'month': ''
             },
    'dir_loc': 'blogimg'  # 设置图床文件夹
}


class ImgMD:
    """MD图片处理类"""

    def __init__(self):
        # 与MD文档有关的
        self.article_loc = r"D:\Users\OneDrive\WRITINGS\test.md"  # default for testing
        self.assets_loc = r"D:\Users\OneDrive\WRITINGS\test.assets"  # default for testing
        self.content = ""
        # 文档中的图片信息
        self.imgs_list = []
        self.imgs_url_list = []
        # 图片在本地中的存储信息
        self.assets_list = []
        self.get_imgs_list()
        self.get_assets_list()
        self.assets_name = re.search('.*\\\(.*)', self.assets_loc, re.S).group(1)

        # 与图床有关的
        with open('danger/oss_info.json') as f:
            self.oss_info = json.load(f)
        self.auth = oss2.Auth(self.oss_info['AccessKeyId'], self.oss_info['AccessKeySecret'])
        self.endpoint = self.oss_info['EndPoint']
        self.bucket_domain = 'https://' + self.oss_info['EndPoint'].replace('https://', self.oss_info['Bucket'] + '.')


        # 设置远端时间文件夹，如/2020/08/的格式
        localtime = time.localtime()
        year = str(localtime.tm_year) if not config['date']['year'] else config['date']['year']
        mon = localtime.tm_mon if not config['date']['month'] else config['date']['month']
        if mon < 10:
            mon = '0' + str(localtime.tm_mon)
        self.remote_dir_loc = config['dir_loc'] + '/' + year + '/' + mon



    def get_content(self, article_loc="", force=False):
        """获得文本内容"""
        if self.content and not force:
            return self.content
        else:
            foo = False
            count = 0
            while not foo and count <= 5:
                try:
                    if not config['test_mode']:
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
        if not force:
            if self.imgs_list and not url:
                return self.imgs_list
            if self.imgs_url_list and url:
                return self.imgs_url_list

        content = self.get_content(force=force)
        self.imgs_url_list = re.findall('!\[.*?\]\((.*?)\)', content, re.S)
        imgs_list = []
        for img_url in self.imgs_url_list:
            img = self.get_name_from_url(img_url) # 不支持绝对路径
            imgs_list.append(img)
        if not url:
            print("Done, %s img(s) found in article." % len(imgs_list))
            print('===', end='')
            print(imgs_list)
            self.imgs_list = imgs_list
            return imgs_list
        else:
            return self.imgs_url_list

    def get_assets_list(self):
        """获得图片文件夹中的图片列表"""
        bar = False
        count = 0
        while not bar and count <= 5:
            try:
                if not config['test_mode']:
                    self.assets_loc = input("input the imgs location（Leave it empty to use default folder）: \n")
                    if self.assets_loc == "":
                        self.assets_loc = self.article_loc.replace('.md', '.assets')
                for a, b, c in os.walk(self.assets_loc):
                    assets_list = c
                    print("Done, %s img(s) found in folder." % len(assets_list))
                    print('===', end='')
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

    def get_name_from_url(self, img_url):
        if '/' in img_url:
            # 是链接
            img = re.search('.*/(.*)', img_url).group(1)
            if '!' in img:
                img = re.search('(.*)!.*', img,re.S).group(1)
            return img
        else:
            return img_url

    def clear_img(self):
        """用于清除文件夹中无用的图片"""
        flag = False
        for file in self.assets_list:
            # typora中使用了自动转url
            u_file = quote(file)
            if u_file not in self.imgs_list and file not in self.imgs_list:
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
        dir_domain_prefix = self.bucket_domain + '/' + remote_dir_loc
        modify_flag = False
        content = self.content
        for img_url in imgs_url_list:
            img = unquote(self.get_name_from_url(img_url))
            u_img = quote(img)

            remote_img_url = dir_domain_prefix +'/'+ self.assets_name +'/' + img
            u_remote_img_url = dir_domain_prefix +'/'+ self.assets_name +'/' + u_img

            # 建立连接
            bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])
            # 判断图片是否在图床中
            remote_img_loc = remote_dir_loc + '/' + self.assets_name + '/' + img
            u_remote_img_loc = remote_dir_loc + '/' + self.assets_name + '/' + u_img
            exist = bucket.object_exists(remote_img_loc)
            if not exist:
                exist = bucket.object_exists(u_remote_img_loc)
            if remote_img_url in img_url or u_remote_img_url in img_url:
                # 图片url为图床链接，开始判断是否在图床中
                if exist:
                    print(img + " is already in remote, ignore it.")
                    continue
                # 否则上传图片
                print('It seems not in remote, try upload it.')
                self.upload(img_url)

            # 替换图片url
            if exist:
                remote_img_url = remote_img_url.replace('https://','')
                self.content = self.content.replace(img_url, 'https://'+ quote(remote_img_url) + '!xwbp')
                modify_flag = True
        if modify_flag:
            # 备份原文档
            with open(self.article_loc + '.original', 'w', encoding="UTF-8") as bk:
                bk.write(content)
            # 开始替换图片url
            with open(self.article_loc, 'w', encoding='UTF-8') as f:
                f.write(self.content)
            print('Img urls are successfully replaced.')
        else:
            print('No need to replace.')

    def upload(self, img_url='', imgs_url_list='', assets_loc='', assets_name=''):
        """用于批量上传图片"""
        # 建立远端连接
        url_list = []
        if not img_url and not imgs_url_list:
            url_list = self.imgs_url_list
        if img_url:
            if imgs_url_list:
                print('Error, can only set img_url or imgs_url_list.')
            url_list.append(img_url)

        if not assets_loc:
            assets_loc = self.assets_loc
        # 设置上传的文件夹名字
        if not assets_name:
            assets_name = re.search('.*\\\(.*)', assets_loc, re.S).group(1)
            self.assets_name = assets_name

        bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])

        # 上传文件夹计数
        imgs_total = len(url_list)
        img_count = 0
        for img_url in url_list:
            img_url = unquote(img_url)
            img = self.get_name_from_url(img_url)
            if 'aliyuncs\.com/' in img_url: # 判断是否在图床
                print("\"" + img + "\" maybe on Internet.")
                self.re_upload(img_url)
                img_count += 1
                continue
            else:
                # progress_callback为可选参数，用于实现进度条功能
                def percentage(consumed_bytes, total_bytes):
                    if total_bytes:
                        rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                        print('\r{0}% '.format(rate), end='')
                        sys.stdout.flush()

                if img in self.assets_list:
                    img_loc = assets_loc + '\\' + img
                    remote_img_loc = self.remote_dir_loc + '/' + assets_name + '/' + img
                    if not bucket.object_exists(remote_img_loc):  # 判断远端文件是否存在
                        oss2.resumable_upload(bucket,
                                              remote_img_loc,
                                              img_loc,
                                              multipart_threshold=200 * 1024,
                                              part_size=100 * 1024,
                                              num_threads=3,
                                              progress_callback=percentage)
                        print(', ' + img + ' is successfully uploaded.')
                    else:
                        print(img + " already exists, next...")
                else:
                    print("Img is not found in .assets, so can't upload it.")
            img_count += 1

        if img_count == imgs_total:
            print("All imgs are uploaded.")
            return True
        else:
            return False

    def re_upload(self,img_url):
        """将网络上的图片转到图床里"""
        pass


if __name__ == '__main__':
    md = ImgMD()
    md.clear_img()
    result = md.upload()
    if result:
        md.change_img_url()
