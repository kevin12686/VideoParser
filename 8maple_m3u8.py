import os
import re
import requests

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
          'Accept-Language': 'zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3',
          'Accept-Encoding': 'gzip, deflate',
          'Referer': '',
          'Connection': 'keep-alive',
          'Upgrade-Insecure-Requests': '1',
          'Pragma': 'no-cache',
          'Cache-Control': 'no-cache'}

buffer_size = 10240
name_re_module = re.compile(r'<title>(?P<name>.+) \| 楓林網</title>')
m3u8_re_module = re.compile(r'php\?url=(?P<url>.+)\.m3u8')
index_re_module = re.compile(r'url:\'(?P<url>.+)\',')
video_re_module = re.compile(r'.*.ts')
video_m3u8_re_module = re.compile(r'.+\.m3u8')
http_re_module = re.compile(r'^http://.*')
ts_re_module = re.compile(r'/(?P<ts_name>[^/]+)\.ts')

page_url = 'http://8maple.ru/'
m3u8_url = 'http://video.8maple.ru/m3u82/?url='

limit_word = '\/:*?"\'><|'


def print_progress_bar():
    bar = ''
    for idx in range(51):
        if idx % 10 == 0:
            bar += '|'
        elif idx % 5 == 0:
            bar += '+'
        else:
            bar += '-'
    print(bar)


if __name__ == '__main__':
    print('請至 {} 尋找影片。'.format(page_url))
    init_session = requests.session()
    video_id = input('影片ID: ')
    page_url += video_id + '/'
    page_result = init_session.get(url=page_url, headers=header)
    header.update(Referer=page_url)
    if '404 未找到' in page_result.text:
        print('** 找無此影片')
    else:
        name = name_re_module.search(string=page_result.text).group('name')
        for word in limit_word:
            if word in name:
                name = name.replace(word, '')
        print('** 正在尋找影集:', name)
        for each in m3u8_re_module.finditer(string=page_result.text):
            index_url = m3u8_url + each.group('url')
            url_result = init_session.get(url=index_url, headers=header)
            search_url = index_re_module.search(string=url_result.text).group('url')
            if '.m3u8' in search_url:
                target_url = search_url[:search_url.index('.m3u8') + 5]
                break
        if target_url is None or index_url is None:
            print('** 下載失敗影片')
        else:
            header.update(Referer=index_url)

            directory = os.path.join(os.path.abspath(os.curdir), name)
            if not os.path.exists(directory):
                os.mkdir(directory)

            flag = True
            while flag:
                m3u8_data = init_session.get(url=target_url, headers=header).content
                ts_list = video_re_module.findall(string=m3u8_data.decode())
                header.update(Referer=target_url)
                if len(ts_list) == 0:
                    m3u8_place = video_m3u8_re_module.search(string=m3u8_data.decode()).group()
                    target_url = target_url.replace('index.m3u8', m3u8_place)
                else:
                    flag = False
            m3u8_file = os.path.join(directory, name + '.m3u8')
            with open(m3u8_file, 'wb') as f:
                f.write(m3u8_data)

            print('** 已抓取m3u8檔案')

            print('** 開始下載影片')
            print_progress_bar()
            ts_dir = os.path.join(directory, 'ts_file')
            if not os.path.exists(ts_dir):
                os.mkdir(ts_dir)
            count = 0
            last_bar = 0
            start = False
            with open(os.path.join(directory, name + '.mp4'), 'ab') as f:
                for line in ts_list:
                    if video_re_module.match(string=line):
                        if not http_re_module.match(string=line):
                            line = target_url.replace('index.m3u8', line)
                        count += 1
                        ts_video_name = ts_re_module.search(string=line).group('ts_name')
                        if not os.path.exists(os.path.join(ts_dir, ts_video_name + '.ts')):
                            data = init_session.get(url=line, headers=header)

                            with open(os.path.join(ts_dir, ts_video_name + '.ts'), 'wb') as ts_f:
                                for ch in data.iter_content(chunk_size=buffer_size):
                                    f.write(ch)
                                    ts_f.write(ch)
                                f.flush()
                        if not start and count > 5:
                            os.startfile(os.path.join(directory, name + '.mp4'))
                            start = True
                        if count * 100 / len(ts_list) - last_bar > 1:
                            print('#', end='')
                            last_bar += 2
        if len(ts_list) > 0:
            print('#')
