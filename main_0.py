import cv2
import time
from datetime import datetime, timedelta
import sys

# ===== 配置 =====
START_HOUR, START_MINUTE = 23, 42
END_HOUR, END_MINUTE = 23, 45
CAMERA_INDEX = 0               # 摄像头编号，通常是 0
OUTPUT_FILE = "timelapse.avi"  # 输出视频文件
FPS = 30                       # 最终视频帧率
FRAME_WIDTH = 3840             # 不出意外是适配广雅希沃
FRAME_HEIGHT = 2160            # 白板摄像头的最高分辨率
# ================

def get_today_time(hour, minute):
    """返回今天的指定时间 datetime 对象"""
    now = datetime.now()
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

def main():
    start_dt = get_today_time(START_HOUR, START_MINUTE)
    end_dt = get_today_time(END_HOUR, END_MINUTE)
    now = datetime.now()

    # 1. 检查时间是否已过
    if now >= end_dt:
        print("拍摄时间已过（20:35），程序退出。")
        sys.exit(0)

    # 2. 如果还没到开始时间，等待
    if now < start_dt:
        wait_seconds = (start_dt - now).total_seconds()
        print(f"当前时间 {now.strftime('%H:%M:%S')}，将在 {start_dt.strftime('%H:%M:%S')} 开始。")
        print(f"等待 {wait_seconds:.0f} 秒...")
        # 提前 2 秒打开摄像头初始化
        pre_open_time = start_dt - timedelta(seconds=2)
        sleep_time = (pre_open_time - datetime.now()).total_seconds()
        if sleep_time > 0:
            time.sleep(sleep_time)
    else:
        print(f"当前时间已在 {start_dt.strftime('%H:%M:%S')} ~ {end_dt.strftime('%H:%M:%S')} 范围内，立即开始。")

    # 3. 打开摄像头
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"错误：无法打开摄像头（索引 {CAMERA_INDEX}）。")
        sys.exit(1)

    # 设置分辨率
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"摄像头分辨率已设为：{actual_w}x{actual_h}")

    # 读取一帧获取尺寸
    ret, frame = cap.read()
    if not ret or frame is None:
        print("错误：无法从摄像头读取画面。")
        cap.release()
        sys.exit(1)

    height, width = frame.shape[:2]
    # 定义编码和创建视频写出器
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(OUTPUT_FILE, fourcc, FPS, (width, height))
    if not out.isOpened():
        print("错误：无法创建视频文件，请检查编码器或磁盘空间。")
        cap.release()
        sys.exit(1)

    print(f"视频尺寸：{width}x{height}，输出文件：{OUTPUT_FILE}")

    # 4. 精确对齐开始时间并拍摄第一帧
    now = datetime.now()
    if now < start_dt:
        # 等待到开始时间
        remaining = (start_dt - datetime.now()).total_seconds()
        if remaining > 0:
            time.sleep(remaining)
        # 立即抓取第一帧
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            print(f"[{start_dt.strftime('%H:%M:%S')}] 第 1 帧")
        else:
            print("警告：开始时刻读取帧失败。")
        next_capture = start_dt + timedelta(seconds=1)
    else:
        # 立即拍摄第一帧
        ret, frame = cap.read()
        if ret:
            out.write(frame)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 第 1 帧")
        else:
            print("警告：开始帧读取失败。")
        next_capture = datetime.now() + timedelta(seconds=1)

    # 5. 循环拍摄直到结束时间
    frame_count = 1
    try:
        while datetime.now() < end_dt:
            # 等待到下一个拍摄时刻
            sleep_sec = (next_capture - datetime.now()).total_seconds()
            if sleep_sec > 0:
                time.sleep(sleep_sec)

            # 当前时间可能已超过结束时间，退出
            if datetime.now() >= end_dt:
                break

            ret, frame = cap.read()
            if ret:
                out.write(frame)
                frame_count += 1
                print(f"[{next_capture.strftime('%H:%M:%S')}] 第 {frame_count} 帧", end='\r')
            else:
                print("警告：读取帧失败，跳过。")

            # 下一个预定拍摄时刻（绝对时间，避免累积偏差）
            next_capture += timedelta(seconds=1)

    except KeyboardInterrupt:
        print("\n用户中断，正在保存已拍摄的视频...")

    finally:
        # 6. 清理资源
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print(f"\n拍摄完成，共 {frame_count} 帧，视频时长约 {frame_count/FPS:.1f} 秒，保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()