import adsk.core
import adsk.fusion
import traceback
from typing import List, ClassVar
from ..lib import fusionAddInUtils as futil
from ..lib.cameraUtils import CameraUtility, CameraRotations
from .. import config

app: adsk.core.Application = adsk.core.Application.get()
ui: adsk.core.UserInterface = app.userInterface

class CameraController:
    """
    JoystickCameraアドイン用カメラコントローラ
    CameraUtilityライブラリを使用してカメラ操作を行う
    """
    rotation_scale: ClassVar[float] = getattr(config, "ROTATION_SCALE", 0.01)
    
    def __init__(self):
        # CameraUtilityのインスタンスを作成、ログ関数を渡す
        self.camera_util = CameraUtility(
            rotation_scale=self.rotation_scale,
            debug=getattr(config, "DEBUG", False),
            use_z_axis_rotation=getattr(config, "USE_Z_AXIS_ROTATION", False),
            log_function=futil.log
        )
        
        # 回転操作用のヘルパークラスを初期化
        self.rotations = CameraRotations(self.camera_util)
    
    @classmethod
    def set_rotation_scale(cls, value: float) -> None:
        """回転スケールを設定"""
        cls.rotation_scale = value
        futil.log(f"Rotation scale set to: {value}")
    
    def navigate_to_home_view(self) -> None:
        """カメラをホームビュー（正面図）に移動する"""
        # ライブラリの機能を使用してホームビューに移動
        self.camera_util.navigate_to_home_view()
    
    def update_camera_position(self, joystick_x: float, joystick_y: float) -> None:
        """ジョイスティックの入力に基づいてカメラ位置を更新
        
        Parameters:
            joystick_x: X軸の入力値 (-1.0 から 1.0)
            joystick_y: Y軸の入力値 (-1.0 から 1.0)
        """
        try:
            # 入力がほぼゼロの場合は処理をスキップ（パフォーマンス向上）
            if abs(joystick_x) < 0.005 and abs(joystick_y) < 0.005:
                return
            
            # カメラベクトルを取得
            forward, right, up = self.camera_util.get_camera_vectors()
            if not forward or not right or not up:
                return
            
            # シンプルな回転スケール計算
            rotation_scale = self.rotation_scale * 0.3
            
            # 単純な線形スケーリング
            joystick_x_scaled = joystick_x * rotation_scale
            joystick_y_scaled = joystick_y * rotation_scale
            
            # クォータニオン計算
            from ..lib.cameraUtils.quaternion import Quaternion
            
            # Z軸回転モードの使用有無に基づいて回転方法を選択
            if getattr(config, "USE_Z_AXIS_ROTATION", False):
                # Z軸回転モード
                world_z_axis = adsk.core.Vector3D.create(0, 0, 1)
                z_direction = 1 if up.dotProduct(world_z_axis) >= 0 else -1
                
                q_vertical = Quaternion.from_axis_angle(right, joystick_y_scaled)
                q_horizontal = Quaternion.from_axis_angle(world_z_axis, z_direction * -joystick_x_scaled)
            else:
                # 通常モード
                q_vertical = Quaternion.from_axis_angle(right, joystick_y_scaled)
                q_horizontal = Quaternion.from_axis_angle(up, -joystick_x_scaled)

            # 回転を結合
            q = q_horizontal * q_vertical
            
            # 回転を適用
            self.camera_util.rotate_camera_with_quaternion(q)
            
        except Exception as e:
            futil.log(f'Error updating camera position: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            if getattr(config, "DEBUG", False):
                futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def execute_button_function(self, function_name: str) -> None:
        """ボタンに割り当てられた機能を実行する"""
        try:
            viewport = app.activeViewport
            if not viewport:
                futil.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return

            if function_name == "home_view":
                self.navigate_to_home_view()
            elif function_name == "fit_view":
                self.camera_util.fit_view()
                futil.log("フィットビューを実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_front":
                self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.FrontViewOrientation)
                futil.log("ビューキューブ前面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_back":
                self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.BackViewOrientation)
                futil.log("ビューキューブ背面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_left":
                self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.LeftViewOrientation)
                futil.log("ビューキューブ左面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_right":
                self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.RightViewOrientation)
                futil.log("ビューキューブ右面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_top":
                self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
                futil.log("ビューキューブ上面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_bottom":
                self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.BottomViewOrientation)
                futil.log("ビューキューブ下面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "iso_view":
                self.camera_util.set_isometric_view()
                futil.log("アイソメトリックビューを実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "nearest_viewcube":
                self.rotations.move_to_nearest_viewcube_face()
                futil.log("最寄りのビューキューブ面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_right":
                self.rotations.rotate_screen_horizontal(90.0)
                futil.log("画面右回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_left":
                self.rotations.rotate_screen_horizontal(-90.0)
                futil.log("画面左回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_right":
                self.rotations.smart_rotate_horizontal(90.0)
                futil.log("スマート右回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_left":
                self.rotations.smart_rotate_horizontal(-90.0)
                futil.log("スマート左回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_up":
                self.rotations.rotate_screen_vertical(90.0)
                futil.log("画面上回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_down":
                self.rotations.rotate_screen_vertical(-90.0)
                futil.log("画面下回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_up":
                self.rotations.smart_rotate_vertical(90.0)
                futil.log("スマート上回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_down":
                self.rotations.smart_rotate_vertical(-90.0)
                futil.log("スマート下回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_clockwise":
                self.rotations.rotate_screen_axial(90.0)
                futil.log("画面垂直時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_counter_clockwise":
                self.rotations.rotate_screen_axial(-90.0)
                futil.log("画面垂直反時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_clockwise":
                self.rotations.smart_rotate_axial(90.0)
                futil.log("スマート垂直時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_counter_clockwise":
                self.rotations.smart_rotate_axial(-90.0)
                futil.log("スマート垂直反時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            else:
                futil.log(f"未知の機能: {function_name}", adsk.core.LogLevels.WarningLogLevel)
                return

            # ビューポートを更新
            viewport.refresh()

        except Exception as e:
            futil.log(f"ボタン機能の実行に失敗しました ({function_name}): {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
