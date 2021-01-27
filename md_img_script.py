# -*- coding: utf-8 -*-
# @Time    : 8/25/2020 7:40 PM
# @Author  : OhiyoX
# @FileName: MDImgScripts.py
# @Software: PyCharm
# @Blog    ：https://blog.ohiyox.in/
# @Desc    : 1、用于自动清除typora写作后多余的图片，简洁文件夹
#            2、也可以自动上传图片到图床，同时修改文档中的图片链接
#            3、若图片为网络图片，将自动转移到图床，同时修改文档中的图片链接
#            4、若图片在图床，但存放位置不规范，也会自动转移位置，同时修改文档中的图片链接


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

try:
    import requests
except ModuleNotFoundError:
    print('requests Module not found, try "pip install requests".')
    os._exit(0)

# 配置
# {
#     "test_mode": True,  # 调试模式
#     "date": {"year": "2019",  # 设置文件夹日期，留空默认为本年
#              "month": "1" # 设置文件夹日期，留空默认为本月
#              },
#     "clean_local_assets": True,
#     "dir_loc": "blogimg",  # 设置图床文件夹
#     "style": "!xwbp",  # 设置默认上传的图片规则，以后缀!标识
#     "re_loc": True,  # 对于已在图床中的图片，设置是否需要重新移动整理图片
#     "delete": True  # 对于移动图片，是否删除原位置
# }

with open('config.json') as cfig:
    config = json.load(cfig)


