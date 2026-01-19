
import cv2
import time
import torch
import sys
import platform
import numpy as np
import os
from ultralytics import YOLO

def benchmark_ncnn():
    print("-" * 30)
    print("开始 NCNN 性能测试...")
    
    model_path = 'yolov8n_ncnn_model'
    if not os.path.exists(model_path):
        print(f"错误: 未找到 NCNN 模型目录 '{model_path}'")
        return

    try:
        # Load the NCNN model using Ultralytics
        print(f"正在加载 NCNN 模型: {model_path} ...")
        model = YOLO(model_path, task='detect')
    except Exception as e:
        print(f"加载模型失败: {e}")
        return

    # Create a random image (640x640)
    img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    print("模型加载完成，开始预热...")
    # Warmup
    for _ in range(5):
        model(img, verbose=False)
        
    print("预热完成，开始测试推理速度 (循环 20 次)...")
    
    start_time = time.time()
    count = 20
    for i in range(count):
        results = model(img, verbose=False)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_fps = count / total_time
    avg_latency = (total_time / count) * 1000
    
    print("-" * 30)
    print(f"NCNN 测试结果:")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均 FPS: {avg_fps:.2f}")
    print(f"平均延迟: {avg_latency:.2f} ms")
    print("-" * 30)

if __name__ == "__main__":
    benchmark_ncnn()
