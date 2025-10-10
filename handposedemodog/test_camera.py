import cv2

def test_all_cameras():
    """测试所有可用摄像头"""
    print("正在检测可用摄像头...")
    available_cameras = []
    
    # 检测前10个可能的摄像头索引
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_cameras.append(i)
                # 获取摄像头信息
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(cap.get(cv2.CAP_PROP_FPS))
                print(f"摄像头 {i}: 分辨率 {width}x{height}, 帧率 {fps}fps")
            cap.release()
    
    if not available_cameras:
        print("未检测到任何可用摄像头")
        return
    
    print(f"\n检测到 {len(available_cameras)} 个摄像头")
    print("按数字键选择要测试的摄像头，按 'q' 退出")
    
    for camera_id in available_cameras:
        print(f"\n正在测试摄像头 {camera_id}...")
        test_single_camera(camera_id)

def test_single_camera(camera_id):
    """测试单个摄像头"""
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"无法打开摄像头 {camera_id}")
        return
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    print(f"摄像头 {camera_id} 测试中... 按 'q' 退出，按 'n' 测试下一个摄像头")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头画面")
            break
        
        # 翻转图像，使其像镜子一样
        frame = cv2.flip(frame, 1)
        
        # 添加信息文本
        cv2.putText(frame, f"Camera {camera_id} Test", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, "Press 'q' to quit, 'n' for next camera", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Resolution: {frame.shape[1]}x{frame.shape[0]}", 
                   (10, frame.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.imshow(f'Camera {camera_id} Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            exit()
        elif key == ord('n'):
            break
    
    cap.release()
    cv2.destroyWindow(f'Camera {camera_id} Test')

if __name__ == "__main__":
    print("=== 摄像头测试工具 ===")
    print("这个工具会依次测试所有检测到的摄像头")
    print("外接摄像头通常编号为 1 或更高数字")
    print("内置摄像头通常编号为 0")
    print()
    
    test_all_cameras()
    
    print("\n测试完成！")
