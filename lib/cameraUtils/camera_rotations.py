"""
カメラ操作拡張機能を提供するモジュール
"""

import adsk.core
import traceback
import math
from typing import Dict, Optional, Tuple
from .camera_utility import CameraUtility
from .quaternion import Quaternion

# Fusionアプリケーション インスタンス
app: adsk.core.Application = adsk.core.Application.get()

class CameraRotations:
    """
    カメラ回転に関する高度な機能を提供するユーティリティクラス
    """
    
    def __init__(self, camera_util: CameraUtility):
        """
        Parameters:
            camera_util: ベースのカメラユーティリティインスタンス
        """
        self.camera_util = camera_util
    
    def _is_on_viewcube_face(self) -> bool:
        """現在のカメラがViewCubeの標準面を向いているかをチェック
        
        Returns:
            bool: 標準面を向いている場合はTrue、任意の向きの場合はFalse
        """
        try:
            viewport = app.activeViewport
            if not viewport or not viewport.camera:
                return False
            
            camera = viewport.camera
            return camera.viewOrientation != adsk.core.ViewOrientations.ArbitraryViewOrientation
            
        except Exception as e:
            self.camera_util.log(f'ViewCube面チェック中にエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            return False
    
    def move_to_nearest_viewcube_face(self) -> None:
        """現在のカメラ視点から最も近いViewCube面に移動する"""
        try:
            viewport = app.activeViewport
            if not viewport:
                self.camera_util.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                self.camera_util.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # 現在のviewOrientationを表示
            current_orientation = camera.viewOrientation
            orientation_names = {
                adsk.core.ViewOrientations.ArbitraryViewOrientation: "任意の向き",
                adsk.core.ViewOrientations.BackViewOrientation: "背面",
                adsk.core.ViewOrientations.BottomViewOrientation: "下面", 
                adsk.core.ViewOrientations.FrontViewOrientation: "前面",
                adsk.core.ViewOrientations.IsoBottomLeftViewOrientation: "アイソ下左",
                adsk.core.ViewOrientations.IsoBottomRightViewOrientation: "アイソ下右",
                adsk.core.ViewOrientations.IsoTopLeftViewOrientation: "アイソ上左",
                adsk.core.ViewOrientations.IsoTopRightViewOrientation: "アイソ上右",
                adsk.core.ViewOrientations.LeftViewOrientation: "左面",
                adsk.core.ViewOrientations.RightViewOrientation: "右面",
                adsk.core.ViewOrientations.TopViewOrientation: "上面"
            }
            current_orientation_name = orientation_names.get(current_orientation, f"不明({current_orientation})")
            self.camera_util.log(f"現在のviewOrientation: {current_orientation_name}({current_orientation})", adsk.core.LogLevels.InfoLogLevel)

            # カメラの視線方向ベクトルを取得（eyeからtargetへの方向）
            eye = camera.eye
            target = camera.target
            view_direction = target.vectorTo(eye)
            view_direction.normalize()
            
            # 標準的なViewCube面の方向ベクトルを定義
            viewcube_directions = {
                adsk.core.ViewOrientations.FrontViewOrientation: adsk.core.Vector3D.create(0, -1, 0),  # 前面（-Y方向）
                adsk.core.ViewOrientations.BackViewOrientation: adsk.core.Vector3D.create(0, 1, 0),   # 背面（+Y方向）
                adsk.core.ViewOrientations.LeftViewOrientation: adsk.core.Vector3D.create(-1, 0, 0),  # 左面（-X方向）
                adsk.core.ViewOrientations.RightViewOrientation: adsk.core.Vector3D.create(1, 0, 0),  # 右面（+X方向）
                adsk.core.ViewOrientations.TopViewOrientation: adsk.core.Vector3D.create(0, 0, 1),    # 上面（+Z方向）
                adsk.core.ViewOrientations.BottomViewOrientation: adsk.core.Vector3D.create(0, 0, -1) # 下面（-Z方向）
            }
            
            # 現在の視線方向と各ViewCube面の方向との内積を計算して最も近い面を見つける
            max_dot_product = -2.0  # 初期値は-2（内積の最小値-1より小さい値）
            nearest_orientation = adsk.core.ViewOrientations.FrontViewOrientation  # デフォルト
            
            for orientation, direction in viewcube_directions.items():
                dot_product = view_direction.dotProduct(direction)
                if dot_product > max_dot_product:
                    max_dot_product = dot_product
                    nearest_orientation = orientation
            
            # デバッグ情報をログ出力
            selected_name = orientation_names.get(nearest_orientation, "不明")
            self.camera_util.log(f"現在の視線方向: [{view_direction.x:.3f}, {view_direction.y:.3f}, {view_direction.z:.3f}]", adsk.core.LogLevels.InfoLogLevel)
            self.camera_util.log(f"最寄りのViewCube面: {selected_name} (類似度: {max_dot_product:.3f})", adsk.core.LogLevels.InfoLogLevel)
            
            # 最寄りの面に移動
            self.camera_util.log(f"最寄りのViewCube面 '{selected_name}' に移動を実行します", adsk.core.LogLevels.InfoLogLevel)
            self.camera_util.set_viewcube_orientation(nearest_orientation)
            self.camera_util.log(f"ViewCube面 '{selected_name}' への移動が完了しました", adsk.core.LogLevels.InfoLogLevel)
            
        except Exception as e:
            self.camera_util.log(f'最寄りのViewCube面への移動に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            if self.camera_util.debug:
                self.camera_util.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def rotate_screen_horizontal(self, angle_degrees: float) -> None:
        """画面の垂直軸で水平方向に回転（右が正、左が負）
        
        Parameters:
            angle_degrees: 回転角度（度）
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                self.camera_util.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                self.camera_util.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # カメラの滑らかな遷移を有効にする
            camera.isSmoothTransition = True
            
            # 上方向ベクトルを回転軸として使用
            up_vector = camera.upVector.copy()
            up_vector.normalize()
            
            # 角度をラジアンに変換（マイナスで反転して直感的な回転方向にする）
            angle_radians = math.radians(-angle_degrees)
            
            # クォータニオンを使用して回転
            rotation_quaternion = Quaternion.from_axis_angle(up_vector, angle_radians)
            
            # 視点（eye）位置を回転
            eye_vector = camera.target.vectorTo(camera.eye)
            rotated_eye_vector = rotation_quaternion.transform_vector(eye_vector)
            
            new_eye = camera.target.copy()
            new_eye.translateBy(rotated_eye_vector)
            camera.eye = new_eye
            
            # カメラをビューポートに適用
            viewport.camera = camera
            viewport.refresh()
            
        except Exception as e:
            self.camera_util.log(f'水平画面回転に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            if self.camera_util.debug:
                self.camera_util.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def rotate_screen_vertical(self, angle_degrees: float) -> None:
        """画面の水平軸で垂直方向に回転（上が正、下が負）
        
        Parameters:
            angle_degrees: 回転角度（度）
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                self.camera_util.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                self.camera_util.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # カメラの滑らかな遷移を有効にする
            camera.isSmoothTransition = True
            
            # 視線方向と上方向から右方向ベクトルを計算
            eye_to_target = camera.eye.vectorTo(camera.target)
            eye_to_target.normalize()
            
            up_vector = camera.upVector.copy()
            up_vector.normalize()
            
            right_vector = eye_to_target.crossProduct(up_vector)
            right_vector.normalize()
            
            # 角度をラジアンに変換
            angle_radians = math.radians(angle_degrees)
            
            # クォータニオンを使用して回転
            rotation_quaternion = Quaternion.from_axis_angle(right_vector, angle_radians)
            
            # 視点（eye）位置を回転
            eye_vector = camera.target.vectorTo(camera.eye)
            rotated_eye_vector = rotation_quaternion.transform_vector(eye_vector)
            
            # 上ベクトルを回転
            rotated_up = rotation_quaternion.transform_vector(up_vector)
            
            # カメラを更新
            new_eye = camera.target.copy()
            new_eye.translateBy(rotated_eye_vector)
            camera.eye = new_eye
            camera.upVector = rotated_up
            
            # カメラをビューポートに適用
            viewport.camera = camera
            viewport.refresh()
            
        except Exception as e:
            self.camera_util.log(f'垂直画面回転に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            if self.camera_util.debug:
                self.camera_util.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def rotate_screen_axial(self, angle_degrees: float) -> None:
        """画面の視線方向軸で回転（時計回りが正、反時計回りが負）
        
        Parameters:
            angle_degrees: 回転角度（度）
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                self.camera_util.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                self.camera_util.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # カメラの滑らかな遷移を有効にする
            camera.isSmoothTransition = True
            
            # 視線方向を計算
            view_direction = camera.target.vectorTo(camera.eye)
            view_direction.normalize()
            
            # 角度をラジアンに変換
            angle_radians = math.radians(angle_degrees)
            
            # クォータニオンを使用して回転
            rotation_quaternion = Quaternion.from_axis_angle(view_direction, angle_radians)
            
            # 上ベクトルを回転
            up_vector = camera.upVector.copy()
            rotated_up = rotation_quaternion.transform_vector(up_vector)
            
            # カメラを更新
            camera.upVector = rotated_up
            
            # カメラをビューポートに適用
            viewport.camera = camera
            viewport.refresh()
            
        except Exception as e:
            self.camera_util.log(f'軸方向画面回転に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            if self.camera_util.debug:
                self.camera_util.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def smart_rotate_horizontal(self, angle_degrees: float) -> None:
        """スマート水平回転：任意の向きの場合は最寄り面に移動してから回転
        
        Parameters:
            angle_degrees: 回転角度（度）
        """
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            self.camera_util.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから回転します", adsk.core.LogLevels.InfoLogLevel)
            self.move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            self.camera_util.log("現在標準ViewCube面を向いているため、直接回転します", adsk.core.LogLevels.InfoLogLevel)
        self.rotate_screen_horizontal(angle_degrees)
    
    def smart_rotate_vertical(self, angle_degrees: float) -> None:
        """スマート垂直回転：任意の向きの場合は最寄り面に移動してから回転
        
        Parameters:
            angle_degrees: 回転角度（度）
        """
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            self.camera_util.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから回転します", adsk.core.LogLevels.InfoLogLevel)
            self.move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            self.camera_util.log("現在標準ViewCube面を向いているため、直接回転します", adsk.core.LogLevels.InfoLogLevel)
        self.rotate_screen_vertical(angle_degrees)
    
    def smart_rotate_axial(self, angle_degrees: float) -> None:
        """スマート軸回転：任意の向きの場合は最寄り面に移動してから回転
        
        Parameters:
            angle_degrees: 回転角度（度）
        """
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            self.camera_util.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから回転します", adsk.core.LogLevels.InfoLogLevel)
            self.move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            self.camera_util.log("現在標準ViewCube面を向いているため、直接回転します", adsk.core.LogLevels.InfoLogLevel)
        self.rotate_screen_axial(angle_degrees)