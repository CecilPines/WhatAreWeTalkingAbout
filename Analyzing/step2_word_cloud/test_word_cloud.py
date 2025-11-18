import jieba.analyse
from PIL import Image,ImageSequence
import numpy
import os
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud,ImageColorGenerator
#import matplotlib.mlab as mlab

from GetOutput import get_output_dir, get_project_root


def get_word_cloud():
    font = FontProperties(fname='C:\Windows\Fonts\simhei.ttf')
    bar_width = 0.4
    lyric = ''

    f = open(os.path.join(get_output_dir(), "comments_keyword.dat"), 'r', encoding="utf-8", errors="ignore")

    for i in f:
        lyric += f.read()
    # print(lyric)#自动加+'\n'

    # 考虑了相邻词的语义关系、基于图排序的关键词提取算法TextRank
    result = jieba.analyse.textrank(lyric, topK=60, withWeight=True)

    keywords = dict()
    for i in result:
        keywords[i[0]] = i[1]
    print(keywords)

    image = Image.open(os.path.join(get_project_root(), "Analyzing", "step2_word_cloud", "background.png"))
    graph = numpy.array(image)
    print(graph)
    wc = WordCloud(font_path='C:\Windows\Fonts\simhei.ttf', background_color='White', max_words=50, mask=graph)
    wc.generate_from_frequencies(keywords)
    image_color = ImageColorGenerator(graph)  # 设置背景图像
    plt.imshow(wc)  # 画图
    plt.imshow(wc.recolor(color_func=image_color))  # 根据背景图片着色
    plt.axis("off")  # 不显示坐标轴
    plt.show()
    wc.to_file(os.path.join(get_output_dir(), 'keywords.png'))

    return

if __name__ == '__main__':
    get_word_cloud()