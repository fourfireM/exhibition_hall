import requests
import time
import subprocess

"""
status:
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"
"""

NavigationStatus = {
    "status": "idle",
    "health": True,
}

_navigation_count = 0


def get_uwb_data():
    url = "http://localhost:18080/signalservice/uwb"
    response = requests.get(url)
    print(response.json())
    return response.json()

def navigation_start(target_position):
    url = "http://localhost:8001/api/start"

    print(f"导航开始，目标位置: {target_position}")
    target_position["frame_id"] = "map"

    # global NavigationStatus
    # NavigationStatus["status"] = "running"
    # NavigationStatus["health"] = True
    # return {
    #     "status": "running",
    #     "health": True,
    # }
    response = requests.post(url, json=target_position)
    if response.status_code == 200:
        res = response.json()
        print(res)
        if res["success"] == True:
            return True
        else:
            return False
    else:
        print(f"导航开始失败: {response.status_code}")
        return False


def navigation_stop():
    url = "http://localhost:8001/api/stop"

    response = requests.post(url)
    if response.status_code == 200:
        res = response.json()
        print(res)
        if res["success"] == True:
            return True
        else:
            return False
    else:
        print(f"导航停止失败: {response.status_code}")
        return False
    # global NavigationStatus
    # global _navigation_count
    # _navigation_count = 0
    # NavigationStatus["status"] = "idle"
    # NavigationStatus["health"] = True

    return NavigationStatus

    
def navigation_status():
    url = "http://localhost:8001/api/status"

    response = requests.get(url)
    if response.status_code == 200:
        res = response.json()
        print(res)
        if res["success"] == True:
            return res['data']['status']
        else:
            return None
    else:
        print(f"导航状态检查失败: {response.status_code}")
        return None
    # global _navigation_count
    # global NavigationStatus
    # print(f"状态检查次数: {_navigation_count}")
    # print(f"导航状态: {NavigationStatus}")
    # if NavigationStatus["status"] == "idle":
    #     return NavigationStatus


    # if _navigation_count >= 10:
    #     NavigationStatus["status"] = "finished"
    #     _navigation_count = 0
    #     return NavigationStatus
    # if NavigationStatus["status"] == "running":
    #     _navigation_count += 1
    #     return NavigationStatus
    # return NavigationStatus

    
def audio_output(type_name):
    if type_name == "start":
        file_path = "/home/myb/Exhibition_Hall/guide_dog/audio_file/start_xingguangdating_xy.mp3"
    if type_name == "guide":
        file_path = "/home/myb/Exhibition_Hall/guide_dog/audio_file/qinggengwolai_xy.mp3"
    if type_name == "quick":
        file_path = "/home/myb/Exhibition_Hall/guide_dog/audio_file/qingjiakuaijiaobu_xy.mp3"
    if type_name == "return":
        file_path = "/home/myb/Exhibition_Hall/guide_dog/audio_file/retrurn_xingguangdating_xy.mp3"

    if type_name == "next":
        file_path = "/home/myb/Exhibition_Hall/guide_dog/audio_file/next_xy.mp3"
    try:
        command = ["mpg123", "-g", str(1.0), file_path]
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"播放音频时出错: {e}")

    print(f"语音播放: {type_name}")
    return


if __name__ == "__main__":
    # while True:
    data = get_uwb_data()
        # print(data['data'])
        
        # time.sleep(1)