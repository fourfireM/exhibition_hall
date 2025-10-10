# 机器狗的sdk服务算法API文档

## 概述

本文档描述了机器狗的sdk服务中供算法使用的API接口。所有接口都通过HTTP协议提供，仅支持JSON格式的请求和响应。

## 基础信息

- **服务地址**: `http://localhost:18080`
- **请求格式**: JSON
- **响应格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

所有API响应都遵循以下格式：

```json
{
    "code": "0",
    "message": "success",
    "data": {}
}
```

### 响应码说明


| 响应码 | 说明 |
| ------ | ---- |
| 0      | 成功 |
| 其他   | 错误 |

## API接口列表

### 1. 机器人移动控制

**接口地址**: `POST /signalservice/robot/move`

**功能描述**: 控制机器人移动

**请求参数**:

```json
{
    "vx": 0.5,    // 前后移动速度 (m/s), 不同机器狗支持的范围不同，如宇树是[-2.5,3],而云深处是[-1,1],如果超出上下限会约束到上下限
    "vy": 0.0,    // 左右移动速度 (m/s), 不同机器狗支持的范围不同,如果超出上下限会约束到上下限
    "vyaw": 0.0   // 旋转速度 (rad/s), 不同机器狗支持的范围不同,如果超出上下限会约束到上下限
}
```

**响应示例**:

```json
{
    "code": "0",
    "message": "success",
    "data": null
}
```

**错误响应**:

```json
{
    "code": "1003",
    "message": "move failed, error code: -1"
}
```

### 2. 机器人命令控制

**接口地址**: `POST /signalservice/robot/cmd`

**功能描述**: 执行机器人预设命令

宇树的蹲下和站起是独立实现

云深处的蹲下和站起实现是相同的，也就是当前如果是蹲下它就会起立，如果是站立状态它就会蹲下，调用时需要注意

**请求参数**:

```json
{
    "cmd": "1"  // 命令类型: 1=蹲下, 2=站起, 3=停止移动, 4=回零
}
```

**响应示例**:

```json
{
    "code": "0",
    "message": "success",
    "data": null
}
```

### 3. 获取点云数据

**接口地址**: `GET /signalservice/robot/point_cloud`

**功能描述**: 获取机器人最新的点云数据，云深处不支持此接口

**请求参数**: 无

**响应示例**:

```json
{
    "code": "0",
    "message": "success",
    "data": {
        "stamp": "1640995200.123456789",
        "frame_id": "base_link",
        "height": 480,
        "width": 640,
        "fields": [
            {
                "name": "x",
                "offset": 0,
                "datatype": 7,
                "count": 1
            },
            {
                "name": "y", 
                "offset": 4,
                "datatype": 7,
                "count": 1
            },
            {
                "name": "z",
                "offset": 8,
                "datatype": 7,
                "count": 1
            }
        ],
        "is_bigendian": false,
        "point_step": 12,
        "row_step": 7680,
        "data": "实际的点云数据, size=row_step*height",
        "is_dense": true
    }
}
```

### 4. 获取高度图数据

**接口地址**: `GET /signalservice/robot/height_map`

**功能描述**: 获取机器人最新的高度图数据

**请求参数**: 无

**响应示例**:

```json
{
    "code": "0",
    "message": "success", 
    "data": {
        "stamp": "1640995200.123456789",
        "frame_id": "odom",
        "resolution": 0.05,
        "width": 128,
        "height": 128,
        "origin": [0.0, 0.0, 0.0],
        "data": "高度图数据"
    }
}
```

### 5. 机器狗抓图

**接口地址**: `GET /signalservice/robot/snapshot`

**功能描述**: 获取机器狗自带的摄像头抓图

**请求参数**: 无

**响应示例**:

```json
{
    "code": "0",
    "message": "success",
    "data": {
        "rgb_jpg": "JPEG文件raw数据",
        "stamp": "1640995200000000000"
    }
}
```

### 6. 获取彩色深度图

**接口地址**: `GET /signalservice/video/color_depth_snapshot`

**功能描述**: 获取外接相机的对齐的彩色和深度图像

**请求参数**: 无

**响应示例**:

```json
{
    "code": "0",
    "message": "success",
    "data": {
        "timestamp": 1640995200000,
        "rgb_width": 640,
        "rgb_height": 480,
        "depth_width": 640,
        "depth_height": 480,
        "rgb_format": 0, //0表示rgb_data是rgb888格式,1表示是nv12格式
        "rgb_data": "base64编码的RGB图像数据",
        "depth_data": "base64编码的深度图像数据"
    }
}
```

