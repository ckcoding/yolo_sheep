
import cv2
import numpy as np
from ultralytics import YOLO
import requests

def verify_sheep_detection():
    print("-" * 30)
    print("开始验证羊群检测能力...")

    # 1. 加载模型 (我们依然用之前的 NCNN 模型，因为它也是继承自 yolov8n.pt)
    model_path = 'yolov8n_ncnn_model'
    print(f"正在加载模型: {model_path} ...")
    try:
        model = YOLO(model_path, task='detect')
    except Exception as e:
        print(f"加载模型失败: {e}")
        return

    # 2. 从网络下载一张羊的测试图片
    # 图片来源：一张开源的羊群图片
    img_url = "https://ultralytics.com/images/zidane.jpg" # 先用官方测试图测试人，确保跑通
    # 羊的图片
    img_url_sheep = "https://ultralytics.com/images/zidane.jpg"
    
    print(f"正在下载测试及羊群图片: {img_url_sheep} ...")
    try:
        # 使用 opencv 的 imdecode 直接读取网络流，不保存文件
        resp = requests.get(img_url_sheep, stream=True, timeout=10)
        if resp.status_code == 200:
            arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
            img = cv2.imdecode(arr, -1) # 'Load it as it is'
        else:
            print("图片下载失败，状态码:", resp.status_code)
            return
    except Exception as e:
        print(f"下载出错: {e}")
        return

    print(f"图片下载成功，尺寸: {img.shape[1]}x{img.shape[0]}")
    
    # 3. 进行预测
    print("正在进行推理识别...")
    # conf=0.25 是默认置信度，save=True 会保存结果图到 runs/detect/predictX 目录
    results = model(img, save=True, conf=0.25)

    print("-" * 30)
    print("检测结果:")
    
    found_sheep = False
    for r in results:
        for box in r.boxes:
            # 获取类别 ID 和 名称
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            name = model.names[cls_id] # 获取对应的名字
            
            # 打印每一个检测到的物体
            print(f"--> 发现目标: {name} (ID: {cls_id}), 置信度: {conf:.2f}")

            if name.lower() == 'sheep':
                found_sheep = True

    print("-" * 30)
    if found_sheep:
        print("✅ 成功！模型识别到了 'sheep' (羊)！")
        print(f"结果图片已保存在: {results[0].save_dir}")
    else:
        print("⚠️ 警告：图中未检测到羊。")
        print("可能是图片中羊太小、太模糊，或者模型需要微调。") 

if __name__ == "__main__":
    verify_sheep_detection()
