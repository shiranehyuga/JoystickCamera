"""
カメラ操作ユーティリティライブラリ
Fusion 360のカメラを制御するための再利用可能な機能を提供
"""

import adsk.core
import adsk.fusion
import traceback
import math
from typing import List, ClassVar, Dict, Any, Optional, Tuple, Union
from .quaternion import Quaternion

# Fusionアプリケーション インスタンス
app: adsk.core.Application = adsk.core.Application.get()
ui: adsk.core.UserInterface = app.userInterface

class CameraUtility:
    """カメラ操作ユーティリティクラス
    
    他のアドインでも再利用可能なカメラ制御機能を提供します。
    """
    
    # デフォルト設定
    DEFAULT_ROTATION_SCALE: ClassVar[float] = 0.01
    DEFAULT_DEBUG: ClassVar[bool] = False
    DEFAULT_USE_Z_AXIS_ROTATION: ClassVar[bool] = False
    
    def __init__(self, 
                 rotation_scale: float = DEFAULT_ROTATION_SCALE, 
                 debug: bool = DEFAULT_DEBUG,
                 use_z_axis_rotation: bool = DEFAULT_USE_Z_AXIS_ROTATION,
                 log_function: callable = None):
        """
        Parameters:
            rotation_scale: カメラ回転のスケール係数
            debug: デバッグモードフラグ
            use_z_axis_rotation: Z軸回転モード使用フラグ
            log_function: ログ出力関数（None の場合は内部でシンプルなログ処理を行う）
        """
        self.rotation_scale = rotation_scale
        self.debug = debug
        self.use_z_axis_rotation = use_z_axis_rotation
        self._log_function = log_function
    
    def log(self, message: str, level: adsk.core.LogLevels = adsk.core.LogLevels.InfoLogLevel) -> None:
        """ログ出力関数
        
        Parameters:
            message: ログメッセージ
            level: ログレベル
        """
        if self._log_function:
            self._log_function(message, level)
        else:
            # デフォルトのシンプルなログ処理
            if level == adsk.core.LogLevels.ErrorLogLevel or (self.debug and level == adsk.core.LogLevels.WarningLogLevel):
                print(f"[CameraUtils] {level}: {message}")
    
    def set_rotation_scale(self, value: float) -> None:
        """回転スケールを設定
        
        Parameters:
            value: 新しい回転スケール値
        """
        self.rotation_scale = value
        self.log(f'Rotation scale set to: {value}')
    
    def navigate_to_home_view(self) -> None:
        """カメラをホームビュー（正面図）に移動する"""
        try:
            # アクティブなビューポートを取得
            viewport = app.activeViewport
            if not viewport:
                self.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
                
            # viewport.goHome() メソッドを使用してホームビューに移動
            try:
                # トランジションの設定（滑らかに移動するかどうか）
                transition = True  # True: スムーズな移動、False: 直接ジャンプ
                
                # goHome メソッドを実行
                result = viewport.goHome(transition)
                
                if result:
                    self.log("ホームビューに正常に移動しました", adsk.core.LogLevels.InfoLogLevel)
                else:
                    self.log("ホームビューへの移動が失敗しました", adsk.core.LogLevels.WarningLogLevel)
                    
                # 画面を更新
                viewport.refresh()
                
                return
            except Exception as e:
                self.log(f"ホームビュー移動中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.WarningLogLevel)
                
            # 以前の方法をバックアップとして残す（APIが失敗した場合）
            try:
                # コマンドIDを使用してホームビューコマンドを実行
                ui.commandDefinitions.itemById('ViewHomeCmd').execute()
                self.log("ホームビューコマンドを実行しました（バックアップ方法）", adsk.core.LogLevels.InfoLogLevel)
            except Exception as e:
                self.log(f"すべてのホームビュー移動方法が失敗しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
                
        except Exception as e:
            self.log(f"ホームビューへの移動中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            if self.debug:
                self.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def fit_view(self) -> None:
        """現在のビューをフィットさせる"""
        try:
            viewport = app.activeViewport
            if not viewport:
                self.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
                
            viewport.fit()
            self.log("フィットビューを実行しました", adsk.core.LogLevels.InfoLogLevel)
        except Exception as e:
            self.log(f"フィットビュー実行中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            if self.debug:
                self.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def rotate_camera_with_quaternion(self, rotation_quaternion: Quaternion) -> None:
        """クォータニオンを使用してカメラを回転させる
        
        Parameters:
            rotation_quaternion: 回転を表すQuaternion
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                self.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
                
            camera: adsk.core.Camera = viewport.camera
            if not camera:
                return

            # カメラの滑らかな遷移を無効化
            camera.isSmoothTransition = False
            
            eye: adsk.core.Point3D = camera.eye
            target: adsk.core.Point3D = camera.target
            up: adsk.core.Vector3D = camera.upVector

            # eye位置の回転
            eye_vector: adsk.core.Vector3D = target.vectorTo(eye)
            rotated_eye_vector: adsk.core.Vector3D = rotation_quaternion.transform_vector(eye_vector)
            new_eye: adsk.core.Point3D = target.copy()
            new_eye.translateBy(rotated_eye_vector)

            # upベクトルの回転
            rotated_up: adsk.core.Vector3D = rotation_quaternion.transform_vector(up)

            # カメラの新しい位置と向きを設定
            camera.eye = new_eye
            camera.upVector = rotated_up
            viewport.camera = camera
            
            # 画面更新
            viewport.refresh()

        except Exception as e:
            # エラーログ
            self.log(f'Camera rotation error: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            if self.debug:
                self.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
                
    def get_camera_vectors(self) -> tuple:
        """カメラの現在の視線ベクトルと上方向ベクトルを取得する
        
        Returns:
            tuple: (forward, right, up) - それぞれのベクトル
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                self.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return None, None, None
                
            camera: adsk.core.Camera = viewport.camera
            if not camera:
                return None, None, None
            
            eye: adsk.core.Point3D = camera.eye
            target: adsk.core.Point3D = camera.target
            up: adsk.core.Vector3D = camera.upVector
            
            # 視線方向とright方向の計算
            forward: adsk.core.Vector3D = target.vectorTo(eye)
            forward.normalize()
            
            right: adsk.core.Vector3D = forward.crossProduct(up)
            # rightベクトルが無効な場合のみ修正
            if right.length < 0.001:
                right = adsk.core.Vector3D.create(1, 0, 0)  # X軸を使用
            else:
                right.normalize()
                
            return forward, right, up
            
        except Exception as e:
            self.log(f'Error getting camera vectors: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            if self.debug:
                self.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
            return None, None, None
    
    def set_viewcube_orientation(self, orientation: adsk.core.ViewOrientations) -> None:
        """指定された向きにビューを設定
        
        Parameters:
            orientation: 設定するビューの向き (adsk.core.ViewOrientations)
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                self.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
                
            # カメラの向きを設定
            camera = viewport.camera
            camera.isSmoothTransition = True
            viewport.viewOrientation = orientation
            viewport.refresh()
            
        except Exception as e:
            self.log(f"ビュー方向設定中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            if self.debug:
                self.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def set_isometric_view(self) -> None:
        """アイソメトリック（等角投影）ビューに設定"""
        try:
            viewport = app.activeViewport
            if not viewport:
                self.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
                
            # アイソメトリックビューに設定
            camera = viewport.camera
            
            # アイソメトリックビュー移動時は滑らかな遷移を有効にする
            camera.isSmoothTransition = True
            
            eye = adsk.core.Point3D.create(10, -10, 10)
            target = adsk.core.Point3D.create(0, 0, 0)
            up = adsk.core.Vector3D.create(0, 0, 1)
            camera.eye = eye
            camera.target = target
            camera.upVector = up
            viewport.camera = camera
            viewport.refresh()
            self.log("アイソメトリックビューを実行しました", adsk.core.LogLevels.InfoLogLevel)
            
        except Exception as e:
            self.log(f"アイソメトリックビュー設定中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            if self.debug:
                self.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def rotate_camera(self, 
                     rotation_axis: adsk.core.Vector3D, 
                     angle_degrees: float = 90.0, 
                     smooth: bool = True) -> None:
        """カメラを指定された軸と角度で回転
        
        Parameters:
            rotation_axis: 回転軸ベクトル
            angle_degrees: 回転角度（度）
            smooth: 滑らかな遷移を使用するか
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                self.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
                
            camera = viewport.camera
            camera.isSmoothTransition = smooth
            
            eye = camera.eye
            target = camera.target
            up = camera.upVector
            
            # 回転角度をラジアンに変換
            angle_rad = math.radians(angle_degrees)
            
            # クォータニオンによる回転
            q = Quaternion.from_axis_angle(rotation_axis, angle_rad)
            
            # 視点の回転
            eye_vector = target.vectorTo(eye)
            rotated_eye_vector = q.transform_vector(eye_vector)
            new_eye = target.copy()
            new_eye.translateBy(rotated_eye_vector)
            
            # アップベクトルの回転
            rotated_up = q.transform_vector(up)
            
            # カメラの更新
            camera.eye = new_eye
            camera.upVector = rotated_up
            viewport.camera = camera
            viewport.refresh()
            
        except Exception as e:
            self.log(f"カメラ回転中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            if self.debug:
                self.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)