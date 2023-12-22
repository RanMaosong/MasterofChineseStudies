import os
import time
import requests
import shutil
from collections import defaultdict
from bs4 import BeautifulSoup
from tqdm import tqdm
import argparse
import threading


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

URL_ROOT = "http://www.guoxuedashi.net"
PINYIN_URL = "{}/zidian".format(URL_ROOT)


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
        avoid_syms = ["?", ", ", "_", "/", "*", "“", "”", "<", ">", "|"]
        for sym in avoid_syms:
            if sym in path:
                path = path.replace(sym, "")

        with open(path, "wb") as f:
            f.write(r.content)

    r = requests.get(url, headers=headers)
    # print(r.text)

    bs = BeautifulSoup(r.text, "html.parser")

    div = bs.select("div.info_txt2.clearfix")[0]

    # 进度条
    if len(div.select("table")) != 0:
        lis = div.select("table tr")[1].select("td ul li")
        for li in lis:
            word_type = li.contents[0]
            li_spans = li.select("span")
            for li_span in li_spans:
                img_url = li_span.select("img")[0].get("src")
                sub_word_type = li_span.contents[2]

                path_root = os.path.join("pics", "all", word)
                file_posfix = img_url.split(".")[-1]

                download(img_url, path_root, f"{word_type}-{sub_word_type}", file_posfix)
    

    imgs = div.find_all("img")

    for img in imgs:
        parent = img.parent
        if parent.name != "span" or parent.parent.name == "li":
            continue
        img_url = img.get("src")

        sub_word_type = parent.contents[-1]
        path_root = os.path.join("pics", "all", word)
        file_posfix = img_url.split(".")[-1]

        download(img_url, path_root, f"{sub_word_type}", file_posfix)

    r = requests.get(f"http://www.guoxuedashi.net/zixing/zg_ajax.php?zi={word}", headers=headers)
    bs = BeautifulSoup(r.text, "html.parser")
    spans = bs.select("span")
    for span in spans:
        img_url = span.select("img")[0].get("src")
        sub_word_type = span.contents[-1]

        path_root = os.path.join("pics", "all", word)
        file_posfix = img_url.split(".")[-1]

        download(img_url, path_root, f"{sub_word_type}", file_posfix)



def process(words, delay_time):
    crawled_words = []
    if os.path.exists("./pics/all"):
        crawled_words = os.listdir("./pics/all")

    thread_name = threading.current_thread().name
    for word in tqdm(words, desc=thread_name):
        while True:
            try:
                url = get_word_url(word) if word not in crawled_words else None
                break
            except:
                print("Raise exception when geting word url")
                time.sleep(delay_time)
        
        if url is not None:
            url = "{}{}".format(URL_ROOT, url)
            while True:
                try:
                    get_pic(url, word)
                    break
                except Exception as e:
                    path_root = os.path.join("pics", "all", word)
                    if os.path.exists(path_root):
                        shutil.rmtree(path_root)
                    print("\nexception on word: {}".format(word))
                    print(e)
                    time.sleep(delay_time)


def main(args):
    print("================== 获取所有拼音 ============================")
    all_pinyin = get_all_pinyin(PINYIN_URL)

    words = []

    print("================== 获取所有汉字============================")
    for pinyin in tqdm(all_pinyin):
        url = "http://www.guoxuedashi.net{}".format(pinyin)
        cur_words = get_all_words(url)
        words.extend(cur_words)

    words = list(set(words))

    

    print("================== 获取所有字的演变字体图像============================")

    threads = []
    num_thread = args.num_thread
    delay_time = args.delay_time

    step = len(words) // num_thread + 1

    for i in range(0, len(words), step):
        thread = threading.Thread(target=process, args=(words[i:i+step], delay_time), name="Thread-{}".format(i//step))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    print("================== all finished =========================")






if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--num_thread', type=int, default=5, help='number of thread')
    parser.add_argument('--delay_time', type=int, default=20, help='the time delay when raise network exception')

    args = parser.parse_args()

    num_thread = args.num_thread
    delay_time = args.delay_time

    main(args)

    

