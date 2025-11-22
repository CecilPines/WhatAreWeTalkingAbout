"""
    demo演示程序：
    加载训练好的模型进行属性级情感分析
    单文本情感分析：针对输入的语句进行单文本情感分析
    批量文本情感分析：Pandas读取Excel文件内容后进行批量情感分析
"""

# 导入所需依赖
import pandas as pd
import paddle
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
os.environ["USE_TORCH"] = "0"
os.environ["DISABLE_DATASETS"] = "1"

from paddlenlp.transformers import SkepTokenizer, SkepModel
from Analyzing.step3_extration_classification.backend.utils.utils import decoding, concate_aspect_and_opinion, format_print
from Analyzing.step3_extration_classification.backend.utils import data_ext, data_cls
from Analyzing.step3_extration_classification.backend.utils.model_define import SkepForTokenClassification, SkepForSequenceClassification
from GetOutput import get_project_root, get_output_dir


# 单条文本情感分析预测函数
def predict(input_text, ext_model, cls_model, tokenizer, ext_id2label, cls_id2label, max_seq_len=512):
    ext_model.eval()
    cls_model.eval()

    # processing input text
    encoded_inputs = tokenizer(list(input_text), is_split_into_words=True, max_seq_len=max_seq_len,)
    input_ids = paddle.to_tensor([encoded_inputs["input_ids"]])
    token_type_ids = paddle.to_tensor([encoded_inputs["token_type_ids"]])

    # extract aspect and opinion words
    logits = ext_model(input_ids, token_type_ids=token_type_ids)
    predictions = logits.argmax(axis=2).numpy()[0]
    tag_seq = [ext_id2label[idx] for idx in predictions][1:-1]
    aps = decoding(input_text, tag_seq)

    # predict sentiment for aspect with cls_model
    results = []
    for ap in aps:
        aspect = ap[0]
        opinion_words = list(set(ap[1:]))
        aspect_text = concate_aspect_and_opinion(input_text, aspect, opinion_words)
        
        encoded_inputs = tokenizer(aspect_text, text_pair=input_text, max_seq_len=max_seq_len, return_length=True)
        input_ids = paddle.to_tensor([encoded_inputs["input_ids"]])
        token_type_ids = paddle.to_tensor([encoded_inputs["token_type_ids"]])

        logits = cls_model(input_ids, token_type_ids=token_type_ids)
        prediction = logits.argmax(axis=1).numpy()[0]

        result = {"aspect": aspect, "opinions": str(opinion_words), "sentiment": cls_id2label[prediction]}
        results.append(result)

    # print results
    format_print(results)

    # 返回预测结果
    return results

# 批量情感分析预测函数
def batchPredict(data, ext_model, cls_model, tokenizer, ext_id2label, cls_id2label, max_seq_len=512):

    ext_model.eval()
    cls_model.eval()

    analysisResults = []

    # 针对批量文本逐条处理
    for input_text in data:
        # processing input text
        encoded_inputs = tokenizer(list(input_text), is_split_into_words=True, max_seq_len=max_seq_len,)
        input_ids = paddle.to_tensor([encoded_inputs["input_ids"]])
        token_type_ids = paddle.to_tensor([encoded_inputs["token_type_ids"]])

        # extract aspect and opinion words
        logits = ext_model(input_ids, token_type_ids=token_type_ids)
        predictions = logits.argmax(axis=2).numpy()[0]
        tag_seq = [ext_id2label[idx] for idx in predictions][1:-1]
        aps = decoding(input_text, tag_seq)

        # predict sentiment for aspect with cls_model
        results = []
        for ap in aps:
            aspect = ap[0]
            opinion_words = list(set(ap[1:]))
            aspect_text = concate_aspect_and_opinion(input_text, aspect, opinion_words)

            encoded_inputs = tokenizer(aspect_text, text_pair=input_text, max_seq_len=max_seq_len, return_length=True)
            input_ids = paddle.to_tensor([encoded_inputs["input_ids"]])
            token_type_ids = paddle.to_tensor([encoded_inputs["token_type_ids"]])

            logits = cls_model(input_ids, token_type_ids=token_type_ids)
            prediction = logits.argmax(axis=1).numpy()[0]

            result = {"属性": aspect, "观点": opinion_words, "情感倾向": cls_id2label[prediction]}
            results.append(result)
        singleResult = {"text": input_text, "result": str(results)}
        analysisResults.append(singleResult)

    # 返回预测结果 list形式
    return analysisResults


