from gc import enable
from unittest import result

import cv2
from Crypto.Util.RFC1751 import binary
from paddleocr import PaddleOCR
"""ocr = PaddleOCR(use_angle_cls=True, lang="ch")
img_path = "./test.jpg"
result = ocr.ocr(img_path)
for line in result:
    print(line)"""
ocr = PaddleOCR(
    # 基础设置
    # device="gpu",
    # use_tensorrt=True,
    enable_mkldnn=True,
    cpu_threads=2,

    lang="ch",

    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,

    # 输入优化
    # text_det_limit_type="min",
    # text_det_limit_side_len=640,
    # text_recognition_batch_size=1,
    # text_det_thresh = 0.4,
    # text_det_box_thresh = 0.7,
    # text_det_unclip_ratio = 1.2,

    text_recognition_model_name="PP-OCRv5_server_rec",
    text_detection_model_name="PP-OCRv5_server_det",
    text_recognition_model_dir="C:/Users/Cecil/.paddlex/official_models/PP-OCRv5_server_rec",  # 文本识别模型
    text_detection_model_dir="C:/Users/Cecil/.paddlex/official_models/PP-OCRv5_server_det",  # 文本检测模型

)
def process_ocr(img_path):
    """gray = cv2.cvtColor(img_path, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.medianBlur(binary, 3)
    cv2.imwrite(tmp_output, img_path)"""
    result = ocr.predict(img_path)
    # print(result[0].keys())
    # for line in result[0]["rec_texts"]:
        # print(line)
    return result[0]["rec_texts"]

# process_ocr("./test1.jpg")

"""import cv2
import os

cap = cv2.VideoCapture("./test-video.mp4")
c = 1
timeRate = 1  # 截取视频帧的时间间隔（这里是每隔1秒截取一帧）

img_dir = "./capture_image"
if not os.path.exists(img_dir):
    os.makedirs(img_dir)

while (True):
    ret, frame = cap.read()
    FPS = cap.get(5)
    if ret:
        frameRate = int(FPS) * timeRate  # 因为cap.get(5)获取的帧数不是整数，所以需要取整一下（向下取整用int，四舍五入用round，向上取整需要用math模块的ceil()方法）
        if (c % frameRate == 0):
            print("开始截取视频第：" + str(c) + " 帧")
            # 这里就可以做一些操作了：显示截取的帧图片、保存截取帧到本地
            cv2.imwrite(img_dir + "/" + str(c) + '.jpg', frame)  # 这里是将截取的图像保存在本地
        c += 1
        cv2.waitKey(0)
    else:
        print("所有帧都已经保存完成")
        break
cap.release()

exist = []
for filename in os.listdir(img_dir):
    if filename.endswith(".jpg"):
        img_path = os.path.join(img_dir, filename)
        present = process_ocr(img_path)
        if present != exist[-1]:
            exist.append(present)
print(exist)"""