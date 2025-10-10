import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
import gradio as gr
import threading
from PIL import Image
import asyncio
import concurrent.futures
from move import (
    move_forward, move_backward, turn_left, turn_right,
    strafe_left, strafe_right, stop_movement
)
import os 
import requests
import ffmpeg

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

class GradioGestureRecognizer:
    def __init__(self):
        # 配置模型路径
        self.model_path = '/home/myb/handposedemodog/gesture_recognizer.task'
        
        # 初始化变量
        self.latest_result = None
        self.latest_timestamp = 0
        self.is_running = False
        self.ffmpeg_process = None
        self.recognizer = None
        self.camera_thread = None
        self.current_frame = None
        self.current_gesture = "无手势"
        self.current_handedness = "未检测到手"
        
        # 视频流参数
        self.width = 640
        self.height = 480
        
        # 性能优化相关
        self.frame_skip_counter = 0
        self.frame_skip_interval = 2  # 每1帧处理一次手势识别，提高响应速度
        self.last_process_time = time.time()
        
        # 机器狗控制相关
        self.robot_control_enabled = False
        self.current_robot_action = "停止"
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.08  # 手势识别冷却时间（秒）进一步减少
        self.min_confidence = 0.5  # 最小置信度阈值
        self.last_action_name = None  # 记录上一个动作，用于快速切换检测
        
        # 异步执行相关
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.pending_actions = set()  # 跟踪正在执行的动作
        
        # RTSP流相关
        rtsp_data = requests.get("http://localhost:18080/signalservice/video/open")
        if os.environ.get("VIDEO_SOURCE") == "unitree":
            self.rtsp_url = rtsp_data.json()["data"]["unitree_rtsp_url"]
            # self.rtsp_url = self.rtsp_url + "?tcp"
        elif os.environ.get("VIDEO_SOURCE") == "realsense":
            self.rtsp_url = rtsp_data.json()["data"]["realsense_rtsp_url"]
        elif os.environ.get("VIDEO_SOURCE") == "orbbec":
            self.rtsp_url = rtsp_data.json()["data"]["orbbec_rtsp_url"]
        else:
            self.rtsp_url = rtsp_data.json()["data"]["lite3_rtsp_url"]
        self.rtsp_reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        
        # 创建手势识别器选项
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        self.options = vision.GestureRecognizerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.LIVE_STREAM,
            result_callback=self.process_result,
            num_hands=1
        )
    
    def process_result(self, result, output_image, timestamp_ms):
        """处理手势识别结果的回调函数"""
        self.latest_result = result
        self.latest_timestamp = timestamp_ms
        
        # 更新手势信息
        gesture_name = None
        confidence = 0.0
        hand_label = None
        
        if result.gestures and result.gestures[0]:
            gesture_name = result.gestures[0][0].category_name
            confidence = result.gestures[0][0].score
            self.current_gesture = f"{gesture_name} ({confidence:.2f})"
        else:
            self.current_gesture = "无手势"
        
        # 更新手性信息
        if result.handedness and result.handedness[0]:
            hand_label = result.handedness[0][0].category_name
            if hand_label == "Left":
                hand_label = "Right"  # 翻转后的左手实际是右手
            elif hand_label == "Right": 
                hand_label = "Left"   # 翻转后的右手实际是左手

            hand_score = result.handedness[0][0].score
            self.current_handedness = f"{hand_label} ({hand_score:.2f})"
        else:
            self.current_handedness = "未检测到手"
        
        # 机器狗控制逻辑
        if gesture_name and confidence > 0:
            robot_action = self.map_gesture_to_robot_action(gesture_name, hand_label, confidence)
            if robot_action:
                action_name, action_func = robot_action
                action_result = self.execute_robot_action(action_name, action_func)
                print(f"机器狗控制: {action_result}")
        # 没有检测到手势时不需要特殊处理，因为已经移除了稳定性检查
    
    def map_gesture_to_robot_action(self, gesture_name, hand_label, confidence):
        """
        将手势映射到机器狗动作
        
        映射规则：
        👆 Pointing_Up（单手向上指）    → 前进
        👇 Thumb_Down（拇指向下）      → 后退  
        ✋ Open_Palm（左手张开）       → 左移
        ✋ Open_Palm（右手张开）       → 右移
        👊 Closed_Fist（左手握拳）     → 左转
        👊 Closed_Fist（右手握拳）     → 右转
        🛑 Victory（V手势）           → 停止
        """
        if not self.robot_control_enabled or confidence < self.min_confidence:
            return None
        
        current_time = time.time()
        
        # 检查冷却时间
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return None
        
        # 手势到动作的映射
        action_map = {
            ("Pointing_Up", None): ("前进", move_forward),
            ("Thumb_Down", None): ("后退", move_backward),
            # ("Open_Palm", "Left"): ("左移", strafe_left),
            # ("Open_Palm", "Right"): ("右移", strafe_right),
            # ("Closed_Fist", "Left"): ("左转", turn_left),
            # ("Closed_Fist", "Right"): ("右转", turn_right),
            ("Open_Palm", "Left"): ("左移", strafe_right),
            ("Open_Palm", "Right"): ("右移", strafe_left),
            ("Closed_Fist", "Left"): ("左转", turn_right),
            ("Closed_Fist", "Right"): ("右转", turn_left),
            ("Victory", None): ("停止", stop_movement),
        }
        
        # 查找匹配的动作
        for (gesture, hand), (action_name, action_func) in action_map.items():
            if gesture_name == gesture and (hand is None or hand_label == hand):
                return action_name, action_func
        
        return None
    
    def execute_robot_action_async(self, action_name, action_func):
        """异步执行机器狗动作的包装函数"""
        try:
            print(f"开始异步执行: {action_name}")
            result = action_func()
            print(f"异步执行完成: {action_name}")
            # 从待执行列表中移除
            self.pending_actions.discard(action_name)
            return result
        except Exception as e:
            print(f"异步执行失败: {action_name}, 错误: {str(e)}")
            self.pending_actions.discard(action_name)
            return f"执行失败: {str(e)}"

    def execute_robot_action(self, action_name, action_func):
        """执行机器狗动作 - 异步非阻塞版本"""
        try:
            current_time = time.time()
            
            # 检查是否已有相同动作在执行中
            if action_name in self.pending_actions:
                return f"执行中: {action_name}"
            
            # 只进行基本的冷却检查，避免过于频繁的相同动作
            time_since_last = current_time - self.last_gesture_time
            
            # 如果是不同的动作，立即执行
            # 如果是相同的动作，检查冷却时间
            if self.last_action_name != action_name or time_since_last >= self.gesture_cooldown:
                # 异步执行动作，不阻塞主线程
                self.pending_actions.add(action_name)
                future = self.executor.submit(self.execute_robot_action_async, action_name, action_func)
                
                # 更新状态（立即更新，不等待执行完成）
                self.current_robot_action = action_name
                self.last_gesture_time = current_time
                self.last_action_name = action_name
                
                print(f"提交机器狗动作: {action_name} (延迟: {time_since_last:.3f}s)")
                return f"执行: {action_name}"
            else:
                # 相同动作在冷却期内
                return f"冷却中: {action_name} ({self.gesture_cooldown - time_since_last:.2f}s)"
            
        except Exception as e:
            print(f"提交机器狗动作失败: {str(e)}")
            return f"提交失败: {str(e)}"
    
    def toggle_robot_control(self):
        """切换机器狗控制状态"""
        self.robot_control_enabled = not self.robot_control_enabled
        if not self.robot_control_enabled:
            # 停用控制时自动停止机器狗
            try:
                stop_movement()
                self.current_robot_action = "停止"
            except:
                pass
        return self.robot_control_enabled
    
    def reconnect_rtsp(self):
        """重连RTSP流"""
        if self.rtsp_reconnect_attempts >= self.max_reconnect_attempts:
            print(f"RTSP重连失败，已达到最大尝试次数 {self.max_reconnect_attempts}")
            return False
        
        self.rtsp_reconnect_attempts += 1
        print(f"尝试重连RTSP流... (第{self.rtsp_reconnect_attempts}次)")
        
        # 终止当前ffmpeg进程
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=3)
            except:
                pass
        
        # 重新连接
        time.sleep(1)  # 等待1秒再重连
        try:
            self.ffmpeg_process = (
                ffmpeg
                .input(self.rtsp_url, rtsp_transport='tcp', fflags="nobuffer", flags="low_delay", strict="experimental")
                .output('pipe:', format='rawvideo', pix_fmt='bgr24')
                .run_async(pipe_stdout=True)
            )
            
            print("RTSP流重连成功")
            self.rtsp_reconnect_attempts = 0  # 重置重连计数
            return True
        except Exception as e:
            print(f"RTSP流重连失败: {e}")
            return False
    
    
    def draw_landmarks_on_image(self, rgb_image, detection_result):
        """在图像上绘制手部关键点"""
        if not detection_result or not detection_result.hand_landmarks:
            return rgb_image
        
        annotated_image = np.copy(rgb_image)
        
        for hand_landmarks in detection_result.hand_landmarks:
            # 将关键点转换为像素坐标
            height, width, _ = annotated_image.shape
            landmark_points = []
            
            for landmark in hand_landmarks:
                x = int(landmark.x * width)
                y = int(landmark.y * height)
                landmark_points.append((x, y))
            
            # 绘制关键点
            for point in landmark_points:
                cv2.circle(annotated_image, point, 3, (0, 255, 0), -1)
            
            # 绘制连接线（手部骨架）
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),  # 拇指
                (0, 5), (5, 6), (6, 7), (7, 8),  # 食指
                (5, 9), (9, 10), (10, 11), (11, 12),  # 中指
                (9, 13), (13, 14), (14, 15), (15, 16),  # 无名指
                (13, 17), (17, 18), (18, 19), (19, 20),  # 小指
                (0, 17)  # 手掌
            ]
            
            for connection in connections:
                if connection[0] < len(landmark_points) and connection[1] < len(landmark_points):
                    cv2.line(annotated_image, landmark_points[connection[0]], 
                            landmark_points[connection[1]], (255, 0, 0), 2)
        
        return annotated_image
    
    def camera_loop(self):
        """摄像头循环处理 - FFmpeg优化版"""
        frame_count = 0
        last_fps_time = time.time()
        
        while self.is_running and self.ffmpeg_process is not None:
            try:
                # 从ffmpeg进程读取原始视频数据
                in_bytes = self.ffmpeg_process.stdout.read(self.width * self.height * 3)
                if not in_bytes:
                    print("RTSP流读取失败，尝试重连...")
                    if self.reconnect_rtsp():
                        continue  # 重连成功，继续循环
                    else:
                        break     # 重连失败，退出循环
                
                # 将字节数据转换为numpy数组
                frame = np.frombuffer(in_bytes, np.uint8).reshape([self.height, self.width, 3])
                frame_count += 1
                
                # 翻转图像，使其像镜子一样
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 帧跳过优化：不是每帧都进行手势识别
                self.frame_skip_counter += 1
                should_process = self.frame_skip_counter >= self.frame_skip_interval
                
                if should_process and self.recognizer:
                    # 创建MediaPipe Image对象
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    
                    # 计算时间戳（毫秒）
                    timestamp_ms = int(time.time() * 1000)
                    
                    # 异步识别手势
                    self.recognizer.recognize_async(mp_image, timestamp_ms)
                    self.frame_skip_counter = 0
                
                # 绘制手部关键点（每帧都绘制，保持视觉连续性）
                if self.latest_result:
                    annotated_frame = self.draw_landmarks_on_image(rgb_frame, self.latest_result)
                    self.current_frame = annotated_frame
                else:
                    self.current_frame = rgb_frame
                
                # 动态FPS监控
                if frame_count % 30 == 0:
                    current_time = time.time()
                    fps = 30 / (current_time - last_fps_time)
                    print(f"RTSP流FPS: {fps:.1f}")
                    last_fps_time = current_time
                
                # 减少睡眠时间，提高响应速度
                time.sleep(0.01)  # 100fps处理速度，但实际受RTSP流限制
                
            except Exception as e:
                print(f"读取视频流出错: {e}")
                if self.reconnect_rtsp():
                    continue
                else:
                    break
    
    def start_recognition(self):
        """开始手势识别"""
        if self.is_running:
            return "手势识别已在运行中", self.current_gesture, self.current_handedness
        
        rtsp_url = self.rtsp_url
        
        # 初始化RTSP流 - 使用FFmpeg优化延迟
        try:
            self.ffmpeg_process = (
                ffmpeg
                .input(rtsp_url, rtsp_transport='tcp', fflags="nobuffer", flags="low_delay", strict="experimental")
                .output('pipe:', format='rawvideo', pix_fmt='bgr24')
                .run_async(pipe_stdout=True)
            )
            print(f"FFmpeg进程已启动，连接到: {rtsp_url}")
        except Exception as e:
            return f"错误: 无法启动FFmpeg进程 {rtsp_url}, 错误: {str(e)}", "无手势", "未检测到手"
        
        # 创建手势识别器
        try:
            self.recognizer = vision.GestureRecognizer.create_from_options(self.options)
            self.is_running = True
            
            # 启动摄像头线程
            self.camera_thread = threading.Thread(target=self.camera_loop)
            self.camera_thread.daemon = True
            self.camera_thread.start()
            
            return f"手势识别已启动 (RTSP流 {rtsp_url})", self.current_gesture, self.current_handedness
            
        except Exception as e:
            self.cleanup()
            return f"启动失败: {str(e)}", "无手势", "未检测到手"
    
    def stop_recognition(self):
        """停止手势识别"""
        if not self.is_running:
            return "手势识别未在运行", "无手势", "未检测到手"
        
        self.cleanup()
        return "手势识别已停止", "无手势", "未检测到手"
    
    def cleanup(self):
        """清理资源"""
        self.is_running = False
        
        if self.camera_thread and self.camera_thread.is_alive():
            self.camera_thread.join(timeout=1.0)
        
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.terminate()
                self.ffmpeg_process.wait(timeout=3)
                print("FFmpeg进程已终止")
            except Exception as e:
                print(f"终止FFmpeg进程时出错: {e}")
            self.ffmpeg_process = None
        
        if self.recognizer:
            self.recognizer.close()
            self.recognizer = None
        
        # 关闭线程池
        if hasattr(self, 'executor'):
            print("正在关闭机器狗控制线程池...")
            self.executor.shutdown(wait=True, timeout=3.0)
        
        self.current_frame = None
        self.latest_result = None
        self.current_gesture = "无手势"
        self.current_handedness = "未检测到手"
    
    def get_current_frame(self):
        """获取当前帧"""
        if self.current_frame is not None:
            # 转换为PIL Image格式供Gradio显示
            return Image.fromarray(self.current_frame)
        else:
            # 返回黑色图像
            black_image = np.zeros((360, 480, 3), dtype=np.uint8)
            return Image.fromarray(black_image)
    
    def get_status_info(self):
        """获取状态信息"""
        return self.current_gesture, self.current_handedness, self.current_robot_action

