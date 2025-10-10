import numpy as np
from scipy.spatial.transform import Rotation as R
import math
import requests
from time import sleep
import time


def calculate_target_pose(robot_pose, uwb_data):
    """
    计算目标点在世界坐标系中的位姿。
 
    Args:
        robot_pose (dict): 机器狗的位姿，包含 x, y, z, roll, pitch, yaw。
        uwb_data (dict): UWB 测量数据，包含 dis (距离), azimuth (方位角)。
 
    Returns:
        numpy.ndarray: 目标点在世界坐标系中的坐标 [x, y, z]。
    """
 
    # 1. 从输入数据中提取信息
    robot_x = robot_pose["x"]
    robot_y = robot_pose["y"]
    robot_z = robot_pose["z"]
    robot_roll = robot_pose["roll"]
    robot_pitch = robot_pose["pitch"]
    robot_yaw = robot_pose["yaw"]
 
    uwb_distance = uwb_data["distance"]
    if uwb_distance > 1:
        uwb_distance = uwb_distance - 1


    uwb_azimuth_degrees = uwb_data["azimuth"]
    uwb_azimuth_radians = np.radians(uwb_azimuth_degrees)
 
    # azimuth_offset_degrees = 180  # 正后方为 0 度 => 需要调整180度
    # uwb_azimuth_degrees = uwb_azimuth_degrees + azimuth_offset_degrees
    # # !!! 重要： 检查调整后的角度范围
    # azimuth_after_offset = uwb_azimuth_degrees - 180
 
    # uwb_azimuth_radians = np.radians(azimuth_after_offset)
    uwb_azimuth_radians = np.radians(uwb_azimuth_degrees)

    # !!! 调试： 输出弧度角的数值
    print("转换后的 UWB 方位角 (弧度):", uwb_azimuth_radians)


    # 2. 将 UWB 数据转换为 UWB 坐标系中的笛卡尔坐标
    uwb_x = uwb_distance * np.cos(uwb_azimuth_radians)
    uwb_y = uwb_distance * np.sin(uwb_azimuth_radians)
    uwb_z = 0  # 假设目标点与 UWB 在同一水平面
 
    uwb_point_robot_frame = np.array([uwb_x, uwb_y, uwb_z])
 
 
    # 3. 构建旋转矩阵
    # 使用 scipy 库，更方便安全
    r = R.from_euler('xyz', [robot_roll, robot_pitch, robot_yaw])  # 注意旋转顺序
    robot_rotation_matrix = r.as_matrix()
 
 
 
    # 4.  坐标变换
    # 将 UWB 坐标系中的点转换到世界坐标系
    robot_position = np.array([robot_x, robot_y, robot_z])
    target_position_world_frame = np.dot(robot_rotation_matrix, uwb_point_robot_frame) + robot_position

    target_position_world_frame = {
        "x": target_position_world_frame[0],
        "y": target_position_world_frame[1],
        "z": target_position_world_frame[2],
        "frame_id": "map"
    }
 
    return target_position_world_frame
 


if __name__ == "__main__":
    nav_url = "http://localhost:8008"
    uwb_url = "http://localhost:18080/signalservice/uwb"
    while True:
        robot_pose = requests.get(nav_url + "/pose").json()
        print(robot_pose)


        degree_data_buffer = []
        distance_data_buffer = []
        start_time = time.time()
    
        while time.time() - start_time < 1.0:  # 运行1秒
            new_data = requests.get(uwb_url).json()["data"]
            print(new_data)
            degree = new_data["azimuth"]
            distance = new_data["distance"]
            if degree:
                degree_data_buffer.append(degree)
            if distance:
                distance_data_buffer.append(distance)
            time.sleep(0.01) # 控制获取数据的频率 (例如，每 10 毫秒一次)

        

        print("原始角度数据:", degree_data_buffer)
        print("角度数据数量:", len(degree_data_buffer))
        print("距离原始数据:", distance_data_buffer)
        print("距离数据数量:", len(distance_data_buffer))
        
        # 处理data_buffer: 去掉最高10%和最低10%，计算剩余数据的中位数
        def process_data(data):
            """
            处理角度数据：去掉最高10%和最低10%的数据，返回剩余数据的中位数
            
            Args:
                data (list): 角度数据列表
                
            Returns:
                float: 处理后的中位数角度值
            """
            if len(data) == 0:
                return None
            
            # 排序数据
            sorted_data = sorted(data)
            n = len(sorted_data)
            
            # 计算要去掉的数据数量（10%）
            remove_count = int(n * 0.1)
            
            # 去掉最低10%和最高10%
            if remove_count > 0:
                filtered_data = sorted_data[remove_count:-remove_count]
            else:
                filtered_data = sorted_data
            
            # 如果过滤后没有数据，返回原始数据的中位数
            if len(filtered_data) == 0:
                filtered_data = sorted_data
            
            # 计算中位数
            filtered_n = len(filtered_data)
            if filtered_n % 2 == 0:
                # 偶数个数据，取中间两个数的平均值
                median = (filtered_data[filtered_n//2 - 1] + filtered_data[filtered_n//2]) / 2
            else:
                # 奇数个数据，取中间的数
                median = filtered_data[filtered_n//2]
            
            print(f"去掉最高最低10%后剩余数据数量: {filtered_n}")
            print(f"过滤后的数据范围: {min(filtered_data):.2f} ~ {max(filtered_data):.2f}")
            
            return median
        
        # 处理数据并获取最终角度值
        final_angle = process_data(degree_data_buffer)
        if final_angle is not None:
            print(f"最终角度值（中位数）: {final_angle:.2f}°")
        else:
            print("没有有效的角度数据")
        final_distance = process_data(distance_data_buffer)
        if final_distance is not None:
            print(f"最终距离值（中位数）: {final_distance:.2f}m")
        else:
            print("没有有效的距离数据")

        uwb_data = {
            "azimuth": final_angle,
            "distance": final_distance
        }

        target_pose = calculate_target_pose(robot_pose, uwb_data)
        print("目标点在世界坐标系中的坐标:", target_pose)
        res = requests.post(nav_url + "/goal", json=target_pose)
        print(res.json())
