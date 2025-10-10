import numpy as np
 
def moving_average(data, window_size):
    """
    移动平均滤波.
    """
    if len(data) < window_size:
        return data  # 数据太少，无法进行滤波
 
    window = np.ones(window_size) / window_size
    smoothed_data = np.convolve(data, window, mode='valid')  # 'valid' 模式确保输出长度正确
    return smoothed_data
 
# 示例使用
azimuth_data = [-77.0, 71.0, -80.0, 65.0, -75.0] # 示例数据
window_size = 3
filtered_azimuth = moving_average(azimuth_data, window_size)
print(filtered_azimuth)


from scipy.signal import medfilt
 
def median_filter(data, kernel_size):
    """
    中值滤波.
    """
    smoothed_data = medfilt(data, kernel_size=kernel_size)
    return smoothed_data
 
# 示例使用
import numpy as np
azimuth_data = np.array([-77.0, 71.0, -80.0, 65.0, -75.0]) # 示例数据
kernel_size = 3  # 必须是奇数
filtered_azimuth = median_filter(azimuth_data, kernel_size)
print(filtered_azimuth)