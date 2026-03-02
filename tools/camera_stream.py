#!/usr/bin/env python3
"""
360 Camera Frame Provider for YOLO

直接从解码器读取帧，转换为 OpenCV 格式供 YOLO 使用。

Usage:
    from camera_stream import get_frame_generator
    
    for frame in get_frame_generator():
        # frame 是 BGR 格式的 numpy 数组 (1080, 1920, 3)
        results = model(frame)
"""

import subprocess
import numpy as np
import cv2
import os

# 配置
WIDTH = 1920
HEIGHT = 1080
FRAME_SIZE = WIDTH * HEIGHT * 3 // 2  # YUV420P


def yuv420p_to_bgr(yuv_data, width, height):
    """将 YUV420P 数据转换为 BGR 格式"""
    yuv = np.frombuffer(yuv_data, dtype=np.uint8)
    yuv = yuv.reshape((height * 3 // 2, width))
    bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
    return bgr


def get_frame_generator(resize=None):
    """
    生成器：持续产出视频帧
    
    Args:
        resize: 可选，(width, height) 调整输出尺寸，例如 (640, 640) 供 YOLO 使用
    
    Yields:
        numpy.ndarray: BGR 格式的帧 (H, W, 3)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    decoder_path = os.path.join(script_dir, 'decoder_service.js')
    
    print(f"[Camera] Starting decoder...")
    
    proc = subprocess.Popen(
        ['node', decoder_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=FRAME_SIZE * 2
    )
    
    frame_count = 0
    
    try:
        while True:
            raw = proc.stdout.read(FRAME_SIZE)
            if len(raw) < FRAME_SIZE:
                print(f"[Camera] Stream ended after {frame_count} frames")
                break
            
            frame = yuv420p_to_bgr(raw, WIDTH, HEIGHT)
            frame_count += 1
            
            if resize:
                frame = cv2.resize(frame, resize)
            
            if frame_count == 1:
                print(f"[Camera] First frame received: {frame.shape}")
            
            yield frame
            
    except KeyboardInterrupt:
        print(f"\n[Camera] Stopped. Total frames: {frame_count}")
    finally:
        proc.terminate()


def main():
    """测试：显示实时视频"""
    print("360 Camera Stream Test")
    print("Press 'q' to quit")
    
    for frame in get_frame_generator():
        # 缩小显示
        display = cv2.resize(frame, (960, 540))
        cv2.imshow('360 Camera', display)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
