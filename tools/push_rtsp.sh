#!/bin/bash
# 360 Camera -> RTSP Stream for YOLO
# 
# 将解码后的 YUV 流转换为 RTSP 流，供 OpenCV/YOLO 使用
# 
# Usage: ./push_rtsp.sh
# Then in Python: cap = cv2.VideoCapture('rtsp://localhost:8554/live')

cd "$(dirname "$0")/.."

RTSP_PORT=8554

echo "Starting 360 Camera RTSP Server..."
echo ""
echo "RTSP URL: rtsp://localhost:$RTSP_PORT/live"
echo ""
echo "Python 使用方法:"
echo "  import cv2"
echo "  cap = cv2.VideoCapture('rtsp://localhost:$RTSP_PORT/live')"
echo "  ret, frame = cap.read()"
echo ""
echo "按 Ctrl+C 停止"
echo ""

# 使用 ffmpeg 将 YUV 流转换为 RTSP
# 需要安装 ffmpeg 且支持 rtsp
node tools/decoder_service.js 2>/dev/null | \
  ffmpeg -f rawvideo -pixel_format yuv420p -video_size 1920x1080 -framerate 25 -i - \
  -c:v libx264 -preset ultrafast -tune zerolatency -g 25 \
  -f rtsp rtsp://localhost:$RTSP_PORT/live
