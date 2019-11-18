import requests
import pandas as pd
import time
import numpy as np
from tqdm import tqdm
import argparse
import os

from bs4 import BeautifulSoup
from janome.tokenizer import Tokenizer
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image

def Crawler(opt, base_url='https://www.uta-net.com'):
    if f'{opt.artist_id}_list.csv' in os.listdir('./output/'):
        print(f'{opt.artist_id}_list.csvが残っていたのでクローリングしません。')
        pass
    else:
        lyrics_df = pd.DataFrame(columns=['歌詞'])
        for page in tqdm(range(1, opt.num_page)):
            print(f"{page}ページ目クローリング開始")
            url = f"{base_url}/artist/{opt.artist_id}/0/{page}/"
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'lxml')
            links = soup.find_all('td', class_='side td1')
            for link in links:
                a = base_url + (link.a.get('href'))

                response = requests.get(a)
                soup = BeautifulSoup(response.text, 'lxml')
                song_lyrics = soup.find('div', itemprop='lyrics')
                song_lyric = song_lyrics.text
                song_lyric = song_lyric.replace('\n', '')
                time.sleep(1)

                tmp_se = pd.DataFrame([song_lyric], index=lyrics_df.columns).T
                lyrics_df = lyrics_df.append(tmp_se)
            print("クローリング終了")
        lyrics_df.to_csv(f'./output/{opt.artist_id}_list.csv', mode='w', encoding='shift_jis')


def Token(opt):
    if f'{opt.artist_id}_wakati_list.txt' in os.listdir('./output/'):
        print(f'{opt.artist_id}_wakati_list.txtが残ってたので分かち書きしません。')
    else:
        df_file = pd.read_csv(f'./output/{opt.artist_id}_list.csv', encoding='shift_jis')
        song_lyrics = df_file['歌詞'].tolist()

        t = Tokenizer()

        results = []

        for s in song_lyrics:
            tokens = t.tokenize(s)

            r = []

            for tok in tokens:
                if tok.base_form == '*':
                    word = tok.surface
                else:
                    word = tok.base_form

                ps = tok.part_of_speech

                hinshi = ps.split(',')[0]

                if hinshi in ['名詞', '動詞', '副詞', '形容詞']:
                    r.append(word)

            rl = (' '.join(r)).strip()
            results.append(rl)
            #余計な文字コードの置き換え
            result = [i.replace('\u3000','') for i in results]

        text_file = f'./output/{opt.artist_id}_wakati_list.txt'
        with open(text_file, 'w', encoding='utf-8') as fp:
            fp.write("\n".join(result))


def Visualize(opt):
    print('画像生成中...')
    text_file = open(f'./output/{opt.artist_id}_wakati_list.txt', encoding='utf-8')
    f = text_file.read()

    fpath = '/Users/t.inoue/Downloads/fonts-japanese-gothic.ttf'

    #無意味そうな単語除去
    with open("./stop_word/stop_word_english.txt", 'r')as eng:
        stop_english = eng.read().splitlines()
    with open("./stop_word/stop_word_japanese.txt", 'r')as jpn:
        stop_japanese = jpn.read().splitlines()
    stop_words = stop_japanese
    stop_words += stop_english

    if opt.base_img:
        img_color = np.array(Image.open(opt.base_img_path))
        wordcloud = WordCloud(background_color='white',
                            mask = img_color,
                            font_path=fpath, width=opt.img_w, height=opt.img_h, stopwords=set(stop_words)).generate(f)
    else:
        wordcloud = WordCloud(background_color='white',
                              font_path=fpath, width=opt.img_w, height=opt.img_h, stopwords=set(stop_words)).generate(f)


    os.makedirs(opt.output, exist_ok=True)
    wordcloud.to_file(f'./{opt.output}/{opt.artist_id}_wordcloud.png')
    print('画像の生成が終わりました。')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='歌詞の特徴を歌詞化')
    parser.add_argument('--artist_id', required=True, help='歌ネットのURLから歌手のIDを参照してください')
    parser.add_argument('--num_page', default=2, help='何ページクローリングするか')
    parser.add_argument('--img_w', default=800, help='出力の画像の幅')
    parser.add_argument('--img_h', default=600, help='出力の画像の高さ')
    parser.add_argument('--output', default='output_image', help='出力画像のパス')
    parser.add_argument('--base_img', action='store_true', help='出力先にしたい画像の有無')
    parser.add_argument('--base_img_path', type=str, help='出力先にしたい画像の有無')


    opt = parser.parse_args()

    Crawler(opt)
    Token(opt)
    Visualize(opt)