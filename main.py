import cv2
from time import sleep
from datetime import datetime, timedelta
from sys import exit
import os
# import math

# ===== 配置 =====
START_HOUR, START_MINUTE = 18, 55
END_HOUR, END_MINUTE = 20, 35
CAMERA_INDEX = 0               # 摄像头编号
OUTPUT_FILE = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.avi"  # 输出视频文件
FPS = 30                       # 最终视频帧率
FRAME_WIDTH = 1920             # 试了几个，只有这个能拍全班级
FRAME_HEIGHT = 1080            # 3224 那个不够宽，拍不全
INTERVAL_SECONDS = 1           # 拍摄间隔，单位秒（默认 1 秒拍一帧）
SHOW_TIMESTAMP = True          # 是否显示时间
LOG_FILE = f"logs/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"  # 日志文件
# ================

def get_today_time(hour, minute):
    """返回今天的指定时间 datetime 对象"""
    now = datetime.now()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

def logprint(message, end='\n'):
    """同时输出到控制台和日志文件（追加模式，自动创建文件）"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}", end=end)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message} {end}")

def draw_timestamp(frame, text):
    """
    在图像右上角绘制带时间戳
    背景颜色根据原图亮度自动选择黑底白字或白底黑字
    """
    h, w = frame.shape[:2]
    # 字体设置
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.2
    thickness = 2
    margin = 20  # 边距

    # 计算文本尺寸
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, thickness)

    # 背景框位置（右上角）
    box_x1 = w - text_width - margin * 2
    box_y1 = margin
    box_x2 = w - margin
    box_y2 = margin + text_height + margin

    # 边界保护
    if box_x1 < 0: box_x1 = 0
    if box_y1 < 0: box_y1 = 0
    if box_x2 > w: box_x2 = w
    if box_y2 > h: box_y2 = h

    # 取背景框区域的平均亮度
    roi = frame[box_y1:box_y2, box_x1:box_x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    mean_brightness = cv2.mean(gray)[0]

    # 根据亮度选择颜色：亮背景 -> 黑底白字，暗背景 -> 白底黑字
    if mean_brightness > 128:
        bg_color = (0, 0, 0)      # 黑色背景
        text_color = (255, 255, 255)  # 白色文字
    else:
        bg_color = (255, 255, 255)  # 白色背景
        text_color = (0, 0, 0)      # 黑色文字

    # 创建用于半透明叠加的图层
    overlay = frame.copy()
    # 画实心矩形作为背景
    cv2.rectangle(overlay, (box_x1, box_y1), (box_x2, box_y2), bg_color, -1)
    # 将背景以 0.6 透明度叠加到原图
    alpha = 0.6
    frame[:, :, :] = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # 在背景上居中写文字
    text_x = box_x1 + margin
    text_y = box_y1 + margin + text_height
    cv2.putText(frame, text, (text_x, text_y),
                font, font_scale, text_color, thickness, cv2.LINE_AA)


def main():
    # 确保日志目录存在
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    start_dt = get_today_time(START_HOUR, START_MINUTE)
    end_dt = get_today_time(END_HOUR, END_MINUTE)
    now = datetime.now()

    # 1. 检查时间是否已过
    if now >= end_dt:
        logprint(f"拍摄时间已过（{end_dt.strftime('%H:%M:%S')}），程序退出。")
        exit(0)

    # 2. 如果还没到开始时间，等待
    if now < start_dt:
        wait_seconds = (start_dt - now).total_seconds()
        logprint(f"当前时间 {now.strftime('%H:%M:%S')}，将在 {start_dt.strftime('%H:%M:%S')} 开始。")
        logprint(f"等待 {wait_seconds:.0f} 秒...")
        # 提前 2 秒打开摄像头初始化
        pre_open_time = start_dt - timedelta(seconds=2)
        sleep_time = (pre_open_time - datetime.now()).total_seconds()
        if sleep_time > 0:
            sleep(sleep_time)
    else:
        logprint(f"当前时间已在 {start_dt.strftime('%H:%M:%S')} ~ {end_dt.strftime('%H:%M:%S')} 范围内，立即开始。")

    # 3. 打开摄像头
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        logprint(f"错误：无法打开摄像头（索引 {CAMERA_INDEX}）。")
        exit(1)

    # 设置分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    logprint(f"摄像头分辨率已设为：{actual_w}x{actual_h}")

    # 读取一帧获取尺寸
    ret, frame = cap.read()
    if not ret or frame is None:
        logprint("错误：无法从摄像头读取画面。")
        cap.release()
        exit(1)

    height, width = frame.shape[:2]
    # 定义编码和创建视频写出器
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(OUTPUT_FILE, fourcc, FPS, (width, height))
    if not out.isOpened():
        logprint("错误：无法创建视频文件，请检查编码器或磁盘空间。")
        cap.release()
        exit(1)

    logprint(f"视频尺寸：{width}x{height}，输出文件：{OUTPUT_FILE}")

    # 4. 精确对齐开始时间并拍摄第一帧
    now = datetime.now()
    if now < start_dt:
        # 等待到开始时间
        remaining = (start_dt - datetime.now()).total_seconds()
        if remaining > 0:
            sleep(remaining)
        # 立即抓取第一帧
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            logprint(f"第 1 帧")
        else:
            logprint("警告：开始时刻读取帧失败。")
        next_capture = start_dt + timedelta(seconds=INTERVAL_SECONDS)
    else:
        # 立即拍摄第一帧
        ret, frame = cap.read()
        if ret:
            if SHOW_TIMESTAMP:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    draw_timestamp(frame, now_str)
            out.write(frame)
            logprint(f"第 1 帧")
        else:
            logprint("警告：开始帧读取失败。")
        next_capture = datetime.now() + timedelta(seconds=INTERVAL_SECONDS)

    # 5. 循环拍摄直到结束时间
    frame_count = 1
    try:
        while datetime.now() < end_dt:
            # 等待到下一个拍摄时刻
            sleep_sec = (next_capture - datetime.now()).total_seconds()
            if sleep_sec > 0:
                sleep(sleep_sec)

            # 当前时间可能已超过结束时间，退出
            if datetime.now() >= end_dt:
                break

            ret, frame = cap.read()
            if ret:
                if SHOW_TIMESTAMP:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    draw_timestamp(frame, now_str)
                out.write(frame)
                frame_count += 1
                logprint(f"第 {frame_count} 帧 共 {frame_count/FPS:.2f} 秒")
            else:
                logprint("警告：读取帧失败，跳过。")

            # 下一个预定拍摄时刻（绝对时间，避免累积偏差）
            next_capture += timedelta(seconds=INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logprint("\n用户中断，正在保存已拍摄的视频...")

    finally:
        # 6. 清理资源
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        logprint(f"\n拍摄完成，共 {frame_count} 帧，视频时长约 {frame_count/FPS:.1f} 秒，保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()