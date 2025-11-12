from gc import enable
from unittest import result
import os

import cv2
from Crypto.Util.RFC1751 import binary
from paddleocr import PaddleOCR

# 延迟初始化 OCR 对象
_ocr = None

def get_ocr():
    """获取或创建 OCR 实例（延迟初始化）"""
    global _ocr
    if _ocr is None:
        # 检查自定义模型路径是否存在
        rec_model_dir = "C:/Users/Cecil/.paddlex/official_models/PP-OCRv5_server_rec"
        det_model_dir = "C:/Users/Cecil/.paddlex/official_models/PP-OCRv5_server_det"
        
        # 如果模型目录存在，使用自定义路径；否则使用默认配置让 PaddleOCR 自动下载
        if os.path.exists(rec_model_dir) and os.path.exists(det_model_dir):
            _ocr = PaddleOCR(
                # 基础设置
                # device="gpu",
                # use_tensorrt=True,
                enable_mkldnn=True,
                cpu_threads=2,
                lang="ch",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                text_recognition_model_name="PP-OCRv5_server_rec",
                text_detection_model_name="PP-OCRv5_server_det",
                text_recognition_model_dir=rec_model_dir,
                text_detection_model_dir=det_model_dir,
            )
        else:
            # 使用默认配置，让 PaddleOCR 自动下载模型
            _ocr = PaddleOCR(
                enable_mkldnn=True,
                cpu_threads=2,
                lang="ch",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
    return _ocr

def process_ocr(img_path):
    """gray = cv2.cvtColor(img_path, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    denoised = cv2.medianBlur(binary, 3)
    cv2.imwrite(tmp_output, img_path)"""
    ocr = get_ocr()
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