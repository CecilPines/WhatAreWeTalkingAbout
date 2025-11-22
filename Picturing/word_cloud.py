import re
import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import matplotlib.font_manager as fm
import os
from GetOutput import get_output_dir


# 读取文件内容
def read_analysis_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


# 文本预处理（提取有效词汇）
def preprocess_text(text):
    # 移除特殊符号和标题标记
    text = re.sub(r'#{1,2}\s*', '', text)  # 去除 ## 标题标记
    text = re.sub(r'[：:]\s*', ' ', text)  # 替换冒号为空格
    text = re.sub(r'[^\w\s]', '', text)  # 去除标点符号

    # 使用jieba分词
    words = jieba.cut(text)

    # 过滤停用词和短词
    stopwords = {'的', '等', '与', '及', '了', '是', '为', '中', '和', '在', '有'}
    filtered_words = [
        word for word in words
        if word.strip() and len(word) > 1 and word not in stopwords
    ]

    return ' '.join(filtered_words)


# 生成词云图
def generate_wordcloud(text, output_path='user_analysis_wordcloud.png'):
    # 确保中文显示正常
    font_path = fm.findfont(fm.FontProperties(family=['SimHei', 'WenQuanYi Micro Hei', 'Heiti TC']))

    # 配置词云参数
    wc = WordCloud(
        font_path=font_path,
        width=1200,
        height=800,
        background_color='white',
        max_words=100,
        collocations=False,  # 避免重复词汇
        contour_width=1,
        contour_color='steelblue'
    )

    # 生成词云
    wc.generate(text)

    # 显示词云
    plt.figure(figsize=(12, 8))
    plt.imshow(wc, interpolation='bilinear')
    plt.axis('off')  # 关闭坐标轴
    plt.tight_layout(pad=0)

    # 保存图片
    wc.to_file(output_path)
    print(f"词云图已保存至 {output_path}")
    plt.show()


def get_generated_wordcloud(file_path, output_path):
    # 读取分析文件
    analysis_text = read_analysis_file(file_path)

    # 预处理文本
    processed_text = preprocess_text(analysis_text)

    # 生成词云
    generate_wordcloud(processed_text, output_path)

if __name__ == '__main__':
    file_path_in = os.path.join(get_output_dir(), "overall_user_analysis.txt")
    file_path_out = os.path.join(get_output_dir(), "user_word_cloud.png")

    get_generated_wordcloud(file_path_in, file_path_out)