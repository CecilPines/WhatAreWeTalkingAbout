import jieba
import jieba.analyse
import pandas
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from GetOutput import get_output_dir, get_project_root


def plot_time_points(comments_time, repost_time):
    # 转成 Python datetime —— 时间格式为：2025-11-08 17:29
    comments_time = pandas.Series(comments_time).reset_index(drop=True)
    repost_time = pandas.Series(repost_time).reset_index(drop=True)

    # 构建 DataFrame 用于绘图
    df_plot = pandas.DataFrame({
        "time": pandas.concat([comments_time, repost_time]),
        "type": ["comments"] * len(comments_time) + ["reposts"] * len(repost_time)
    })

    # 确保时间列是 datetime 类型
    df_plot["time"] = pandas.to_datetime(df_plot["time"], errors='coerce')

    # 设置画布
    plt.figure(figsize=(12, 5))

    # 画散点图
    plt.subplot(131)
    plt.scatter(df_plot[df_plot["type"] == "comments"]["time"],
                [1] * sum(df_plot["type"] == "comments"),
                s=10, label="comment time")
    plt.scatter(df_plot[df_plot["type"] == "reposts"]["time"],
                [2] * sum(df_plot["type"] == "reposts"),
                s=10, label="repost time")
    plt.yticks([1, 2], ["comments", "reposts"])
    plt.xlabel("time")
    plt.title("comments / reposts time plot")
    plt.legend()

    # 绘制柱状图（按小时统计评论和转发数量）
    df_plot["hour"] = df_plot["time"].dt.hour
    hour_count = df_plot.groupby(["hour", "type"]).size().unstack(fill_value=0)

    plt.subplot(132)
    hour_count.plot(kind='bar', stacked=True, ax=plt.gca())
    plt.xlabel("hour of day")
    plt.title("Hourly comments and reposts count")

    # 绘制热力图（时间密度）
    df_plot["minute"] = df_plot["time"].dt.minute
    df_plot["day"] = df_plot["time"].dt.date
    heatmap_data = df_plot.groupby(["day", "hour", "minute", "type"]).size().unstack(fill_value=0)

    plt.subplot(133)
    heatmap_data = heatmap_data.stack().unstack(fill_value=0)  # Prepare for plotting
    plt.imshow(heatmap_data, cmap='hot', interpolation='nearest', aspect='auto')
    plt.title("Time density heatmap")
    plt.xlabel("Time")
    plt.ylabel("Density")

    # 自动调整布局
    plt.tight_layout()

    # 保存图片
    output_path = os.path.join(get_output_dir(), "comment_repost_time_plots.png")
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"已生成时间图表：{output_path}")



"""
从Spidering的爬取结果中获取评论
"""
def get_comments(csv_path):
    df_comments = pandas.read_csv(csv_path, encoding='utf-8')
    df_repost = pandas.read_csv(csv_path, encoding='utf-8')

    comments = df_comments['评论内容']
    comments_time = df_comments['发布时间'].tolist()
    repost_time = df_repost['发布时间'].tolist()
    plot_time_points(comments_time, repost_time)

    with open(os.path.join(get_output_dir(),"comments.txt"), "w", encoding="utf-8") as f:
        for comment in comments:
            f.write(comment + '\n')
    print("1/3 评论合并已完成")
    return

jieba.load_userdict(os.path.join(get_project_root(), "Analyzing", "step1_cut_words", "dict", "SogouLabDic.txt"))
jieba.load_userdict(os.path.join(get_project_root(), "Analyzing", "step1_cut_words", "dict", "dict_baidu_utf8.txt"))
jieba.load_userdict(os.path.join(get_project_root(), "Analyzing", "step1_cut_words", "dict", "dict_pangu.txt"))
jieba.load_userdict(os.path.join(get_project_root(), "Analyzing", "step1_cut_words", "dict", "dict_sougou_utf8.txt"))
jieba.load_userdict(os.path.join(get_project_root(), "Analyzing", "step1_cut_words", "dict", "dict_tencent_utf8.txt"))

def get_data():
    file = os.path.join(get_output_dir(),"comments.txt")
    file2 = os.path.join(get_output_dir(),"comments_cut.dat")
    stopword_path = os.path.join(get_project_root(), "Analyzing", "step1_cut_words", "StopWord.txt")
    stopwords = {}.fromkeys([ line.rstrip() for line in open(stopword_path,'r',encoding='utf-8') ])
    result =[]
    f = open(file,"r", encoding="utf-8", errors="ignore")
    data = f.readlines()
    f.close()
    print(len(data))
    for line in data:
        if not len(line):
            continue
        seg = jieba.cut(line)
        for i in seg:
            if i not in stopwords:
                result.append(i)

        fo = open(file2, "a+",encoding='utf-8')
        for j in result:
           fo.write(j)
           fo.write(' ')
        fo.write('\n')
        result=[]
    fo.close()
    print("2/3 词转换已完成")
    return

"""
从消除停用词后的文本中提取关键词
"""
def extract_key():
    file1 = os.path.join(get_output_dir(),"comments_cut.dat")
    file2 = os.path.join(get_output_dir(),"comments_keyword.dat")
    tfidf = jieba.analyse.extract_tags
    for line in open(file1, encoding="utf-8"):
        if line.strip() == '':
            continue
        text = line
        # tfidf 仅仅从词的统计信息出发，而没有充分考虑词之间的语义信息
        keywords = tfidf(text,
                         allowPOS=('ns', 'nr', 'nt', 'nz', 'nl', 'n', 'vn', 'vd', 'vg', 'v', 'vf', 'a', 'an', 'i'))
        result = []

        for keyword in keywords:
            result.append(keyword)
        # print(result[0])
        fo = open(file2, "a+", encoding="utf-8", errors="ignore")
        for j in result:
            fo.write(j)
            fo.write(' ')
        fo.write('\n')
    fo.close()

    print("3/3 关键词提取已完成")
    return


if __name__ == '__main__':
    csv_path = os.path.join(get_project_root(), "Spidering", "backend", "weibo_analysis", "QcIif0Rd7", "QcIif0Rd7_comments.csv")
    print("1/3 评论合并开始...")
    get_comments(csv_path)
    print("2/3 词转换开始...")
    get_data()
    print("3/3 关键词提取开始...")
    extract_key()

    print("Done!")