def get_predict(target_path_list, name_list, time_list):
    """

    :param target_path: txt文件，每段所需要预测的文字占一行
    :return:
    """
    analysis_path = os.path.join(get_project_root(), "Analyzing", "step3_extration_classification", "backend")
    label_ext_path = os.path.join(analysis_path, "label_ext.dict")  # "./label_ext.dict"
    label_cls_path = os.path.join(analysis_path, "label_cls.dict")  # "./label_cls.dict"
    # 加载PaddleNLP开源的基于全量数据训练好的评论观点抽取模型和属性级情感分类模型
    ext_model_path = os.path.join(analysis_path, "model", "best_ext.pdparams")  # "./model/best_ext.pdparams"
    cls_model_path = os.path.join(analysis_path, "model", "best_cls.pdparams")  # "./model/best_cls.pdparams"

    # load dict
    model_name = "skep_ernie_1.0_large_ch"
    ext_label2id, ext_id2label = data_ext.load_dict(label_ext_path)
    cls_label2id, cls_id2label = data_cls.load_dict(label_cls_path)
    tokenizer = SkepTokenizer.from_pretrained(model_name)
    print("label dict loaded.")

    # load ext model   观点抽取模型
    ext_state_dict = paddle.load(ext_model_path)
    ext_skep = SkepModel.from_pretrained(model_name)
    ext_model = SkepForTokenClassification(ext_skep, num_classes=len(ext_label2id))
    ext_model.load_dict(ext_state_dict)
    print("extraction model loaded.")

    # load cls model   属性级情感分析模型
    cls_state_dict = paddle.load(cls_model_path)
    cls_skep = SkepModel.from_pretrained(model_name)
    cls_model = SkepForSequenceClassification(cls_skep, num_classes=len(cls_label2id))
    cls_model.load_dict(cls_state_dict)
    print("classification model loaded.")

    # 读取txt文件内容进行批量情感分析
    for index in range(len(target_path_list)):
        # 初始化计数器
        positive_count = 0
        negative_count = 0
        other_count = 0
        opinions_list = []
        # 每条评论的情感倾向列表
        emotions_list = []

        target_path = target_path_list[index]
        # 评论发布的时间列表
        time_seq = time_list[index]
        time_seq_list = []
        with open(target_path, "r", encoding="utf-8") as f:
            i = 0
            for line in f:
                input_text = line.strip()
                if not input_text:
                    continue
                print(input_text)
                max_seq_len = 512
                try:
                    # 情感分析预测
                    results = predict(input_text, ext_model, cls_model, tokenizer, ext_id2label, cls_id2label,
                                      max_seq_len=max_seq_len)
                    if results:
                        # 如果返回了预测结果，遍历每个aspect
                        for res in results:
                            sentiment = res.get("sentiment", None)
                            if sentiment == "正向":
                                positive_count += 1
                                emotions_list.append(1)
                            elif sentiment == "负向":
                                negative_count += 1
                                emotions_list.append(-1)
                            else:
                                other_count += 1
                                emotions_list.append(0)
                            time_seq_list.append(time_seq[i])

                            # 收集opinions
                            opinions_str = res.get("opinions", "[]")
                            # opinions是字符串形式的列表，如 "['有趣']"，转成实际列表
                            try:
                                ops = eval(opinions_str)
                                opinions_list.extend(ops)
                            except:
                                pass
                    else:
                        # 没有aspect/opinion返回的情况计为其他
                        other_count += 1
                        emotions_list.append(0)
                        time_seq_list.append(time_seq[i])
                    i += 1
                except Exception as e:
                    print(f"Error in: {input_text} -> {e}")
                    other_count += 1
                    emotions_list.append(0)
                    time_seq_list.append(time_seq[i])
                    i += 1
                    continue

        # 保存opinions
        opinions_file = os.path.join(get_output_dir(), name_list[index]+"_opinions.txt")
        with open(opinions_file, "w", encoding="utf-8") as f:
            for op in opinions_list:
                f.write(op + "\n")
        print(f"Opinions saved to {opinions_file}")

        """绘制情感倾向饼状图"""
        labels = ['Positive', 'Negative', 'Others']
        sizes = [positive_count, negative_count, other_count]
        # colors = ['#ff9999','#66b3ff','#99ff99']
        colors = ['#ff7f0e', '#1f77b4', '#7f7f7f']
        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.title(name_list[index]+"_sentiment_distribution")
        plt.axis('equal')

        # 保存饼图到文件
        pie_path = os.path.join(get_output_dir(), name_list[index]+"_sentiment_distribution.png")
        plt.savefig(pie_path, dpi=300)  # dpi可调，图片清晰度
        print(f"饼图保存到 {pie_path}")

        plt.show()

        print(f"正向: {positive_count}, 负向: {negative_count}, 其他: {other_count}")

        """绘制情感倾向线形图"""
        print(positive_count+negative_count+other_count)
        print(len(time_seq_list))
        print(len(emotions_list))
        plot_emotion_with_distribution(time_seq_list, emotions_list)

    return None


