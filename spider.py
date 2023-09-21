import os
import time
import requests
import shutil
from collections import defaultdict
from bs4 import BeautifulSoup
from tqdm import tqdm


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Cookie": "Hm_lvt_1e7477a020c530bede1b4ea19a1e4c2b=1695264222; Hm_lvt_f360f57688a7b531f5ec75f46a7d0a1a=1695264222; Hm_lpvt_f360f57688a7b531f5ec75f46a7d0a1a=1695264389; Hm_lpvt_1e7477a020c530bede1b4ea19a1e4c2b=1695264389",
    "Host": "www.guoxuedashi.net",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
    "Upgrade-Insecure-Requests": "1"

}


def get_all_pinyin(url):
    r = requests.get(url, headers=headers)
    bs = BeautifulSoup(r.text, "html.parser")

    all_pinyin = []

    nodes = bs.select("table.table2")[0].select("td a")
    for node in nodes:
        all_pinyin.append(node.get("href"))
    
    return all_pinyin


def get_all_words(url):
    try:
        r = requests.get(url, headers=headers)
    except:
        time.sleep(2)
        r = requests.get(url, headers=headers)
    bs = BeautifulSoup(r.text, "html.parser")

    words = []

    nodes = bs.select("table.table2")[0].select("td a")
    for node in nodes:
        words.append(node.text)

    return words


def get_word_url(word):
    url = "http://www.guoxuedashi.net/zixing/yanbian/?ybz={}".format(word)
    r = requests.get(url, headers=headers)

    bs = BeautifulSoup(r.text, "html.parser")

    if len(bs.select("dd.dd3 a")) != 0:
        href = bs.select("dd.dd3 a")[0].get("href")
        return href

    return None

def get_pic(url, word):

    def download(url, path_root, word_type, file_posfix):
        # time.sleep(0.5)
        if not os.path.exists(path_root):
            os.makedirs(path_root)
        path = os.path.join(path_root, "{}.{}".format(word_type, file_posfix))
        r = requests.get(url)
        with open(path, "wb") as f:
            f.write(r.content)

    r = requests.get(url, headers=headers)
    # print(r.text)

    bs = BeautifulSoup(r.text, "html.parser")

    div = bs.select("div.info_txt2.clearfix")[0]

    if len(div.select("table")) == 0:
        # 没有进度条的
        spans = div.select("div.info_txt2.clearfix >span")
        for span in spans:
            word_type = span.contents[-1]
            img_url = span.select("img")[0].get("src")

            path_root = os.path.join("pics", "no_progress", word)
            file_posfix = img_url.split(".")[-1]
            download(img_url, path_root, word_type, file_posfix)

    else:
        lis = div.select("table tr")[1].select("td ul li")
        for li in lis:
            word_type = li.contents[0]

            img_url = li.select("span img")[0].get("src")


            path_root = os.path.join("pics", "progress", word)
            file_posfix = img_url.split(".")[-1]

            download(img_url, path_root, word_type, file_posfix)

URL_ROOT = "http://www.guoxuedashi.net"
PINYIN_URL = "{}/zidian".format(URL_ROOT)

print("================== 获取所有拼音 ============================")
all_pinyin = get_all_pinyin(PINYIN_URL)

words = []

print("================== 获取所有汉字============================")
for pinyin in tqdm(all_pinyin):
    url = "http://www.guoxuedashi.net{}".format(pinyin)
    cur_words = get_all_words(url)
    words.extend(cur_words)

words = set(words)


print("================== 获取所有字的演变字体图像============================")
for word in tqdm(words):
    url = get_word_url(word)
    
    if url is not None:
        url = "{}{}".format(URL_ROOT, url)
        try:
            get_pic(url, word)
        except:
            path_root = os.path.join("pics", "no_progress", word)
            if not os.path.exists(path_root):
                path_root = os.path.join("pics", "progress", word)
            shutil.rmtree(path_root)
    time.sleep(0.5)

# print("================== 获取所有图像 ============================")
# for word, url in tqdm(word_to_url.items()):
#     try:
#         get_pic(url, word)
#     except:
#         path_root = os.path.join("pics", "no_progress", word)
#         if not os.path.exists(path_root):
#             path_root = os.path.join("pics", "progress", word)
#         shutil.rmtree(path_root)
