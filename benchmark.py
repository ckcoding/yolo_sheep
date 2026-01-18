import cv2
import time
import torch
import sys
import platform
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("错误: 未找到 'ultralytics' 库。请运行: pip install ultralytics")
    sys.exit(1)

def get_system_info():
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {sys.version}")
    try:
        print(f"PyTorch版本: {torch.__version__}")
        print(f"CUDA可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU设备: {torch.cuda.get_device_name(0)}")
        else:
            print("注意: 未检测到CUDA，将使用CPU进行推理。")
            print("提示: GT710M可能需要较旧的PyTorch版本或难以支持现代CUDA。")
    except Exception as e:
        print(f"获取环境信息时出错: {e}")

def benchmark():
    print("-" * 30)
    print("开始性能测试...")
    
    # 强制使用CPU测试基准，因为低端显卡可能不如CPU或配置困难
    # 如果有GPU，用户可以手动修改代码尝试，或者ultralytics默认会尝试
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"测试运行设备: {device}")

    try:
        # 加载最轻量级的YOLOv8 nano模型
        # 第一次运行会自动下载
        print("正在加载 YOLOv8n 模型 (首次运行会下载模型)...")
        model = YOLO('yolov8n.pt') 
    except Exception as e:
        print(f"加载模型失败: {e}")
        return

    # 创建一个随机图像 (640x640)
    img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
    
    print("模型加载完成，开始预热...")
    # 预热
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
    print(f"测试结果:")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"平均 FPS: {avg_fps:.2f}")
    print(f"平均延迟: {avg_latency:.2f} ms")
    print("-" * 30)
    
    if avg_fps < 1.0:
        print("评价: 性能非常低，不适合实时视频。")
    elif avg_fps < 5.0:
        print("评价: 性能较低，可能会卡顿。建议尝试更小的模型或NCNN加速。")
    elif avg_fps < 15.0:
        print("评价: 性能勉强可用，适合低帧率监控。")
    else:
        print("评价: 性能良好。")

if __name__ == "__main__":
    get_system_info()
    benchmark()