# 创建全局识别器实例
gesture_recognizer = GradioGestureRecognizer()

def start_recognition():
    """启动识别的包装函数"""
    status, gesture, handedness = gesture_recognizer.start_recognition()
    return status, gesture, handedness

def stop_recognition():
    """停止识别的包装函数"""
    status, gesture, handedness = gesture_recognizer.stop_recognition()
    return status, gesture, handedness

def toggle_robot_control():
    """切换机器狗控制状态的包装函数"""
    enabled = gesture_recognizer.toggle_robot_control()
    status = "机器狗控制已启用" if enabled else "机器狗控制已禁用"
    return status, gesture_recognizer.current_robot_action

def update_display():
    """更新显示的包装函数"""
    frame = gesture_recognizer.get_current_frame()
    gesture, handedness, robot_action = gesture_recognizer.get_status_info()
    return frame, gesture, handedness, robot_action

# 创建Gradio界面
def create_interface():
    with gr.Blocks(title="手势识别", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 🤖 手势识别 + 机器狗控制系统 (FFmpeg版本)
            
            使用FFmpeg优化的低延迟RTSP视频流处理
            
            **支持的手势控制**:
            - 👆 Pointing_Up → 前进
            - 👇 Thumb_Down → 后退  
            - ✋ Open_Palm (左手) → 左移
            - ✋ Open_Palm (右手) → 右移
            - 👊 Closed_Fist (左手) → 左转
            - 👊 Closed_Fist (右手) → 右转
            - ✌️ Victory → 停止
            """
        )
        
        with gr.Row():
            # 左侧：视频显示
            with gr.Column(scale=2):
                video_output = gr.Image(
                    label="📹 摄像头视频流",
                    type="pil",
                    interactive=False,
                    height=600
                )
            
            # 右侧：识别结果和控制
            with gr.Column(scale=1):
                with gr.Group():
                    gr.Markdown("### 🎯 识别结果")
                    
                    gesture_output = gr.Textbox(
                        label="检测到的手势",
                        value="无手势",
                        interactive=False,
                        lines=2
                    )
                    
                    handedness_output = gr.Textbox(
                        label="左手/右手",
                        value="未检测到手",
                        interactive=False,
                        lines=2
                    )
                    
                    robot_action_output = gr.Textbox(
                        label="🐕 机器狗动作",
                        value="停止",
                        interactive=False,
                        lines=2
                    )
                
                with gr.Group():
                    gr.Markdown("### 🎮 控制面板")
                    
                    start_btn = gr.Button(
                        "▶️ 开始识别",
                        variant="primary",
                        size="lg"
                    )
                    
                    stop_btn = gr.Button(
                        "⏹️ 停止识别",
                        variant="secondary",
                        size="lg"
                    )
                    
                    robot_control_btn = gr.Button(
                        "🐕 启用/禁用机器狗控制",
                        variant="secondary",
                        size="lg"
                    )
                    
                    status_output = gr.Textbox(
                        label="系统状态",
                        value="就绪",
                        interactive=False,
                        lines=2
                    )
                    
                    robot_status_output = gr.Textbox(
                        label="🐕 机器狗状态",
                        value="机器狗控制已禁用",
                        interactive=False,
                        lines=2
                    )
        
        # 按钮事件绑定
        start_btn.click(
            fn=start_recognition,
            outputs=[status_output, gesture_output, handedness_output]
        )
        
        stop_btn.click(
            fn=stop_recognition,
            outputs=[status_output, gesture_output, handedness_output]
        )
        
        robot_control_btn.click(
            fn=toggle_robot_control,
            outputs=[robot_status_output, robot_action_output]
        )
        
        # 使用更高频率的定时器更新显示
        timer = gr.Timer(0.03)  # 50ms更新一次，提高流畅度
        timer.tick(
            fn=update_display,
            outputs=[video_output, gesture_output, handedness_output, robot_action_output]
        )
    
    return interface

if __name__ == "__main__":
    # 创建并启动界面
    interface = create_interface()
    
    try:
        # 启动Gradio应用
        interface.launch(
            server_name="127.0.0.1",  # 只允许本地访问
            server_port=7870,         # 端口号            
            debug=False
        )
    except KeyboardInterrupt:
        print("\n正在关闭应用...")
    finally:
        # 清理资源
        gesture_recognizer.cleanup()
        print("应用已关闭")
