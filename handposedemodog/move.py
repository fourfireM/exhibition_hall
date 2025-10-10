import requests
import json

# 机器狗API接口地址
ROBOT_API_BASE_URL = "http://localhost:18080"  # 替换为真实的API地址
ROBOT_MOVE_ENDPOINT = "/signalservice/robot/move"

# 调用机器狗移动API的函数
def call_robot_move_api(vx, vy, vyaw):
    """
    调用机器狗移动API
    
    参数:
    vx: x方向速度 [-2.5~3.8] (m/s)
    vy: y方向速度 [-1.0~1.0] (m/s)
    vyaw: yaw方向速度 [-4~4] (rad/s)
    
    返回:
    API调用结果
    """
    try:
        url = ROBOT_API_BASE_URL + ROBOT_MOVE_ENDPOINT
        payload = {
            "vx": vx,
            "vy": vy,
            "vyaw": vyaw
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        
        if response.status_code == 200:
            print(f"机器狗移动指令发送成功: vx={vx}, vy={vy}, vyaw={vyaw}")
            return f"指令发送成功: vx={vx}, vy={vy}, vyaw={vyaw}"
        else:
            print(f"API调用失败: {response.status_code}, {response.text}")
            return f"API调用失败: {response.status_code}"
            
    except Exception as e:
        print(f"调用移动API异常: {str(e)}")
        return f"调用异常: {str(e)}"

# 修改后的控制函数 - 使用适当的速度参数
def move_forward():
    """向前移动，使用适当的前向速度"""
    vx = 0.2  # 设置为适中的前向速度
    vy = 0.0  # 无侧向移动
    vyaw = 0.0  # 无旋转
    result = call_robot_move_api(vx, vy, vyaw)
    print(f"move_forward: vx={vx}, vy={vy}, vyaw={vyaw}, result={result}")
    # return result

def move_backward():
    """向后移动，使用适当的后向速度"""
    vx = -0.2  # 设置为适中的后向速度
    vy = 0.0  # 无侧向移动
    vyaw = 0.0  # 无旋转
    result = call_robot_move_api(vx, vy, vyaw)
    print(f"move_backward: vx={vx}, vy={vy}, vyaw={vyaw}, result={result}")
    # return result

def turn_left():
    """向左转，使用适当的旋转速度"""
    vx = 0.0  # 无前后移动
    vy = 0.0  # 无侧向移动
    vyaw = 0.5  # 设置为适中的左转速度
    result = call_robot_move_api(vx, vy, vyaw)
    print(f"turn_left: vx={vx}, vy={vy}, vyaw={vyaw}, result={result}")
    # return result

def turn_right():
    """向右转，使用适当的旋转速度"""
    vx = 0.0  # 无前后移动
    vy = 0.0  # 无侧向移动
    vyaw = -0.5  # 设置为适中的右转速度
    result = call_robot_move_api(vx, vy, vyaw)
    print(f"turn_right: vx={vx}, vy={vy}, vyaw={vyaw}, result={result}")
    # return result

def strafe_left():
    """向左平移，使用适当的侧向速度"""
    vx = 0.0  # 无前后移动
    vy = 0.2  # 设置为适中的左平移速度
    vyaw = 0.0  # 无旋转
    result = call_robot_move_api(vx, vy, vyaw)
    print(f"strafe_left: vx={vx}, vy={vy}, vyaw={vyaw}, result={result}")
    # return result

def strafe_right():
    """向右平移，使用适当的侧向速度"""
    vx = 0.0  # 无前后移动
    vy = -0.2  # 设置为适中的右平移速度
    vyaw = 0.0  # 无旋转
    result = call_robot_move_api(vx, vy, vyaw)        
    print(f"strafe_right: vx={vx}, vy={vy}, vyaw={vyaw}, result={result}")
    # return result

def stop_movement():
    """停止所有移动"""
    vx = 0.0
    vy = 0.0
    vyaw = 0.0
    result = call_robot_move_api(vx, vy, vyaw)
    print(f"stop_movement: vx={vx}, vy={vy}, vyaw={vyaw}, result={result}")
    # return result
