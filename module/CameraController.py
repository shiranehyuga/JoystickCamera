import adsk.core
import adsk.fusion
import traceback
from typing import List, ClassVar
from ..lib import fusionAddInUtils as futil
from ..Quaternion import Quaternion
from .. import config

app: adsk.core.Application = adsk.core.Application.get()
ui: adsk.core.UserInterface = app.userInterface

class CameraController:
    rotation_scale: ClassVar[float] = getattr(config, 'ROTATION_SCALE', 0.01)

    @classmethod
    def set_rotation_scale(cls, value: float) -> None:
        cls.rotation_scale = value
        futil.log(f'Rotation scale set to: {value}')
        
    @staticmethod
    def navigate_to_home_view() -> None:
        """カメラをホームビュー（正面図）に移動する"""
        try:
            # アクティブなビューポートを取得
            viewport = app.activeViewport
            if not viewport:
                futil.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
                
            # viewport.goHome() メソッドを使用してホームビューに移動
            try:
                # トランジションの設定（滑らかに移動するかどうか）
                transition = True  # True: スムーズな移動、False: 直接ジャンプ
                
                # goHome メソッドを実行
                result = viewport.goHome(transition)
                
                if result:
                    futil.log("ホームビューに正常に移動しました", adsk.core.LogLevels.InfoLogLevel)
                else:
                    futil.log("ホームビューへの移動が失敗しました", adsk.core.LogLevels.WarningLogLevel)
                    
                # 画面を更新
                viewport.refresh()
                
                return
            except Exception as e:
                futil.log(f"ホームビュー移動中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.WarningLogLevel)
                
            # 以前の方法をバックアップとして残す（APIが失敗した場合）
            try:
                # コマンドIDを使用してホームビューコマンドを実行
                ui.commandDefinitions.itemById('ViewHomeCmd').execute()
                futil.log("ホームビューコマンドを実行しました（バックアップ方法）", adsk.core.LogLevels.InfoLogLevel)
            except Exception as e:
                futil.log(f"すべてのホームビュー移動方法が失敗しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
                
        except Exception as e:
            futil.log(f"ホームビューへの移動中にエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)

    @staticmethod
    def update_camera_position(joystick_x: float, joystick_y: float) -> None:
        try:
            # 入力がほぼゼロの場合は処理をスキップ（パフォーマンス向上）
            if abs(joystick_x) < 0.005 and abs(joystick_y) < 0.005:  # 閾値を上げてさらに軽量化
                return
            
            camera: adsk.core.Camera = app.activeViewport.camera
            if not camera:
                return

            # カメラの滑らかな遷移を無効化
            camera.isSmoothTransition = False
            
            eye: adsk.core.Point3D = camera.eye
            target: adsk.core.Point3D = camera.target
            up: adsk.core.Vector3D = camera.upVector

            # シンプルな回転スケール計算
            rotation_scale = CameraController.rotation_scale * 0.3  # さらに縮小して軽量化
            
            # 単純な線形スケーリング（非線形処理を削除）
            joystick_x_scaled = joystick_x * rotation_scale
            joystick_y_scaled = joystick_y * rotation_scale
            
            # 視線方向とright方向の計算（シンプル化）
            forward: adsk.core.Vector3D = target.vectorTo(eye)
            forward.normalize()
            
            right: adsk.core.Vector3D = forward.crossProduct(up)
            # rightベクトルが無効な場合のみ簡単な修正
            if right.length < 0.001:
                right = adsk.core.Vector3D.create(1, 0, 0)  # X軸を使用
            else:
                right.normalize()

            # シンプルな回転処理（特異点検出なし）
            if getattr(config, 'USE_Z_AXIS_ROTATION', False):
                # Z軸回転モード：シンプル版
                world_z_axis = adsk.core.Vector3D.create(0, 0, 1)
                z_direction = 1 if up.dotProduct(world_z_axis) >= 0 else -1
                
                q_vertical: Quaternion = Quaternion.from_axis_angle(right, joystick_y_scaled)
                q_horizontal: Quaternion = Quaternion.from_axis_angle(world_z_axis, z_direction * -joystick_x_scaled)
            else:
                # 通常モード：シンプル版
                q_vertical: Quaternion = Quaternion.from_axis_angle(right, joystick_y_scaled)
                q_horizontal: Quaternion = Quaternion.from_axis_angle(up, -joystick_x_scaled)

            # 回転を結合
            q: Quaternion = q_horizontal * q_vertical

            # eye位置の回転
            eye_vector: adsk.core.Vector3D = target.vectorTo(eye)
            rotated_eye_vector: adsk.core.Vector3D = q.transform_vector(eye_vector)
            new_eye: adsk.core.Point3D = target.copy()
            new_eye.translateBy(rotated_eye_vector)

            # upベクトルの回転（シンプル版）
            rotated_up: adsk.core.Vector3D = q.transform_vector(up)

            # カメラの新しい位置と向きを設定
            camera.eye = new_eye
            camera.upVector = rotated_up
            app.activeViewport.camera = camera
            
            # 画面更新
            app.activeViewport.refresh()

        except Exception as e:
            # エラーログも簡素化
            if config.DEBUG:
                futil.log(f'Camera update error: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)

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
                viewport.fit()
                futil.log("フィットビューを実行しました", adsk.core.LogLevels.InfoLogLevel)
            # ビューキューブ機能（Fusion 360のビューキューブと同等）
            elif function_name == "viewcube_front":
                self._set_viewcube_orientation(adsk.core.ViewOrientations.FrontViewOrientation)
                futil.log("ビューキューブ前面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_back":
                self._set_viewcube_orientation(adsk.core.ViewOrientations.BackViewOrientation)
                futil.log("ビューキューブ背面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_left":
                self._set_viewcube_orientation(adsk.core.ViewOrientations.LeftViewOrientation)
                futil.log("ビューキューブ左面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_right":
                self._set_viewcube_orientation(adsk.core.ViewOrientations.RightViewOrientation)
                futil.log("ビューキューブ右面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_top":
                self._set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
                futil.log("ビューキューブ上面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "viewcube_bottom":
                self._set_viewcube_orientation(adsk.core.ViewOrientations.BottomViewOrientation)
                futil.log("ビューキューブ下面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "iso_view":
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
                futil.log("アイソメトリックビューを実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "nearest_viewcube":
                self._move_to_nearest_viewcube_face()
                futil.log("最寄りのビューキューブ面を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_right":
                self.rotate_screen_right()
                futil.log("画面右回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_left":
                self.rotate_screen_left()
                futil.log("画面左回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_right":
                self.smart_rotate_right()
                futil.log("スマート右回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_left":
                self.smart_rotate_left()
                futil.log("スマート左回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_up":
                self.rotate_screen_up()
                futil.log("画面上回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_down":
                self.rotate_screen_down()
                futil.log("画面下回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_up":
                self.smart_rotate_up()
                futil.log("スマート上回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_down":
                self.smart_rotate_down()
                futil.log("スマート下回転90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_clockwise":
                self.rotate_screen_clockwise()
                futil.log("画面垂直時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "rotate_screen_counter_clockwise":
                self.rotate_screen_counter_clockwise()
                futil.log("画面垂直反時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_clockwise":
                self.smart_rotate_clockwise()
                futil.log("スマート垂直時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            elif function_name == "smart_rotate_counter_clockwise":
                self.smart_rotate_counter_clockwise()
                futil.log("スマート垂直反時計回り90度を実行しました", adsk.core.LogLevels.InfoLogLevel)
            else:
                futil.log(f"未知の機能: {function_name}", adsk.core.LogLevels.WarningLogLevel)
                return

            # ビューポートを更新
            viewport.refresh()

        except Exception as e:
            futil.log(f'ボタン機能の実行に失敗しました ({function_name}): {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)

    def _set_viewcube_orientation(self, orientation: adsk.core.ViewOrientations) -> None:
        """ビューキューブの方向設定（Fusion 360のビューキューブクリックと同等）"""
        try:
            viewport = app.activeViewport
            if not viewport:
                futil.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # カメラオブジェクトを取得して方向を設定
            camera = viewport.camera
            
            # ビューキューブ移動時は滑らかな遷移を有効にする
            camera.isSmoothTransition = True
            
            camera.viewOrientation = orientation
            
            # カメラをビューポートに適用
            viewport.camera = camera
            
            # 必要に応じてビューをフィット
            viewport.fit()
            
            # ビューポートを更新
            viewport.refresh()
            
        except Exception as e:
            futil.log(f'ビューキューブ方向設定に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)

    def _move_to_nearest_viewcube_face(self) -> None:
        """現在のカメラ視点から最も近いViewCube面に移動する"""
        try:
            viewport = app.activeViewport
            if not viewport:
                futil.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                futil.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
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
            futil.log(f"現在のviewOrientation: {current_orientation_name}({current_orientation})", adsk.core.LogLevels.InfoLogLevel)

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
            futil.log(f"現在の視線方向: [{view_direction.x:.3f}, {view_direction.y:.3f}, {view_direction.z:.3f}]", adsk.core.LogLevels.InfoLogLevel)
            futil.log(f"最寄りのViewCube面: {selected_name} (類似度: {max_dot_product:.3f})", adsk.core.LogLevels.InfoLogLevel)
            
            # 最寄りの面に移動
            futil.log(f"最寄りのViewCube面 '{selected_name}' に移動を実行します", adsk.core.LogLevels.InfoLogLevel)
            self._set_viewcube_orientation(nearest_orientation)
            futil.log(f"ViewCube面 '{selected_name}' への移動が完了しました", adsk.core.LogLevels.InfoLogLevel)
            
        except Exception as e:
            futil.log(f'最寄りのViewCube面への移動に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)

    def rotate_screen_right(self) -> None:
        """画面の垂直軸で右に90度回転（直接回転）"""
        self._rotate_screen_by_angle(90.0)
    
    def rotate_screen_left(self) -> None:
        """画面の垂直軸で左に90度回転（直接回転）"""
        self._rotate_screen_by_angle(-90.0)
    
    def smart_rotate_right(self) -> None:
        """スマート右回転：ArbitraryViewOrientation（任意の向き）の場合は最寄り面に移動してから90度回転"""
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            futil.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから右回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            futil.log("現在標準ViewCube面を向いているため、直接右回転します", adsk.core.LogLevels.InfoLogLevel)
        self._rotate_screen_by_angle(90.0)
    
    def smart_rotate_left(self) -> None:
        """スマート左回転：ArbitraryViewOrientation（任意の向き）の場合は最寄り面に移動してから90度回転"""
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            futil.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから左回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            futil.log("現在標準ViewCube面を向いているため、直接左回転します", adsk.core.LogLevels.InfoLogLevel)
        self._rotate_screen_by_angle(-90.0)
    
    def rotate_screen_up(self) -> None:
        """画面の水平軸で上に90度回転（直接回転）"""
        self._rotate_screen_vertical_by_angle(90.0)
    
    def rotate_screen_down(self) -> None:
        """画面の水平軸で下に90度回転（直接回転）"""
        self._rotate_screen_vertical_by_angle(-90.0)
    
    def smart_rotate_up(self) -> None:
        """スマート上回転：ArbitraryViewOrientation（任意の向き）の場合は最寄り面に移動してから90度回転"""
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            futil.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから上回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            futil.log("現在標準ViewCube面を向いているため、直接上回転します", adsk.core.LogLevels.InfoLogLevel)
        self._rotate_screen_vertical_by_angle(90.0)
    
    def smart_rotate_down(self) -> None:
        """スマート下回転：ArbitraryViewOrientation（任意の向き）の場合は最寄り面に移動してから90度回転"""
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            futil.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから下回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            futil.log("現在標準ViewCube面を向いているため、直接下回転します", adsk.core.LogLevels.InfoLogLevel)
        self._rotate_screen_vertical_by_angle(-90.0)
    
    def rotate_screen_clockwise(self) -> None:
        """画面垂直方向（画面Z軸周り）に時計回りに90度回転"""
        self._rotate_screen_z_by_angle(90.0)
    
    def rotate_screen_counter_clockwise(self) -> None:
        """画面垂直方向（画面Z軸周り）に反時計回りに90度回転"""
        self._rotate_screen_z_by_angle(-90.0)
    
    def smart_rotate_clockwise(self) -> None:
        """スマート垂直時計回り回転：ArbitraryViewOrientation（任意の向き）の場合は最寄り面に移動してから90度回転"""
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            futil.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから垂直時計回り回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            futil.log("現在標準ViewCube面を向いているため、直接垂直時計回り回転します", adsk.core.LogLevels.InfoLogLevel)
        self._rotate_screen_z_by_angle(90.0)
    
    def smart_rotate_counter_clockwise(self) -> None:
        """スマート垂直反時計回り回転：ArbitraryViewOrientation（任意の向き）の場合は最寄り面に移動してから90度回転"""
        is_on_face = self._is_on_viewcube_face()
        if not is_on_face:
            futil.log("現在任意の向き（ArbitraryViewOrientation）のため、最寄りViewCube面に移動してから垂直反時計回り回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        else:
            futil.log("現在標準ViewCube面を向いているため、直接垂直反時計回り回転します", adsk.core.LogLevels.InfoLogLevel)
        self._rotate_screen_z_by_angle(-90.0)
    
    def _rotate_screen_by_angle(self, angle_degrees: float) -> None:
        """ViewCube面の左右矢印と同等の回転（現在のViewCube面を基準とした左右回転）"""
        try:
            viewport = app.activeViewport
            if not viewport:
                futil.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                futil.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # 現在のカメラパラメータを取得
            eye = camera.eye
            target = camera.target
            up_vector = camera.upVector
            
            # 角度をラジアンに変換
            import math
            angle_radians = math.radians(angle_degrees)
            
            # up_vector軸周りにeyeの位置を回転（ViewCube左右矢印と同等）
            rotation_quaternion = Quaternion.from_axis_angle(up_vector, angle_radians)
            
            # targetを原点としてeyeの相対位置を回転
            eye_relative = target.vectorTo(eye)
            rotated_eye_relative = rotation_quaternion.transform_vector(eye_relative)
            
            # 新しいeye位置を計算
            new_eye = target.copy()
            new_eye.translateBy(rotated_eye_relative)
            
            # 新しいカメラパラメータを設定
            camera.eye = new_eye
            camera.target = target
            camera.upVector = up_vector  # up_vectorは変更しない
            
            # スムースな移動を有効にして適用
            camera.isSmoothTransition = True
            viewport.camera = camera
            viewport.refresh()
            
            futil.log(f"ViewCube面を基準に左右{angle_degrees}度回転しました", adsk.core.LogLevels.InfoLogLevel)
            
        except Exception as e:
            futil.log(f'ViewCube面左右回転に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def _rotate_screen_vertical_by_angle(self, angle_degrees: float) -> None:
        """ViewCube面の上下矢印と同等の回転（現在のViewCube面を基準とした上下回転）"""
        try:
            viewport = app.activeViewport
            if not viewport:
                futil.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                futil.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # 現在のカメラパラメータを取得
            eye = camera.eye
            target = camera.target
            up_vector = camera.upVector
            
            # 視線方向ベクトルを計算
            view_direction = eye.vectorTo(target)
            view_direction.normalize()
            
            # 世界座標系のZ軸（0, 0, 1）
            world_z = adsk.core.Vector3D.create(0, 0, 1)
            
            # ViewCube面の右方向ベクトルを計算（視線方向とup_vectorの外積）
            right_vector = view_direction.crossProduct(up_vector)
            # 外積の長さがゼロに近い場合の安全チェック
            if right_vector.length < 0.01:
                # 代替として世界座標系のX軸を使用
                right_vector = adsk.core.Vector3D.create(1, 0, 0)
            else:
                right_vector.normalize()
            
            # 角度をラジアンに変換
            import math
            angle_radians = math.radians(angle_degrees)
            
            # 右方向軸周りにeyeの位置を回転
            rotation_quaternion = Quaternion.from_axis_angle(right_vector, angle_radians)
            
            # targetを原点としてeyeの相対位置を回転
            eye_relative = target.vectorTo(eye)
            rotated_eye_relative = rotation_quaternion.transform_vector(eye_relative)
            
            # 新しいeye位置を計算
            new_eye = target.copy()
            new_eye.translateBy(rotated_eye_relative)
            
            # 新しいup_vectorも同じ軸周りに回転
            rotated_up = rotation_quaternion.transform_vector(up_vector)
            
            # 新しいカメラパラメータを設定
            camera.eye = new_eye
            camera.target = target
            camera.upVector = rotated_up
            
            # スムースな移動を有効にして適用
            camera.isSmoothTransition = True
            viewport.camera = camera
            viewport.refresh()
            
            futil.log(f"ViewCube面を基準に上下{angle_degrees}度回転しました", adsk.core.LogLevels.InfoLogLevel)
            
        except Exception as e:
            futil.log(f'ViewCube面上下回転に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def _rotate_screen_z_by_angle(self, angle_degrees: float) -> None:
        """画面垂直方向（画面のZ軸周り）に指定角度回転する
        
        Args:
            angle_degrees: 回転角度（度数法）。正の値で時計回り、負の値で反時計回り
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                futil.log("No active viewport found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            camera = viewport.camera
            if not camera:
                futil.log("No active camera found.", adsk.core.LogLevels.WarningLogLevel)
                return
            
            # 現在のカメラパラメータを取得
            eye = camera.eye
            target = camera.target
            up_vector = camera.upVector
            
            # 視線方向ベクトルを計算（カメラから見た前方向）
            view_direction = eye.vectorTo(target)
            view_direction.normalize()
            
            # 角度をラジアンに変換
            import math
            angle_radians = math.radians(angle_degrees)
            
            # 視線方向軸周りにup_vectorを回転
            rotation_quaternion = Quaternion.from_axis_angle(view_direction, angle_radians)
            
            # up_vectorを回転
            rotated_up = rotation_quaternion.transform_vector(up_vector)
            
            # 新しいカメラパラメータを設定（eyeとtargetは変更せず、up_vectorのみ回転）
            camera.eye = eye
            camera.target = target
            camera.upVector = rotated_up
            
            # スムースな移動を有効にして適用
            camera.isSmoothTransition = True
            viewport.camera = camera
            viewport.refresh()
            
            futil.log(f"画面垂直方向（Z軸周り）に{angle_degrees}度回転しました", adsk.core.LogLevels.InfoLogLevel)
            
        except Exception as e:
            futil.log(f'画面垂直方向回転に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def _is_on_viewcube_face(self) -> bool:
        """現在の視点がViewCube面に向いているかどうかを判定する
        
        Camera.viewOrientationを使用してArbitraryViewOrientation（値:0）でないかをチェック
        """
        try:
            viewport = app.activeViewport
            if not viewport:
                return False
            
            camera = viewport.camera
            if not camera:
                return False
            
            # Camera.viewOrientationで現在の向きを取得
            current_orientation = camera.viewOrientation
            
            # ArbitraryViewOrientation（値:0）でない場合は標準的なViewCube面を向いている
            is_on_standard_face = current_orientation != adsk.core.ViewOrientations.ArbitraryViewOrientation
            
            # デバッグ情報を出力
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
            
            orientation_name = orientation_names.get(current_orientation, f"不明({current_orientation})")
            
            if config.DEBUG:
                futil.log(f"ViewCube面判定: 現在の向き={orientation_name}({current_orientation}), "
                         f"判定={'標準面向き' if is_on_standard_face else '任意の向き'}", 
                         adsk.core.LogLevels.InfoLogLevel)
            
            return is_on_standard_face
            
        except Exception as e:
            futil.log(f'ViewCube面判定でエラー: {str(e)}', adsk.core.LogLevels.WarningLogLevel)
            return False