**说明**:

- `rgb_format`: 0=RGB888, 1=NV12
- 深度数据为16位无符号整数，单位为毫米

### 7. 获取视频流地址

**接口地址**: `GET /signalservice/video/open`

**功能描述**: 获取可用的RTSP视频流地址

**请求参数**: 无

**响应示例**:

```json
{
    "code": "0",
    "message": "success",
    "data": {
        "unitree_rtsp_url": "rtsp://172.16.33.232:18554/unitree",
        "realsense_rtsp_url": "rtsp://172.16.33.232:18555/realsense", 
        "orbbec_rtsp_url": "rtsp://172.16.33.232:18556/orbbec"
    }
}
```

**说明**:

- 只有正在运行的相机服务才会返回对应的RTSP地址
- 可以使用VLC等播放器直接播放RTSP流
- 支持多路视频流同时观看,为了降低流量带宽，单个流同时只支持1个客户端观看

## 使用示例

### Python示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:18080"

# 机器人移动
def move_robot(vx, vy, vyaw):
    url = f"{BASE_URL}/signalservice/robot/move"
    data = {"vx": vx, "vy": vy, "vyaw": vyaw}
    response = requests.post(url, json=data)
    return response.json()

# 获取点云数据
def get_point_cloud():
    url = f"{BASE_URL}/signalservice/robot/point_cloud"
    response = requests.get(url)
    return response.json()

# 获取彩色深度图
def get_color_depth_snapshot():
    url = f"{BASE_URL}/signalservice/video/color_depth_snapshot"
    response = requests.get(url)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 控制机器人前进
    result = move_robot(0.5, 0.0, 0.0)
    print("移动结果:", result)
  
    # 获取点云数据
    point_cloud = get_point_cloud()
    print("点云数据:", point_cloud)
  
    # 获取彩色深度图
    snapshot = get_color_depth_snapshot()
    print("抓图结果:", snapshot)
```

### C++示例

```cpp
#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include <iostream>

using json = nlohmann::json;

class RobotAPI {
private:
    std::string base_url = "http://localhost:18080";
  
    static size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
        userp->append((char*)contents, size * nmemb);
        return size * nmemb;
    }
  
    json make_request(const std::string& endpoint, const json& data = nullptr) {
        CURL* curl = curl_easy_init();
        std::string response;
  
        if (curl) {
            std::string url = base_url + endpoint;
            std::string post_data;
  
            if (!data.is_null()) {
                post_data = data.dump();
            }
  
            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
  
            if (!post_data.empty()) {
                curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data.c_str());
                curl_easy_setopt(curl, CURLOPT_POST, 1L);
            }
  
            CURLcode res = curl_easy_perform(curl);
            curl_easy_cleanup(curl);
  
            if (res == CURLE_OK) {
                return json::parse(response);
            }
        }
  
        return json();
    }

public:
    json move_robot(float vx, float vy, float vyaw) {
        json data = {
            {"vx", vx},
            {"vy", vy}, 
            {"vyaw", vyaw}
        };
        return make_request("/signalservice/robot/move", data);
    }
  
    json get_point_cloud() {
        return make_request("/signalservice/robot/point_cloud");
    }
  
    json get_color_depth_snapshot() {
        return make_request("/signalservice/video/color_depth_snapshot");
    }
};

int main() {
    RobotAPI api;
  
    // 控制机器人移动
    auto result = api.move_robot(0.5, 0.0, 0.0);
    std::cout << "移动结果: " << result.dump() << std::endl;
  
    // 获取点云数据
    auto point_cloud = api.get_point_cloud();
    std::cout << "点云数据: " << point_cloud.dump() << std::endl;
  
    return 0;
}
```

## 注意事项

1. **参数范围限制**: 移动控制接口有速度限制，超出范围会自动调整到安全值
2. **相机超时**: 抓图接口有5秒超时，如果相机未就绪会返回超时错误
3. **功能支持**: 部分功能可能不支持（如点云、高度图），会返回相应的错误码
4. **网络连接**: 确保算法程序能够访问到机器狗的sdk服务
6. **实时性**: 移动接口建议根据实际需求调整请求频率，避免机器狗底层sdk处理不过来

## 错误处理

当API调用失败时，请检查：

1. **网络连接**: 确保能够访问到服务地址
2. **服务状态**: 确保机器狗的sdk服务正在运行
3. **参数范围**: 检查请求参数是否在允许范围内
4. **硬件状态**: 确保相关硬件（相机、机器人）正常工作
5. **错误码**: 根据返回的错误码进行相应的处理
