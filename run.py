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
import shutil
import sys
import time
from urllib.parse import quote, unquote

from datetime import datetime

# 阿里云OSS的SDK
try:
    import oss2
except ModuleNotFoundError:
    print('Oss2 Module not found, try "pip install oss2". ')
    exit(0)

try:
    import requests
except ModuleNotFoundError:
    print('requests Module not found, try "pip install requests".')
    exit(0)

# 配置
# {
#     "test_mode": True,  # 调试模式
#     "date": {"year": "2019",  # 设置文件夹日期，留空默认为本年
#              "month": "1" # 设置文件夹日期，留空默认为本月
#              },
#     "clean_local_assets": True,
#     "main_oss_folder_ref": "blogimg",  # 设置图床文件夹
#     "style": "!xwbp",  # 设置默认上传的图片规则，以后缀!标识
#     "relocate_oss_existing_file": True,  # 对于已在图床中的图片，设置是否需要重新移动整理图片
#     "delete": True  # 对于移动图片，是否删除原位置
# }

with open('config.json') as cfig:
    config = json.load(cfig)


class ImgMD:
    """MD图片处理类"""

    def __init__(self):
        # 与MD文档有关的
        self.article_filepath = None
        self.assets_dirpath = None
        self.content = ""
        # 文档中的图片信息
        self.imgs_list = []
        self.imgs_url_list = []
        # 图片在本地中的存储信息
        self.assets_list = []

        self.get_doc_imgs_list()
        self.get_assets_list()

        self.temp_dir = 'temp_img'

        # 与图床有关的
        with open('danger/oss_info.json') as f:
            self.oss_info = json.load(f)
        self.auth = oss2.Auth(self.oss_info['AccessKeyId'], self.oss_info['AccessKeySecret'])
        self.endpoint = self.oss_info['EndPoint']
        self.bucket_domain = 'https://' + self.oss_info['EndPoint'].replace('https://', self.oss_info['Bucket'] + '.')

        date_format = input('Set date format(YYYY.MM): ') or f"{config['date']['year']}.{config['date']['month']}"
        print(f'date format: {date_format}')
        year, month = date_format.split('.')

        # 设置远端时间文件夹，如/2020/08/的格式
        localtime = time.localtime()
        year = str(localtime.tm_year) if not year else year
        mon = str(localtime.tm_mon) if not month else month
        if int(mon) < 10:
            mon = '0' + str(int(mon))
        self.remote_main_oss_folder_ref = '/'.join([config['main_oss_folder_ref'], year, mon])

    def get_content(self, article_filepath="", force=False):
        """获得文本内容"""
        if self.content and not force:
            return self.content
        else:
            foo = False
            count = 0
            while not foo and count <= 5:
                try:
                    if not config['test_mode']:
                        if not article_filepath:
                            self.article_filepath = input("Input the article path: ").strip('\"')
                            if "\"" in self.article_filepath:
                                self.article_filepath = re.search("\"(.*)\"", self.article_filepath).group(1)
                            article_filepath = self.article_filepath
                    else:
                        article_filepath = self.article_filepath
                    with open(article_filepath, 'r', encoding="UTF-8") as f:
                        self.content = f.read()
                    foo = True
                    return self.content
                except:
                    print("Notice! File is not found or an error occurs, retry.")
                    count += 1
                    if count > 5:
                        exit(0)

    def get_doc_imgs_list(self, url=False, force=False):
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
            img = self.get_filename_from_url(img_url)  # 不支持绝对路径
            imgs_list.append(img)
        if not url:
            print("Done, %s img(s) found in article." % len(imgs_list))
            for i, img in enumerate(imgs_list):
                print(f"{i}: {img}")

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
                    self.assets_dirpath = input("input the imgs path (Leave it empty to use default folder): ")
                    if self.assets_dirpath == '':
                        self.assets_dirpath = self.article_filepath.replace('.md', '.assets')
                for a, b, c in os.walk(self.assets_dirpath):
                    assets_list = c
                    print("Done, %s img(s) found in assets." % len(assets_list))
                    print('As below:')
                    for i, a in enumerate(assets_list):
                        print(f"{i}: {a}")
                    self.assets_list = assets_list
                    return assets_list
                bar = True
            except:
                print(Exception)
                count += 1
                if count > 5:
                    exit(-1)

    def get_filename_from_url(self, img_url):
        if 'http' in img_url and '/' in img_url:
            # 是链接
            if 'https://mmbiz.qpic.cn/' in img_url:
                # 是微信订阅号图片
                img_info = re.search('https://mmbiz.qpic.cn/(.*)', img_url).group(1)
                img_name = re.search('.*/(.*)/', img_info, re.S).group(1)
                img_format = re.search('.*=(.*)', img_info, re.S).group(1)
                img_full_name = img_name + '.' + img_format
                return img_full_name
            elif '?' in img_url:
                # 针对其他图床的?规则
                img_full_name = re.search('.*/(.*?)\?', img_url, re.S).group(1)
                return img_full_name
            else:
                img_full_name = re.search('.*/(.*)', img_url).group(1)
                if '!' in img_url:
                    # 针对!规则
                    img_full_name = re.search('(.*)!.*', img_full_name, re.S).group(1)
                return img_full_name
        else:
            img_full_name = re.search('.*/(.*)', img_url).group(1)
            return img_full_name

    def get_bucket_ref_from_url(self, img_url):
        if 'http' in img_url:
            return re.search('\..*?/(.*)[!]?', img_url, re.S)[1]
        else:
            return img_url

    def clear_local_imgs(self):
        """用于清除文件夹中无用的图片"""
        flag = False
        redundant_list = []
        for file in self.assets_list:
            u_file = quote(file)  # typora中使用了unicode-escape
            if u_file not in self.imgs_list and file not in self.imgs_list:
                redundant_list.append(self.assets_dirpath + '\\' + file)
                flag = True
        if flag:
            for x in redundant_list:
                os.remove(x)
                print(x + " is removed.")
        else:
            print("Scan finished, no redundant img is found in assets.")

    def img_upload(self, img_url='', imgs_url_list='', assets_dirpath='', assets_name=''):
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
        if not assets_dirpath:
            assets_dirpath = self.assets_dirpath
        # 设置上传的文件夹名字
        if not assets_name:
            assets_name = re.search('.*\\\(.*)', assets_dirpath, re.S).group(1)
            self.assets_name = assets_name

        # progress_callback为可选参数，用于实现进度条功能
        def percentage(consumed_bytes, total_bytes):
            if total_bytes:
                rate = int(100 * (float(consumed_bytes) / float(total_bytes)))
                print('\r{0}% '.format(rate), end='')
                sys.stdout.flush()

        def upload(img_path_, remote_img_ref, img_full_filename):
            # 上传过程的函数，使用断点续传
            if not bucket.object_exists(remote_img_ref):  # 判断远端文件是否存在
                oss2.resumable_upload(
                    bucket,
                    remote_img_ref,
                    img_path_,
                    multipart_threshold=200 * 1024,
                    part_size=100 * 1024,
                    num_threads=3,
                    progress_callback=percentage)
                print(', ' + img_full_filename + ' is successfully uploaded.')
            else:
                print(img_full_filename + " already exists, ignore it.")

        bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])

        # 上传文件夹计数
        imgs_total = len(url_list)
        imgs_count = 0
        for img_url in url_list:
            img_url = unquote(img_url)
            img = self.get_filename_from_url(img_url)
            if self.bucket_domain in img_url:  # 判断是否在图床
                print("\"" + img + "\" is already in remote, no need to upload.")
                # 移动图片在图床中的位置
                if config['relocate_oss_existing_file']:
                    remote_img_ref = self.get_bucket_ref_from_url(img_url)
                    if bucket.object_exists(remote_img_ref):
                        new_remote_img_ref = '/'.join([self.remote_main_oss_folder_ref, self.assets_name, img])
                        if remote_img_ref != new_remote_img_ref:
                            self.img_relocate(remote_img_ref, new_remote_img_ref,
                                              delete=config['delete_old_oss_existing_file'])
            else:
                # /xxx/xxxx/abc.jpg 格式的路径，不包含根目录
                remote_img_ref = '/'.join([self.remote_main_oss_folder_ref, assets_name, img])
                if 'http' in img_url and '/' in img_url:
                    # 是网络图片，需要先下载到temp里再上传
                    print('Found web img, re-upload it to Remote.')
                    # img_path 是图片现在存在的路径
                    img_path = self.img_download(img_url)
                    upload(img_path, remote_img_ref, img)
                else:
                    if img in self.assets_list:
                        img_path = assets_dirpath + '\\' + img

                        upload(img_path, remote_img_ref, img)
                    else:
                        print("Img is not found in .assets, so I can't upload it.")
            imgs_count += 1

        if imgs_count == imgs_total:
            print("All imgs are uploaded.")
            # 清理temp
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            return True
        else:
            return False

    def img_relocate(self, remote_img_ref, new_remote_img_ref, delete=True):
        """将图床图片移动到合适位置"""
        print('relocate_oss_existing_file process:', end='')

        def delete_(_remote_img_ref):
            # delete 指示是否删除旧位置的文件
            if delete:
                if bucket.delete_object(_remote_img_ref):
                    print('deleted "' + self.get_filename_from_url(_remote_img_ref) + '" in original loc.')
                    return True
                return False
            p_dir = re.search('(.*)/', _remote_img_ref, re.S).group(1)
            if bucket.delete_object(p_dir):
                # 清理掉旧的文件夹
                print('deleted empty loc.')
            return True

        bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])
        exist = bucket.object_exists(new_remote_img_ref)
        if exist:
            return delete_(remote_img_ref)
        else:
            if bucket.copy_object(self.oss_info['Bucket'], remote_img_ref, new_remote_img_ref):
                return delete_(remote_img_ref)
            else:
                return False

    def img_download(self, img_url):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38'
        }

        """将网络上的图片转到图床里"""
        if not os.path.exists(self.temp_dir):
            os.mkdir(self.temp_dir)
        response = requests.get(img_url, headers=headers)
        if response.status_code == 200:
            img_name = self.get_filename_from_url(img_url)
            temp_img_filepath = '/'.join([self.temp_dir, img_name])
            with open(temp_img_filepath, 'wb') as f:
                f.write(response.content)
            return temp_img_filepath
        else:
            print(f"error: {response.status_code}")
        return None

    def replace_img_url(self, remote_main_oss_folder_ref=''):
        """用于更换文章中的图片地址"""
        print('------replacing urls process------')
        if remote_main_oss_folder_ref == '':
            remote_main_oss_folder_ref = self.remote_main_oss_folder_ref

        # 判断图片是否已在图床中
        imgs_url_list = self.get_doc_imgs_list(url=True, force=False)
        remote_domain_prefix = '/'.join([self.bucket_domain, remote_main_oss_folder_ref])
        modify_flag = False
        content_o = self.content  # 原内容
        content_w = self.content  # 微信内容
        for index, img_url in enumerate(imgs_url_list):
            img_name = unquote(self.get_filename_from_url(img_url))
            u_img_name = quote(img_name).replace("%5C", '/')

            # 建立连接
            bucket = oss2.Bucket(self.auth, self.endpoint, self.oss_info['Bucket'])

            remote_img_ref = '/'.join([remote_main_oss_folder_ref, self.assets_name, img_name])
            u_remote_img_ref = '/'.join([remote_main_oss_folder_ref, quote(self.assets_name), u_img_name])

            # 判断图片是否在图床中
            exist = bucket.object_exists(remote_img_ref)
            if not exist:
                exist = bucket.object_exists(u_remote_img_ref)

            remote_img_url = '/'.join([remote_domain_prefix, self.assets_name, img_name])
            u_remote_img_url = '/'.join([remote_domain_prefix, quote(self.assets_name), u_img_name])

            if remote_img_url in img_url or u_remote_img_url in img_url:
                # 图片url为图床链接，开始判断是否在图床中
                if exist:
                    print(img_name + " already has remote url, no need to replace.")
                    continue
                # 否则上传图片
                print(img_name + ' seems not in remote, try to upload it.')
                self.img_upload(img_url)

            # 替换图片url
            if exist:
                remote_img_url = remote_img_url.replace('https://', '')
                duplicate_verify = 'https://' + quote(remote_img_url) + config['style']
                if duplicate_verify not in self.content:
                    self.content = self.content.replace(img_url, 'https://' + quote(remote_img_url) + config['style'])
                    modify_flag = True
                    print(f"{index}: {img_name} is replaced.")

        if modify_flag:
            # 备份原文档
            original_fn, original_ext = os.path.splitext(self.article_filepath)
            with open(
                    f"{original_fn}'-'{datetime.now().strftime('%Y%m%d%H%M%S')}'-original'{original_ext}",
                    'w',
                    encoding="UTF-8"
            ) as bkup:
                bkup.write(content_o)
            # 开始替换图片url
            with open(self.article_filepath, 'w', encoding='UTF-8') as f:
                f.write(self.content)
            print('Img urls are successfully replaced.')
        else:
            print('No img url needs to replace.')

        # 为微信公众号做一个特别版
        content_w = self.content.replace(config['style'], config['weixin'])
        with open(self.article_filepath.replace('.md', '') + '-weixin-edition.md', 'w', encoding="UTF-8") as w:
            w.write(content_w)
        print('Generated weixin-edition.')


if __name__ == '__main__':
    md = ImgMD()
    if config['clean_local_assets']:
        md.clear_local_imgs()
    opt = input('upload images? y/n.: ')
    if opt.lower() in ['y', 'yes']:
        result = md.img_upload()
    else:
        result = False
    if result:
        md.replace_img_url()
