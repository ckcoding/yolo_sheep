
import cv2
import numpy as np
from ultralytics import YOLO
import time

def is_point_in_polygon(point, polygon):
    """
    判断点是否在多边形内
    point: (x, y)
    polygon: NumPy array of points [[x,y], [x,y], ...]
    """
    # cv2.pointPolygonTest 返回值：
    # >0: 内部
    # =0: 边界上
    # <0: 外部
    result = cv2.pointPolygonTest(polygon, point, False)
    return result >= 0

def main():
    # 1. 加载 NCNN 模型 (确保使用的是导出的 ncnn 模型目录)
    model_path = 'yolov8n_ncnn_model' 
    print(f"正在加载模型: {model_path} ...")
    try:
        model = YOLO(model_path, task='detect')
    except Exception as e:
        print(f"模型加载失败，请检查是否已运行导出命令。错误: {e}")
        return

    # 2. 打开视频流 (0 代表第一个摄像头，也可以是视频文件路径 'video.mp4')
    # 如果您没有摄像头，可以先传一个视频文件上去测试
    video_source = 0 
    # video_source = "sheep_video.mp4" # 如果有视频文件测试请取消注释并修改
    
    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"无法打开视频源: {video_source}")
        return

    # 获取视频尺寸
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"视频分辨率: {width}x{height}")

    # 3. 定义电子围栏区域 (这里简单定义为一个梯形/矩形，实际部署需根据摄像头画面修改坐标)
    # 坐标格式: [x, y]
    # 假设画面中间大块区域是安全的
    margin = 50
    fence_polygon = np.array([
        [margin, margin],                  # 左上
        [width - margin, margin],          # 右上
        [width - margin, height - margin], # 右下
        [margin, height - margin]          # 左下
    ], np.int32)
    fence_polygon = fence_polygon.reshape((-1, 1, 2))

    # 羊在 COCO 数据集中的类别 ID 是 18
    TARGET_CLASS_ID = 18 
    TARGET_LABEL = "Sheep"

    print("开始监控。按 'q' 键退出。")

    while True:
        start_time = time.time()
        
        # 读取一帧
        ret, frame = cap.read()
        if not ret:
            print("视频流结束或无法读取。")
            break

        # 4. 推理
        # verbose=False 不打印多余日志
        # imgsz=640 标准大小
        results = model(frame, verbose=False, imgsz=640)

        # 绘制围栏 (绿色)
        cv2.polylines(frame, [fence_polygon], True, (0, 255, 0), 2)
        cv2.putText(frame, "Safe Zone", (margin, margin-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        alarm_triggered = False

        # 5. 处理检测结果
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 获取类别 ID
                cls_id = int(box.cls[0])
                
                # 只处理“羊”
                # 在测试阶段，如果您身边没有羊，可以把这里临时改成 0 (检测人) 来模拟测试
                # if cls_id == 0:  # 测试用：检测人
                if cls_id == TARGET_CLASS_ID:
                    # 获取坐标 (x1, y1, x2, y2)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    # 计算“落脚点” (通常取底部中心点作为物体的位置)
                    foot_x = int((x1 + x2) / 2)
                    foot_y = int(y2) 

                    # 6. 判断是否在围栏内
                    is_safe = is_point_in_polygon((foot_x, foot_y), fence_polygon)

                    # 绘制
                    color = (0, 255, 0) if is_safe else (0, 0, 255) # 绿(安全) / 红(越界)
                    status_text = "Safe" if is_safe else "WARNING!"
                    
                    if not is_safe:
                        alarm_triggered = True

                    # 画框
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    # 画落脚点
                    cv2.circle(frame, (foot_x, foot_y), 5, color, -1)
                    # 标签
                    label = f"{TARGET_LABEL} {status_text}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # 整体报警提示
        if alarm_triggered:
            cv2.putText(frame, "ALARM: SHEEP OUTSIDE FENCE!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        #一直跑会卡死，如果是服务器环境(无显示器)，注释掉下面这几行
        #并改写成保存图片或者发送日志
        # cv2.imshow("Sheep Fence Monitor", frame)
        
        # 计算 FPS (仅供参考)
        process_time = time.time() - start_time
        fps = 1.0 / (process_time + 1e-6)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        # 按 'q' 退出
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #    break
        
        # 简单输出日志代替显示
        if alarm_triggered:
            print(f"[{time.strftime('%H:%M:%S')}] 警告：发现羊群越界！")
        else:
             # 为了避免刷屏，可以注释掉安全时的日志
             # print(f"[{time.strftime('%H:%M:%S')}] 监控正常 ({fps:.1f} FPS)")
             pass
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