"""绘制评论舆论转折示意图"""
def plot_emotion_with_distribution(time_seq, emotions_list):

    # ---- 构建 DataFrame ----
    df = pd.DataFrame({
        "time": pd.to_datetime(time_seq),
        "emotion": emotions_list
    })

    # 按时间排序
    df = df.sort_values(by="time").reset_index(drop=True)

    # ---- 按时间统计每种情感数量 ----
    df_group = df.groupby(["time", "emotion"]).size().unstack(fill_value=0)
    df_group = df_group.rename(columns={1: "pos", -1: "neg", 0: "neu"})

    # ---- 情感均值，用于折线图 ----
    df_mean = df.groupby("time")["emotion"].mean().reset_index()

    # ---- 设置画布 ----
    fig, ax1 = plt.subplots(figsize=(14, 6))

    # ---- 折线图：情感均值 ----
    ax1.plot(df_mean["time"], df_mean["emotion"], color="black", linewidth=2, label="Emotion Trend")

    # 散点颜色
    color_map = df_mean["emotion"].map({
        1: "orange",
        -1: "blue",
        0: "gray"
    }).fillna("gray")

    ax1.scatter(df_mean["time"], df_mean["emotion"], c=color_map, s=40)

    ax1.set_ylabel("Emotion Value (-1, 0, 1)")
    ax1.set_ylim(-1.2, 1.2)

    # ---- 第二轴：情感数量柱状图 ----
    ax2 = ax1.twinx()

    # 按时间堆叠柱状图
    ax2.bar(df_group.index, df_group["neg"], color="blue", width=0.01, label="Negative")
    ax2.bar(df_group.index, df_group["neu"], bottom=df_group["neg"], color="gray", width=0.01, label="Neutral")
    ax2.bar(df_group.index, df_group["pos"], bottom=df_group["neg"] + df_group["neu"],
            color="orange", width=0.01, label="Positive")

    ax2.set_ylabel("Comment Count")

    # ---- X 轴时间格式 ----
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)

    # ---- 添加图例 ----
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    plt.title("emotion_distribution")

    plt.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()

    # 保存饼图到文件
    pie_path = os.path.join(get_output_dir(), "emotion_distribution.png")
    plt.savefig(pie_path, dpi=300)  # dpi可调，图片清晰度
    print(f"饼图保存到 {pie_path}")

    plt.show()