class ImgMD:
    """MD图片处理类"""

    def __init__(self):
        # 与MD文档有关的
        self.article_path = r"D:\Users\OneDrive\WRITINGS\in a old train\In a old train.md"  # default for testing
        self.assets_path = r"D:\Users\OneDrive\WRITINGS\in a old train\In a old train.assets"  # default for testing
        self.content = ""
        # 文档中的图片信息
        self.imgs_list = []
        self.imgs_url_list = []
        # 图片在本地中的存储信息
        self.assets_list = []

        self.get_imgs_list()
        self.get_assets_list()
        self.assets_name = re.search('.*\\\(.*)', self.assets_path, re.S).group(1)

        # 与图床有关的
        with open('danger/oss_info.json') as f:
            self.oss_info = json.load(f)
        self.auth = oss2.Auth(self.oss_info['AccessKeyId'], self.oss_info['AccessKeySecret'])
        self.endpoint = self.oss_info['EndPoint']
        self.bucket_domain = 'https://' + self.oss_info['EndPoint'].replace('https://', self.oss_info['Bucket'] + '.')

        # 设置远端时间文件夹，如/2020/08/的格式
        localtime = time.localtime()
        year = str(localtime.tm_year) if not config['date']['year'] else config['date']['year']
        mon = str(localtime.tm_mon if not config['date']['month'] else config['date']['month'])
        if int(mon) < 10:
            mon = '0' + str(int(mon))
        self.remote_dir_loc = self.__concat(config['dir_loc'], year, mon)

    def __concat(self, *str):
        """concat by '/'"""
        foo = []
        for s in str:
            foo.append(s)
        return '/'.join(foo)

    def get_content(self, article_path="", force=False):
        """获得文本内容"""
        if self.content and not force:
            return self.content
        else:
            foo = False
            count = 0
            while not foo and count <= 5:
                try:
                    if not config['test_mode']:
                        if not article_path:
                            self.article_path = input("input the article path: ")
                            if "\"" in self.article_path:
                                self.article_path = re.search("\"(.*)\"", self.article_path).group(1)
                            article_path = self.article_path
                    else:
                        article_path = self.article_path
                    with open(article_path, 'r', encoding="UTF-8") as f:
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
            img = self.get_name_from_url(img_url)  # 不支持绝对路径
            imgs_list.append(img)
        if not url:
            print("Done, %s img(s) found in article." % len(imgs_list))
            print('==', end='')
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
                    self.assets_path = input("input the imgs path（Leave it empty to use default folder）: \n")
                    if self.assets_path == '':
                        self.assets_path = self.article_path.replace('.md', '.assets')
                for a, b, c in os.walk(self.assets_path):
                    assets_list = c
                    print("Done, %s img(s) found in assets." % len(assets_list))
                    print('==', end='')
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
        if 'http' in img_url and '/' in img_url:
            # 是链接
            if 'https://mmbiz.qpic.cn/' in img_url:
                # 是微信订阅号图片
                img_info = re.search('https://mmbiz.qpic.cn/(.*)', img_url).group(1)
                img_name = re.search('.*/(.*)/', img_info, re.S).group(1)
                img_format = re.search('.*=(.*)', img_info, re.S).group(1)
                img = img_name + '.' + img_format
                return img
            elif '?' in img_url:
                # 针对其他图床的?规则
                img = re.search('.*/(.*?)\?', img_url, re.S).group(1)
                return img
            else:
                img = re.search('.*/(.*)', img_url).group(1)
                if '!' in img_url:
                    # 针对!规则
                    img = re.search('(.*)!.*', img, re.S).group(1)
                return img
        else:
            img = re.search('.*/(.*)', img_url).group(1)
            return img

    def get_loc_from_url(self, img_url):
        if 'http' in img_url and '/' in img_url:
            if '!' in img_url:
                return re.search('\..*?/(.*)!', img_url, re.S).group(1)
        else:
            # return re.search('(.*)/',img_url,re.S).group(1)
            return img_url

    def clean_img(self):
        """用于清除文件夹中无用的图片"""
        flag = False
        redundant_list = []
        for file in self.assets_list:
            u_file = quote(file)  # typora中使用了unicode-escape
            if u_file not in self.imgs_list and file not in self.imgs_list:
                redundant_list.append(self.assets_path + '\\' + file)
                flag = True
        if flag:
            for x in redundant_list:
                os.remove(x)
                print(x + " is removed.")
        else:
            print("Scan finished, no redundant img is found in assets.")

    def img_upload(self, img_url='', imgs_url_list='', assets_path='', assets_name=''):
        """用于批量上传图片"""
        print('------uploading process------')
        # 建立远端连接
        url_list = []
        if not img_url and not imgs_url_list:
            url_list = self.imgs_url_list
        if img_url:
            if imgs_url_list:
                print('Error, you can only set img_url or imgs_url_list.')
            url_list.append(img_url)
        if not assets_path:
            assets_path = self.assets_path
        # 设置上传的文件夹名字
        if not assets_name:
            assets_name = re.search('.*\\\(.*)', assets_path, re.S).group(1)
            self.assets_name = assets_name

        # progress_callback为可选参数，用于实现进度条功能
        def percentage(consumed_bytes, total_bytes):
            if total_bytes:
                rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                print('\r{0}% '.format(rate), end='')
                sys.stdout.flush()

        def up(img_path_, remote_img_loc_, img_):
            # 上传过程的函数，使用断点续传
            if not bucket.object_exists(remote_img_loc_):  # 判断远端文件是否存在
                oss2.resumable_upload(bucket,
                                      remote_img_loc_,
                                      img_path_,
                                      multipart_threshold=200 * 1024,
                                      part_size=100 * 1024,
                                      num_threads=3,
                                      progress_callback=percentage)
                print(', ' + img_ + ' is successfully uploaded.')
            else:
                print(img_ + " already exists, ignore it.")

        bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])

        # 上传文件夹计数
        imgs_total = len(url_list)
        imgs_count = 0
        for img_url in url_list:
            img_url = unquote(img_url)
            img = self.get_name_from_url(img_url)
            if self.bucket_domain in img_url:  # 判断是否在图床
                print("\"" + img + "\" is already in remote, no need to upload.")
                # 移动图片在图床中的位置
                if config['re_loc']:
                    remote_img_loc = self.get_loc_from_url(img_url)
                    if bucket.object_exists(remote_img_loc):
                        new_remote_img_loc = self.__concat(self.remote_dir_loc, self.assets_name, img)
                        if remote_img_loc != new_remote_img_loc:
                            self.img_reloc(remote_img_loc, new_remote_img_loc, delete=config['delete_old_remote'])

                imgs_count += 1
                continue
            else:
                # /xxx/xxxx/abc.jpg 格式的路径，不包含根目录
                remote_img_loc = self.__concat(self.remote_dir_loc, assets_name, img)
                if 'http' in img_url and '/' in img_url:
                    # 是网络图片，需要先下载到temp里再上传
                    print('Found web img, re-upload it to Remote.')
                    # img_path 是图片现在存在的路径
                    img_path = self.img_down(img_url)
                    up(img_path, remote_img_loc, img)
                else:
                    if img in self.assets_list:
                        img_path = assets_path + '\\' + img

                        up(img_path, remote_img_loc, img)
                    else:
                        print("Img is not found in .assets, so I can't upload it.")
            imgs_count += 1

        if imgs_count == imgs_total:
            print("All imgs are uploaded.")
            # 清理temp
            if os.path.exists('temp_img/'):
                for a, b, c in os.walk('temp_img/'):
                    for cc in c:
                        os.remove('temp_img/' + cc)
                os.rmdir('temp_img/')
            return True
        else:
            return False

    def img_reloc(self, remote_img_loc, new_remote_img_loc, delete=True):
        """将图床图片移动到合适位置"""
        print('re_loc process:', end='')

        def delete_(remote_img_loc_):
            # delete 指示是否删除旧位置的文件
            if delete:
                if bucket.delete_object(remote_img_loc_):
                    print('deleted "' + self.get_name_from_url(remote_img_loc) + '" in original loc.')
                    return True
                return False
            p_dir = re.search('(.*)/', remote_img_loc_, re.S).group(1)
            if bucket.delete_object(p_dir):
                # 清理掉旧的文件夹
                print('deleted empty loc.')
            return True

        bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])
        exist = bucket.object_exists(new_remote_img_loc)
        if exist:
            return delete_(remote_img_loc)
        else:
            if bucket.copy_object(self.oss_info['Bucket'], remote_img_loc, new_remote_img_loc):
                return delete_(remote_img_loc)
            else:
                return False

    def img_down(self, img_url):
        """将网络上的图片转到图床里"""
        if not os.path.exists('temp_img/'):
            os.mkdir('temp_img/')
        response = requests.get(img_url)
        if response.status_code == 200:
            img_name = self.get_name_from_url(img_url)
            temp_img_path = 'temp_img/' + img_name
            with open(temp_img_path, 'wb') as f:
                f.write(response.content)
            return temp_img_path
        return None

    def replace_img_url(self, remote_dir_loc=''):
        """用于更换文章中的图片地址"""
        print('------replacing urls process------')
        if remote_dir_loc == '':
            remote_dir_loc = self.remote_dir_loc

        # 判断图片是否已在图床中
        imgs_url_list = self.get_imgs_list(force=False, url=True)
        remote_domain_prefix = self.__concat(self.bucket_domain, remote_dir_loc)
        modify_flag = False
        content_o = self.content # 原内容
        content_w = self.content # 微信内容
        for img_url in imgs_url_list:
            img = unquote(self.get_name_from_url(img_url))
            u_img = quote(img)

            # 建立连接
            bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])

            remote_img_loc = self.__concat(remote_dir_loc, self.assets_name, img)
            u_remote_img_loc = self.__concat(remote_dir_loc, quote(self.assets_name), u_img)

            # 判断图片是否在图床中
            exist = bucket.object_exists(remote_img_loc)
            if not exist:
                exist = bucket.object_exists(u_remote_img_loc)

            remote_img_url = self.__concat(remote_domain_prefix, self.assets_name, img)
            u_remote_img_url = self.__concat(remote_domain_prefix, quote(self.assets_name), u_img)

            if remote_img_url in img_url or u_remote_img_url in img_url:
                # 图片url为图床链接，开始判断是否在图床中
                if exist:
                    print(img + " already has remote url, no need to replace.")
                    continue
                # 否则上传图片
                print(img + ' seems not in remote, try to upload it.')
                self.img_upload(img_url)

            # 替换图片url
            if exist:
                remote_img_url = remote_img_url.replace('https://', '')
                duplicate_verify = 'https://' + quote(remote_img_url) + config['style']
                if duplicate_verify not in self.content:
                    self.content = self.content.replace(img_url, 'https://' + quote(remote_img_url) + config['style'])
                    modify_flag = True
                    print("replaced")

        if modify_flag:
            # 备份原文档
            with open(self.article_path + '-' + str(int(time.time())) + '.original', 'w', encoding="UTF-8") as bkup:
                bkup.write(content_o)
            # 开始替换图片url
            with open(self.article_path, 'w', encoding='UTF-8') as f:
                f.write(self.content)
            print('Img urls are successfully replaced.')
        else:
            print('No img url needs to replace.')

        # 为微信公众号做一个特别版
        content_w = self.content.replace(config['style'],config['weixin'])
        with open(self.article_path.replace('.md', '') + '-weixin-edition.md', 'w', encoding="UTF-8") as w:
            w.write(content_w)
        print('Generated weixin-edition.')


if __name__ == '__main__':
    md = ImgMD()
    if config['clean_local_assets']:
        md.clean_img()
    opt = input('upload images? y/n.: ')
    if opt == 'y':
        result = md.img_upload()
    else:
        result = False
    if result:
        md.replace_img_url()
    xx = input('Enter anything to exit.')
    if xx:
        os._exit(0)
