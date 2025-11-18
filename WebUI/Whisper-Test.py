"""import whisper

model = whisper.load_model("turbo")
result = model.transcribe("./test.wav")
print(result["text"])"""

import whisper
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os


# 界面逻辑
def select_file():
    path = filedialog.askopenfilename(
        title="选择音频文件",
        filetypes=[("音频文件", "*.mp3 *.wav *.m4a *.flac *.aac *.ogg *.wma *.mp4")]
    )
    if path:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, path)


def transcribe_audio():
    audio_path = entry_path.get().strip()
    if not audio_path or not os.path.exists(audio_path):
        messagebox.showerror("错误", "请选择一个有效的音频文件！")
        return

    btn_start.config(state="disabled")
    text_output.delete(1.0, tk.END)
    text_output.insert(tk.END, "正在加载模型，请稍等...\n")

    def run():
        try:
            model = whisper.load_model("base") # whisper.load_model("base")
            text_output.insert(tk.END, "模型加载完成，正在识别...\n")
            result = model.transcribe(audio_path)
            text = result["text"]

            # 输出文本
            text_output.insert(tk.END, "\n识别结果：\n" + text + "\n")

            # 保存txt
            txt_path = os.path.splitext(audio_path)[0] + ".txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)

            text_output.insert(tk.END, f"\n✅ 已保存为：{txt_path}\n")
            messagebox.showinfo("完成", f"识别完成，已保存到：\n{txt_path}")
        except Exception as e:
            messagebox.showerror("错误", str(e))
        finally:
            btn_start.config(state="normal")

    threading.Thread(target=run).start()


# 创建窗口
root = tk.Tk()
root.title("Whisper 音频转文字工具")
root.geometry("600x400")

tk.Label(root, text="音频文件路径：").pack(pady=5)
entry_path = tk.Entry(root, width=60)
entry_path.pack(pady=5)
tk.Button(root, text="浏览...", command=select_file).pack(pady=5)
btn_start = tk.Button(root, text="开始识别", command=transcribe_audio)
btn_start.pack(pady=10)

text_output = tk.Text(root, height=15)
text_output.pack(padx=10, pady=5, fill="both", expand=True)

root.mainloop()