import numpy as np
from scipy.spatial.transform import Rotation as R
import math
import requests

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
    uwb_azimuth_degrees = uwb_data["azimuth"]

    # !!! 调试： 输出原始方位角
    print("原始 UWB 方位角 (度):", uwb_azimuth_degrees)

    # !!! 重要：确认 UWB 方位角的定义! 是否需要添加偏移角度?
    azimuth_offset_degrees = 0  #  如果UWB定义0度是正前方，则为0, 否则根据UWB的定义修改这个值
    uwb_azimuth_degrees += azimuth_offset_degrees

    uwb_azimuth_radians = np.radians(uwb_azimuth_degrees)

    # !!! 调试： 输出弧度角的数值
    print("转换后的 UWB 方位角 (弧度):", uwb_azimuth_radians)


    # 2. 将 UWB 数据转换为 UWB 坐标系中的笛卡尔坐标
    uwb_x = uwb_distance * np.cos(uwb_azimuth_radians)
    uwb_y = uwb_distance * np.sin(uwb_azimuth_radians)
    uwb_z = 0  # 假设目标点与 UWB 在同一水平面

    uwb_point_robot_frame = np.array([uwb_x, uwb_y, uwb_z])
    # !!! 调试： 输出UWB坐标系下的点
    print("UWB 坐标系下的点:", uwb_point_robot_frame)


    # 3. 构建旋转矩阵
    # 使用 scipy 库，更方便安全
    r = R.from_euler('xyz', [robot_roll, robot_pitch, robot_yaw])  # 注意旋转顺序
    robot_rotation_matrix = r.as_matrix()

    # !!! 调试： 输出旋转矩阵
    print("旋转矩阵:\n", robot_rotation_matrix)


    # 4.  坐标变换
    # 将 UWB 坐标系中的点转换到世界坐标系
    robot_position = np.array([robot_x, robot_y, robot_z])
    target_position_world_frame = np.dot(robot_rotation_matrix, uwb_point_robot_frame) + robot_position

    # !!! 调试： 输出最终结果
    print("机器狗位置:", robot_position)
    print("目标点在世界坐标系中的坐标:", target_position_world_frame)

    return target_position_world_frame


nav_url = "http://localhost:8008"
uwb_url = "http://localhost:18080/signalservice/uwb"

robot_pose = requests.get(nav_url + "/pose").json()
print(robot_pose)
uwb_data = requests.get(uwb_url).json()["data"]
print(uwb_data)

target_pose = calculate_target_pose(robot_pose, uwb_data)
#print("目标点在世界坐标系中的坐标:", target_pose) #调试期间不要使用print

