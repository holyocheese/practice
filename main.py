#-*- coding:utf-8 -*-
import os
import urllib
from bs4 import BeautifulSoup as Bs
import sys
import requests
import demjson
from time import ctime
import re
import threading
from time import sleep
from contextlib import closing
import ProcessBar


reload(sys)
sys.setdefaultencoding('utf-8')
# 统一访问session
print os.path
# 连接数
requests.adapters.DEFAULT_RETRIES = 5
se = requests.session()
se.keep_alive = False
# 代理服务器
# se.proxies = {"https://"}
# 变更工作空间
os.chdir(r'G:\pythonproject\srcrap')
path = r'G:\pythonproject\srcrap\img'

class Pixiv(object):
    '''pixiv请求类'''

    def __init__(self, scraptype):
        # 爬取类型
        self.scrap_type = scraptype
        # 主页
        self.indexurl = "https://www.pixiv.net/"
        # 登录请求连接
        self.loginurl = "https://accounts.pixiv.net/api/login?lang=zh"
        # 图片搜索列表
        self.img_list_url = "https://www.pixiv.net/search.php"
        # 作者页
        self.inner_url = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id="
        # 排行榜页面
        self.ranking_url = "https://www.pixiv.net/ranking_area.php?type=detail&no="
        # 请求头
        #self.headers = [
        #    {'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
        #        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
        #                  'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'},#Chrome
        #    {'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
        #        'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us)  '
        #                      'AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'},#safari
        #    {'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
        #        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv,2.0.1) '
        #                      'Gecko/20100101 Firefox/4.0.1'},#firefox
        #]
        # 请求头
        self.headers = {'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}  # Chrome

        # 登录所需数据
        self.logindata = {
            'pixiv_id': 'j8436346@gmail.com',
            'password': '123456',
            'return_to': r"https://www.pixiv.net/",
            'post_key': []
        }
        # 搜索关键词、页数
        self.searchdata = {
            'word': '',
            'order': 'date_d',
            'p': 1,
        }
        # 作者页搜索结果列表
        self.img_list = []
        # 下载连接和标题
        self.down_list = []

    def login(self):
        """模拟登录请求"""
        postkey = self.getpostkey()
        if(postkey == None):
            print "postkey为空！"
            return
        else:
            self.logindata['post_key'] = postkey
        #登录
        try:
            se.post(self.loginurl, data=self.logindata, headers=self.headers)
            print "Login Done!"
        except Exception as e:
            print e

    def get_img_ranking_list(self, no="6"):
        """ 爬取排行榜数据（默认国际排行榜）
            :param :no
            1.北海道/东北
            2.关东
            3.中部
            4.近畿
            5.中国/四国
            6.九州/冲绳
            7.国际
        """
        nodic = {"0": "北海道/东北",
                 "1": "关东",
                 "2": "中部",
                 "3": "近畿",
                 "4": "中国/四国",
                 "5": "九州/冲绳",
                 "6": "国际"
                 }
        html = se.get(self.ranking_url + no)
        bsObj = Bs(html.text, 'lxml')
        href = bsObj.findAll("a",{"class":re.compile("^(work)")})
        # 当前周
        week = bsObj.findAll("span",{"class": "_about"})[0].string
        downloadPath = os.path.join(path, week + nodic.get(no) + u"排行榜")
        for link in href:
            if(link.attrs['href'][0]=='/'):
                self.img_list.append(self.indexurl + link.attrs['href'][1:])
            else:
                self.img_list.append(self.indexurl + link.attrs['href'])
        try:
            # 返回根文件夹
            os.chdir(os.path.dirname(downloadPath))
            os.mkdir(week + nodic.get(no) + u"排行榜")
        except Exception as e:
            pass
        finally:
            os.chdir(downloadPath)
        print "ranking " + week + " are Downloading!"

        # 获取当前页所有图片 （下载）
        for link in self.img_list:
            # 此处要添加代理
            html = se.get(link, headers=self.headers)
            bsObj = Bs(html.text, 'lxml')
            try:
                src = bsObj.find("img", {"class": "original-image"})
                if src:
                    self.down_list.append({"src": src.attrs['data-src'].decode("unicode-escape"),
                                           "title": src.attrs['alt']})
            except AttributeError as e:
                print "NOT Found"
            except Exception as e:
                print e
        for item in self.down_list:
            for key in item:
                print key + ":" + item[key]
        # 开启三个线程下载图片
        self.threading(3)


    def get_img_search_list(self, keyword="10000users", page= 5):
        """按照keyword搜索图片
            返回page页数
            并进行下载"""
        count = 1
        postdata = self.searchdata
        postdata['word'] = keyword
        # 循环获取图片搜索页到目标页数为止
        # 添加进pixiv.inner_url列表
        while count <= page:
            print "Page " +str(count)
            postdata['p'] = count
            searchdata = urllib.urlencode(postdata)
            html = se.get(self.img_list_url+"?"+searchdata, headers=self.headers)
            bsObj = Bs(html.text, 'lxml')
            href = bsObj.findAll("input", {"id": "js-mount-point-search-result-list"})
            if not href:
                print "not from input!"
                href = bsObj.findAll("div", {"id": "js-mount-point-search-result-list"})

            # 获取作品ID拼接跳转连接
            for dataitem in href:
                if 'data-items' in dataitem.attrs:
                    # print dataitem.attrs['data-items'] # 转码会报错
                    toObj = demjson.decode(dataitem.attrs['data-items'])
                    for item in toObj:
                        if item not in self.img_list:
                            self.img_list.append(self.inner_url+item["illustId"])
            downloadPath = os.path.join(path, keyword + "_page" + str(count))
            try:
                #返回根文件夹
                os.chdir(os.path.dirname(downloadPath))
                os.mkdir(keyword + "_page" + str(count))
            except Exception as e:
                pass
            finally:
                os.chdir(downloadPath)
            print "page " + str(count) + " add DONE!"

            # 获取当前页所有图片 （下载）
            for link in self.img_list:
                html = se.get(link, headers=self.headers)
                bsObj = Bs(html.text, 'lxml')
                try:
                    src = bsObj.find("img", {"class": "original-image"})
                    if src:
                        self.down_list.append({"src": src.attrs['data-src'].decode("unicode-escape"),
                                               "title": src.attrs['alt']})
                        filetype = src.attrs['data-src'].split('.')[-1]
                        print src.attrs['alt'] + " is Downloading"
                        content = se.get(src.attrs['data-src'], headers=self.headers)
                        with open(src.attrs['alt'] + '.' + filetype, 'ab') as f:
                            f.write(content.content)
                except AttributeError as e:
                    print "NOT Found"
                except Exception as e:
                    print e
            for item in self.down_list:
                for key in item:
                    print key + ":" + item[key]
            # 页数+1
            count = count + 1
            # 清空图片连接
            self.img_list = []


    def main(self):
        self.login()
        while 1:
            scrap_type = raw_input("""输入数字[1]以关键词爬取数据
输入数字[2]爬取排行榜数据
按[3]退出 : """)
            if scrap_type == "3":
                exit(0)
            if scrap_type == "1":
                word = raw_input("""请输入搜索关键词：""")
                if word == "":
                    print raw_input("请输入关键词")
                    continue
                page = raw_input("""请输入搜索页数（输入错误默认五页，请输入小于10的数字）：""")
                if not page:
                    self.get_img_search_list(keyword=word)
                    continue
                if int(page) > 10:
                    print "请输入小于10的数字"
                    continue
                self.get_img_search_list(word, int(page))
                break
            if scrap_type == "2":
                no = raw_input("""0: "北海道/东北",
1: "关东",
2: "中部",
3: "近畿",
4: "中国/四国",
5: "九州/冲绳",
6: "国际
请输入数字对应排行榜（回车默认选择国际) : 
""")
                if not no:
                    #self.get_img_ranking_list()#获取图片下载路径
                    print "请正确输入!"
                    continue
                elif int(no) < 0 or int(no) > 6:
                    print "请正确输入"
                    continue
                else:
                    self.get_img_ranking_list(no)
                    print "ALL DONE!"
                    break
            else:
                print "请重新输入", 'utf-8'
                continue

    def getpostkey(self):
        """获取登录所需要的postkey"""
        url = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
        try:
            html = se.get(url, headers=self.headers).text
        except Exception as e:
            print "You may need a VPN！"
            print "End!"
            exit(0)
        bsObj = Bs(html, "lxml")
        postkey = bsObj.find('input')['value']
        return postkey

    def threading(self, threadingcount=0):
        """多线程下载图片"""
        print "threading!"
        if self.down_list == 0:
            print "No Img Link"
            return
        if 5 > threadingcount > 0:
            count = 0
            while count < len(self.down_list):
                threads = []
                nloops = range(threadingcount)
                for i in nloops:
                    count = count + 1
                    if count < len(self.down_list):
                        t = threading.Thread(target=self.downloadImg, args=(self.down_list[count]['src'], self.down_list[count]['title'], 2))
                        threads.append(t)
                        print len(threads)
                    else:
                        break
                # 启用线程
                for i in nloops:
                    threads[i].start()
                # 线程锁
                for i in nloops:
                    threads[i].join()
                    # count = count + 3
        elif threadingcount >= 5 or threadingcount < 0:
            self.threading(0)

    # 下载文件（线程）
    def downloadImg(self, src, filename, nsec):
        print filename + "is downloading"
        filetype = src.split('.')[-1]
        # 进度条
        while 1:
            try:
                with closing(se.get(src, headers=self.headers, stream=True)) as response:
                    chunk_size = 128  # 单次请求最大值
                    content_size = int(response.headers['content-length'])  # 内容体总大小
                    progress = ProcessBar.ProgressBar(filename, total=content_size,
                                                      unit="KB", chunk_size=chunk_size, run_status="正在下载",
                                                      fin_status="下载完成")
                    with open(filename + '.' + filetype, 'ab') as f:
                        for data in response.iter_content(chunk_size=chunk_size):
                            f.write(data)
                            progress.refresh(count=len(data))
                break
            except IOError as e:
                print "文件名错误："+e
                break
            except requests.ConnectionError as e:
                print e
                # 请求被拒绝 60秒后重试
                sleep(60)
                continue
        sleep(nsec)

if __name__ == "__main__":
    print """
    *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
    *   `````````   `````````   `         `   `````````   `           ` *
    *   `       `       `         `     `         `        `         `  *
    *   `       `       `           ` `           `         `       `   *
    *   `````````       `           ` `           `          `     `    *
    *   `               `         `     `         `           `   `     *
    *   `           `````````   `         `   `````````         `       *
    *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *   *
    """
    # 标记开始时间
    begintime = ctime()
    print "Scrap starts at " + ctime()
    # 初始化类
    pixiv = Pixiv("0")
    pixiv.main()
    print "Scrap ends at " + ctime() + "Used Time :" + (ctime() - begintime)