# ===== 示例 =====
# time_seq = ["2025-11-09 08:05", "2025-11-09 08:05", "2025-11-09 08:06", "2025-11-09 08:10"]
# emotions_list = [1, -1, 0, 1]
# plot_emotion_with_distribution(time_seq, emotions_list)




if __name__== "__main__" :
    from Analyzing.step1_cut_words.test_cut_words import get_comments
    wid = "QcUifa8Oj"
    csv_path = os.path.join(get_project_root(), "Spidering", "backend", "weibo_analysis", wid, wid + "_comments.csv")
    print("3/5 - 1/3 评论合并开始...")
    time_seq = get_comments(csv_path)

    target_path_list = [os.path.join(get_output_dir(), "comments.txt")]  # , os.path.join(get_output_dir(), "weibo.txt")]
    name_list = ["comments"]  # , "weibo"]
    time_list = [time_seq]
    get_predict(target_path_list, name_list, time_list)

    """
    analysis_path = os.path.join(get_project_root(), "Analyzing", "step3_extration_classification", "backend")
    label_ext_path = os.path.join(analysis_path, "label_ext.dict") # "./label_ext.dict"
    label_cls_path = os.path.join(analysis_path, "label_cls.dict") # "./label_cls.dict"
    # 加载PaddleNLP开源的基于全量数据训练好的评论观点抽取模型和属性级情感分类模型
    ext_model_path = os.path.join(analysis_path, "model", "best_ext.pdparams") # "./model/best_ext.pdparams"
    cls_model_path = os.path.join(analysis_path, "model", "best_cls.pdparams") # "./model/best_cls.pdparams"

    # load dict
    model_name = "skep_ernie_1.0_large_ch"
    ext_label2id, ext_id2label = data_ext.load_dict(label_ext_path)
    cls_label2id, cls_id2label = data_cls.load_dict(label_cls_path)
    tokenizer = SkepTokenizer.from_pretrained(model_name)
    print("label dict loaded.")

    # load ext model   观点抽取模型
    ext_state_dict = paddle.load(ext_model_path)
    ext_skep = SkepModel.from_pretrained(model_name)
    ext_model = SkepForTokenClassification(ext_skep, num_classes=len(ext_label2id))    
    ext_model.load_dict(ext_state_dict)
    print("extraction model loaded.")

    # load cls model   属性级情感分析模型
    cls_state_dict = paddle.load(cls_model_path)
    cls_skep = SkepModel.from_pretrained(model_name)
    cls_model = SkepForSequenceClassification(cls_skep, num_classes=len(cls_label2id))    
    cls_model.load_dict(cls_state_dict)
    print("classification model loaded.")

    # 单条文本情感分析
    max_seq_len = 512
    input_text = "可爱的，我现在还喜欢掀被子看我儿子摆的什么睡姿"
    predict(input_text, ext_model, cls_model, tokenizer, ext_id2label, cls_id2label,  max_seq_len=max_seq_len)
    
    input_text = "我尊重我孩子。但是真的觉得自己孩子可爱，时不时想瞅她几眼。"
    predict(input_text, ext_model, cls_model, tokenizer, ext_id2label, cls_id2label,  max_seq_len=max_seq_len)

    
    # 读取Excel文件内容进行批量情感分析
    df = pd.read_excel('./static/测试数据.xlsx', index_col=None)
    # 读取Excel中列名为"text"或"文本"的数据，若无该列名则默认读取第一列数据
    if 'text' in df.columns:
        contents = df['text']
    elif '文本' in df.columns:
        contents = df['文本']
    else: contents = df[df.columns[0]]

    # 批量文本情感分析
    batchResult = batchPredict(contents, ext_model, cls_model, tokenizer, ext_id2label, cls_id2label,  max_seq_len=512)
    print(batchResult)"""






