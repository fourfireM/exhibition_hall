import gradio as gr
import threading
import time
from dog_service import get_uwb_data, navigation_start, navigation_stop, navigation_status, audio_output
import traceback
from move import call_robot_move_api


class GuideDogController:
    def __init__(self):
        self.is_running = False
        self.navigation_active = False
        self.current_distance = 0
        self.current_azimuth = 0
        self.status_message = "系统就绪"
        self.thread = None

        self.navigation_service_health = None
        self.navigation_status = None
        
        # 位置管理
        self.start_position = {
            "position": {
                "x": 2.138,
                "y": -1.059,
                "z": 0
            },
            "orientation": {
                "x": 0,
                "y": 0,
                "z": -0.969,
                "w": 0.243
            } 
        } # 起始点
        self.guide_position = {
            "position": {
                "x": 5.80781,
                "y": 6.98177,
                "z": 0
            },
            "orientation": {
                "x": 0,
                "y": 0,
                "z": 0.752544,
                "w": 0.658542
            }
        }  # 引导目标点
        
        # 合并所有多点位引导位置配置
        self.multi_point_positions = {
            "vip": {
                "A": {
                    "position": {"x": 6.839, "y": -9.069, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0.115, "w": 0.993}
                },
                "B": {
                    "position": {"x": 13.942, "y": -4.806, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0.317, "w": 0.948}
                },
                "C": {
                    "position": {"x": 12.056, "y": 16.803, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": -0.998, "w": 0.048}
                },
                "D": {
                    "position": {"x": 2.86547, "y": 71.826, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0.89045, "w": 0.455206}
                },
                "E": {
                    "position": {"x": 3.00834, "y": 34.3506, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": -0.743092, "w": 0.669195}
                },
                "F": {
                    "position": {"x": 2.71766, "y": 30.9047, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": -0.774974, "w": 0.632013}
                },
                "G": {
                    "position": {"x": 0.758814, "y": 7.62268, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": -0.333069, "w": 0.942907}
                }
            },
            "zhanting": {
                "xingguangdating": {
                    "position": {"x": 13.942, "y": -4.806, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": 0.317, "w": 0.948}
                },
                "hudongtiyanqu": {
                    "position": {"x": 12.056, "y": 16.803, "z": 0},
                    "orientation": {"x": 0, "y": 0, "z": -0.998, "w": 0.048}
                },
            }
        }
        
        # 合并所有路由配置
        self.routes = {
            "vip": ["A", "B", "C"],  # 可扩展为 ["A", "B", "C", "D", "E", "F", "G"]
            "zhanting": ["xingguangdating", "hudongtiyanqu"]
        }
        
        self.current_target_position = None  # 当前目标点
        self.next_target_position = None  # 下一个目标点
        
        # 工作流状态
        self.workflow_state = "waiting"  # waiting, guiding, returning, multi_point_guiding, multi_point_returning
        self.uwb_check_enabled = False  # 是否启用UWB距离检查
        
        # 多点引导通用参数
        self.current_route_type = None  # 当前路由类型（"vip"或"zhanting"）
        self.current_point_index = 0  # 当前点位索引

    def update_navigation_status(self):
        try:
            self.navigation_status = navigation_status()
            # self.navigation_service_health = navigation_status()["health"]
        except Exception as e:
            print(traceback.format_exc())
            self.navigation_status = None
            self.navigation_service_health = None


    
    def start_guide_system(self):
        """开始引路系统"""
        if self.is_running:
            return "系统已在运行中"
        
        self.is_running = True
        self.thread = threading.Thread(target=self._guide_loop, daemon=True)
        self.thread.start()
        return "引路系统已启动"
    
    def start_guiding(self, type_name="guide"):
        """开始引导流程（统一处理guide、vip、zhanting）"""
        if self.workflow_state != "waiting":
            return f"当前状态不允许开始引导: {self.workflow_state}"

        
        
        if type_name == "guide":
            # 单点引导模式
            audio_output(type_name="start")
            self.current_target_position = self.guide_position.copy()
            self.next_target_position = self.start_position.copy()
            self.workflow_state = "guiding"
            self.uwb_check_enabled = True
            self.current_route_type = None
        elif type_name in ["vip", "zhanting"]:
            # 多点引导模式（vip和zhanting使用相同逻辑）
            audio_output(type_name="start")

            self.current_route_type = type_name
            self.current_point_index = 0
            
            # 获取第一个目标位置
            route = self.routes[type_name]
            first_point = route[0]
            self.current_target_position = self.multi_point_positions[type_name][first_point].copy()
            self.workflow_state = "multi_point_guiding"
            self.uwb_check_enabled = True
        else:
            return f"未知的引导类型: {type_name}"
        
        # 开始导航
        if navigation_start(self.current_target_position):
            self.navigation_active = True
            self.status_message = f"开始{type_name}引导到目标位置"
        else:
            self.status_message = f"开始引导失败，请检查导航服务"
            return f"导航服务启动失败"
        
        return f"{type_name}引导流程已开始"
    
    def stop_guide_system(self):
        """停止引路系统"""
        self.is_running = False
        if self.navigation_active:
            if navigation_stop():
                self.navigation_active = False
            else:
                self.status_message = f"停止引导失败，请检查导航服务"
                return
            
        
        # 重置状态
        self.workflow_state = "waiting"
        self.current_target_position = None
        self.next_target_position = None
        self.uwb_check_enabled = False
        self.status_message = "系统已停止"
        return "引路系统已停止"
    
    def _guide_loop(self):
        """主要的引路控制循环"""
        while self.is_running:
            try:
                # 获取UWB数据
                self.update_navigation_status()
                uwb_data = get_uwb_data()
                if uwb_data and 'data' in uwb_data:
                    data = uwb_data['data']
                    self.current_distance = data.get('distance', 0)
                    self.current_azimuth = data.get('azimuth', 0)
                
                # 执行工作流状态机
                self._execute_workflow()
                
            except Exception as e:
                print(traceback.format_exc())
                self.status_message = f"错误: {str(e)}"
            
            time.sleep(3.0)  # 每0.5秒检查一次
    
    def _execute_workflow(self):
        """执行工作流状态机（简化版）"""
        if self.workflow_state == "waiting":
            self.status_message = "等待开始引导指令"
        elif self.workflow_state == "guiding":
            self._handle_guiding_state()
        elif self.workflow_state == "returning":
            self._handle_returning_state()
        elif self.workflow_state == "multi_point_guiding":
            self._handle_multi_point_guiding_state()
        elif self.workflow_state == "multi_point_returning":
            self._handle_multi_point_returning_state()


    
    def _handle_guiding_state(self):
        """处理引导状态"""
        distance = self.current_distance
        
        # 检查是否到达目标位置（这里用简单的逻辑模拟）
        if self._reached_target():
            # 引导结束，播放结束语音
            audio_output(type_name="return")
            
            # 切换到返回状态
            self.workflow_state = "returning"
            """
            可能要加一些确保uwb返回的逻辑
            """
            self.current_target_position = self.start_position.copy()
            self.next_target_position = None
            self.uwb_check_enabled = False  # 返回过程不需要UWB检查
            
            if navigation_start(self.current_target_position):
                self.navigation_active = True
            else:
                self.status_message = f"返回引导失败，请检查导航服务"
                return
            self.status_message = "引导完成，正在返回起始点"
            return
        
        # UWB距离检查逻辑（仅在引导过程中启用）
        if self.uwb_check_enabled:
            if distance > 4:
                # 距离超过5m，停止导航等待
                if self.navigation_active:
                    if navigation_stop():
                        self.navigation_active = False
                    else:
                        self.status_message = f"停止引导失败，请检查导航服务"
                        return
                    
                audio_output(type_name="quick")
                self.status_message = f"距离过远({distance:.2f}m)，等待跟随者靠近"
                
            elif distance < 2 and not self.navigation_active:
                # 距离小于2m，继续导航
                if navigation_start(self.current_target_position):

                    self.navigation_active = True
                    self.status_message = f"距离合适({distance:.2f}m)，继续引导"
                else:
                    self.status_message = f"继续引导失败，请检查导航服务"
                    return
                audio_output(type_name="guide")
            elif self.navigation_active and 2 <= distance <= 4:
                self.status_message = f"正在引导中，距离: {distance:.2f}m"
                audio_output(type_name="guide")
            elif not self.navigation_active and 2 <= distance <= 4:
                audio_output(type_name="quick")
    
    def _handle_returning_state(self):
        """处理返回状态"""
        # 检查是否到达起始点
        if self._reached_target():
            # 返回完成
            # navigation_stop()
            self.navigation_active = False
            self.workflow_state = "waiting"
            self.current_target_position = None
            self.next_target_position = None
            self.status_message = "已返回起始点，等待下次引导"
        else:
            self.status_message = "正在返回起始点"
    
    def _handle_multi_point_guiding_state(self):
        """处理多点引导状态（统一处理VIP和展厅）"""
        distance = self.current_distance
        route_type = self.current_route_type
        route = self.routes[route_type]
        
        # 检查是否到达当前目标点
        if self._reached_target():
            # 移动到下一个点
            self._move_to_next_point()
            return
        
        # UWB距离检查逻辑
        if self.uwb_check_enabled:
            current_point = route[self.current_point_index]
            
            if distance > 4:
                # 距离超过4m，停止导航等待
                if self.navigation_active:
                    if navigation_stop():
                        self.navigation_active = False
                    else:
                        self.status_message = f"停止{route_type}引导失败，请检查导航服务"
                        return
                    
                audio_output(type_name="quick")
                self.status_message = f"{route_type}引导: 距离过远({distance:.2f}m)，等待跟随者靠近，目标: {current_point}"
                
            elif distance < 2 and not self.navigation_active:
                # 距离小于2m，继续导航
                if navigation_start(self.current_target_position):
                    self.navigation_active = True
                    self.status_message = f"{route_type}引导: 距离合适({distance:.2f}m)，继续引导到{current_point}"
                else:
                    self.status_message = f"继续{route_type}引导失败，请检查导航服务"
                    return
                audio_output(type_name="guide")
                
            elif self.navigation_active and 2 <= distance <= 4:
                self.status_message = f"{route_type}引导中，目标: {current_point}，距离: {distance:.2f}m"
                
            elif not self.navigation_active and 2 <= distance <= 4:
                audio_output(type_name="quick")
    
    def _handle_multi_point_returning_state(self):
        """处理多点引导返回状态（统一处理VIP和展厅）"""
        # 检查是否到达起始点
        if self._reached_target():
            # 引导完全结束
            route_type = self.current_route_type
            self.navigation_active = False
            self.workflow_state = "waiting"
            self.current_target_position = None
            self.next_target_position = None
            self.current_point_index = 0
            self.current_route_type = None
            self.uwb_check_enabled = False
            self.status_message = f"{route_type}引导完成，已返回起始点"
        else:
            route_type = self.current_route_type
            self.status_message = f"{route_type}引导结束，正在返回起始点"
    
    def _move_to_next_point(self):
        """移动到路径的下一个点（统一处理VIP和展厅）"""
        self.current_point_index += 1
        route_type = self.current_route_type
        route = self.routes[route_type]
        
        # 检查是否完成所有点的引导
        if self.current_point_index >= len(route):
            # 引导路径完成
            self.workflow_state = "waiting"
            self.current_target_position = None
            self.next_target_position = None
            self.current_point_index = 0
            self.current_route_type = None
            self.uwb_check_enabled = False
            self.status_message = f"{route_type}引导完成，所有目标点已到达"
            return
        
        # 设置下一个目标点
        next_point = route[self.current_point_index]
        self.current_target_position = self.multi_point_positions[route_type][next_point].copy()
        if next_point == "hudongtiyanqu":
            audio_output(type_name="next")
        
        # 开始导航到下一个点
        if navigation_start(self.current_target_position):
            self.navigation_active = True
            self.status_message = f"{route_type}引导: 已到达，前往下一个目标: {next_point}"
        else:
            self.status_message = f"{route_type}引导失败，无法导航到{next_point}，请检查导航服务"
    
    def _reached_target(self):
        print(f"导航状态: {self.navigation_status}")
        return self.navigation_status == "succeeded"
    
    def get_status(self):
        """获取当前状态信息"""
        print(self.is_running, self.navigation_active, self.current_distance, self.current_azimuth, self.status_message)
        status_info = {
            "系统状态": "运行中" if self.is_running else "已停止",
            "工作流状态": self.workflow_state,
            "导航状态": "激活" if self.navigation_active else "停止",
            "当前距离": f"{self.current_distance:.2f}m",
            "方位角": f"{self.current_azimuth:.1f}°",
            "当前目标": str(self.current_target_position) if self.current_target_position else "无",
            "下个目标": str(self.next_target_position) if self.next_target_position else "无",
            "UWB检查": "启用" if self.uwb_check_enabled else "禁用",
            "状态信息": self.status_message
        }
        
        # 添加多点引导相关状态（统一处理VIP和展厅）
        if self.workflow_state in ["multi_point_guiding", "multi_point_returning"] and self.current_route_type:
            route = self.routes[self.current_route_type]
            if self.current_point_index < len(route):
                current_point = route[self.current_point_index]
                status_info[f"{self.current_route_type}当前目标"] = f"{current_point}"
            status_info[f"{self.current_route_type}进度"] = f"{self.current_point_index}/{len(route)}"
            status_info[f"{self.current_route_type}路径"] = " → ".join(route)
        
        return status_info

# 创建控制器实例
controller = GuideDogController()

def create_interface():
    """创建Gradio界面"""
    
    def start_system():
        return controller.start_guide_system()
    
    def stop_system():
        return controller.stop_guide_system()
    
    def start_guide():
        return controller.start_guiding(type_name="guide")
    
    def start_vip():    
        return controller.start_guiding(type_name="vip")

    def start_zhanting():
        return controller.start_guiding(type_name="zhanting")
    
    with gr.Blocks(title="引路犬控制系统", theme=gr.themes.Soft()) as app:
        gr.Markdown("# 🐕 引路犬控制系统")
        gr.Markdown("基于UWB定位的智能引路系统")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 控制面板")
                start_btn = gr.Button("🚀 启动引路系统", variant="primary", size="lg")
                # guide_btn = gr.Button("🎯 开始单点引导", variant="secondary", size="lg")
                # vip_guide_btn = gr.Button("🏛️ VIP室引导", variant="secondary", size="lg")
                zhanting_guide_btn = gr.Button("🏢 展厅引导", variant="secondary", size="lg")
                stop_btn = gr.Button("⏹️ 停止系统", variant="stop", size="lg")
                
                operation_result = gr.Textbox(label="操作结果", interactive=False)
            
            with gr.Column(scale=2):
                gr.Markdown("### 系统状态")
                display_status = gr.JSON(
                    value=lambda: controller.get_status(),
                    label="系统状态", 
                    every=1
                )
        
        # 事件绑定
        start_btn.click(
            fn=start_system,
            outputs=operation_result
        )
        
        # guide_btn.click(
        #     fn=start_guide,
        #     outputs=operation_result
        # )
        
        # vip_guide_btn.click(
        #     fn=start_vip,
        #     outputs=operation_result
        # )
        
        zhanting_guide_btn.click(
            fn=start_zhanting,
            outputs=operation_result
        )
        
        stop_btn.click(
            fn=stop_system,
            outputs=operation_result
        )
    
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
