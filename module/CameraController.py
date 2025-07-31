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
            if abs(joystick_x) < 0.001 and abs(joystick_y) < 0.001:
                return
            
            # デバッグモードがオンの場合のみ表示
            if config.DEBUG and (abs(joystick_x) > 0.5 or abs(joystick_y) > 0.5):
                futil.log(f'Joystick input - X: {joystick_x:.4f}, Y: {joystick_y:.4f}')
            
            camera: adsk.core.Camera = app.activeViewport.camera
            if not camera:
                futil.log('No active camera found.')
                return

            # カメラの滑らかな遷移を無効化（ログなし）
            camera.isSmoothTransition = False
            
            eye: adsk.core.Point3D = camera.eye
            target: adsk.core.Point3D = camera.target
            up: adsk.core.Vector3D = camera.upVector

            # ベクトル計算 - 入力をスケーリングして小さくする
            rotation_scale = CameraController.rotation_scale * 0.5  # 回転スケールを半分に
            
            # 入力値にさらに非線形処理を適用して大きな動きを抑制
            joystick_x_scaled = joystick_x * abs(joystick_x) * rotation_scale  
            joystick_y_scaled = joystick_y * abs(joystick_y) * rotation_scale
            
            forward: adsk.core.Vector3D = target.vectorTo(eye)
            forward.normalize()

            # 安全なrightベクトルの計算（ViewCubeコーナー対応）
            right: adsk.core.Vector3D = forward.crossProduct(up)
            
            # rightベクトルの長さをチェックして特異点を検出
            right_length = right.length
            if right_length < 0.01:  # ほぼゼロの場合（特異点）
                # 代替のrightベクトルを計算
                world_z_axis = adsk.core.Vector3D.create(0, 0, 1)
                world_x_axis = adsk.core.Vector3D.create(1, 0, 0)
                world_y_axis = adsk.core.Vector3D.create(0, 1, 0)
                
                # forwardと最も垂直に近い世界軸を見つける
                x_dot = abs(forward.dotProduct(world_x_axis))
                y_dot = abs(forward.dotProduct(world_y_axis))
                z_dot = abs(forward.dotProduct(world_z_axis))
                
                # 最も垂直に近い軸を使用してrightベクトルを計算
                if x_dot < y_dot and x_dot < z_dot:
                    right = forward.crossProduct(world_x_axis)
                elif y_dot < z_dot:
                    right = forward.crossProduct(world_y_axis)
                else:
                    right = forward.crossProduct(world_z_axis)
                
                # 再度長さをチェック
                if right.length < 0.01:
                    # すべて失敗した場合は、upベクトルと垂直な任意のベクトルを使用
                    if abs(up.x) < 0.9:
                        right = adsk.core.Vector3D.create(1, 0, 0)
                    else:
                        right = adsk.core.Vector3D.create(0, 1, 0)
                
                if config.DEBUG:
                    futil.log(f'ViewCube角での特異点を検出、代替rightベクトルを使用: length={right_length:.6f}', adsk.core.LogLevels.InfoLogLevel)
            
            right.normalize()

            # ViewCube角での安全な回転処理
            # 複数の特異点を検出して適切な回転軸を選択
            world_z_axis = adsk.core.Vector3D.create(0, 0, 1)
            world_x_axis = adsk.core.Vector3D.create(1, 0, 0)
            world_y_axis = adsk.core.Vector3D.create(0, 1, 0)
            
            # 視線方向と各世界軸との内積を計算
            forward_x_dot = abs(forward.dotProduct(world_x_axis))
            forward_y_dot = abs(forward.dotProduct(world_y_axis))
            forward_z_dot = abs(forward.dotProduct(world_z_axis))
            
            # upベクトルと各世界軸との内積も計算
            up_x_dot = abs(up.dotProduct(world_x_axis))
            up_y_dot = abs(up.dotProduct(world_y_axis))
            up_z_dot = abs(up.dotProduct(world_z_axis))
            
            # 特異点の検出（任意の軸に対して80%以上平行）
            singularity_threshold = 0.8
            is_forward_singular = (forward_x_dot > singularity_threshold or 
                                 forward_y_dot > singularity_threshold or 
                                 forward_z_dot > singularity_threshold)
            is_up_singular = (up_x_dot > singularity_threshold or 
                            up_y_dot > singularity_threshold or 
                            up_z_dot > singularity_threshold)
            
            # ViewCube角での特異点処理
            if is_forward_singular or is_up_singular or right_length < 0.05:
                # 特異点付近では、世界座標軸を使用した安全な回転
                # デバッグログの頻度制限（10回に1回のみ表示）
                if config.DEBUG and not hasattr(CameraController, '_debug_counter'):
                    CameraController._debug_counter = 0
                if config.DEBUG:
                    CameraController._debug_counter += 1
                    if CameraController._debug_counter % 10 == 1:  # 10回に1回のみログ出力
                        futil.log(f'ViewCube角特異点検出中 (#{CameraController._debug_counter})', adsk.core.LogLevels.InfoLogLevel)
                
                # 入力スケールを大幅に縮小して安定化
                safe_x_scale = joystick_x_scaled * 0.1
                safe_y_scale = joystick_y_scaled * 0.1
                
                # 世界座標軸を使用した単純な回転
                q_vertical: Quaternion = Quaternion.from_axis_angle(world_x_axis, safe_y_scale)
                q_horizontal: Quaternion = Quaternion.from_axis_angle(world_z_axis, -safe_x_scale)
                
            elif getattr(config, 'USE_Z_AXIS_ROTATION', False):
                # Z軸回転モード（特異点でない場合）
                if forward_z_dot > 0.95:  # Z軸特異点付近
                    # Z軸特異点付近では通常回転
                    q_vertical: Quaternion = Quaternion.from_axis_angle(right, joystick_y_scaled)
                    q_horizontal: Quaternion = Quaternion.from_axis_angle(up, -joystick_x_scaled)
                    
                    if config.DEBUG:
                        futil.log(f'Z軸特異点付近のため通常回転モードを使用 (Z軸内積: {forward_z_dot:.3f})', adsk.core.LogLevels.InfoLogLevel)
                else:
                    # 通常のZ軸回転処理
                    z_direction = 1 if up.dotProduct(world_z_axis) >= 0 else -1
                    
                    q_vertical: Quaternion = Quaternion.from_axis_angle(right, joystick_y_scaled)
                    q_horizontal: Quaternion = Quaternion.from_axis_angle(world_z_axis, z_direction * -joystick_x_scaled)
                    
                    if config.DEBUG and abs(joystick_x) > 0.5:
                        futil.log(f'Z軸回転モード - Z方向: {z_direction}', adsk.core.LogLevels.InfoLogLevel)
            else:
                # 通常モード（特異点でない場合）
                q_vertical: Quaternion = Quaternion.from_axis_angle(right, joystick_y_scaled)
                q_horizontal: Quaternion = Quaternion.from_axis_angle(up, -joystick_x_scaled)

            # 回転を結合
            q: Quaternion = q_horizontal * q_vertical

            # Rotate the eye position around the target
            eye_vector: adsk.core.Vector3D = target.vectorTo(eye)  # 方向を修正
            rotated_eye_vector: adsk.core.Vector3D = q.transform_vector(eye_vector)
            new_eye: adsk.core.Point3D = target.copy()
            new_eye.translateBy(rotated_eye_vector)

            # upベクトルの安全な更新処理
            if is_forward_singular or is_up_singular or right_length < 0.05:
                # 特異点付近では既存のupベクトルを維持して安定化
                # 小さな調整のみ適用
                adjustment_factor = 0.05
                temp_up = q.transform_vector(up)
                
                # 既存のupベクトルと変換後のupベクトンをブレンド
                rotated_up = adsk.core.Vector3D.create(
                    up.x * (1 - adjustment_factor) + temp_up.x * adjustment_factor,
                    up.y * (1 - adjustment_factor) + temp_up.y * adjustment_factor,
                    up.z * (1 - adjustment_factor) + temp_up.z * adjustment_factor
                )
                rotated_up.normalize()
                
                # デバッグログは100回に1回のみ（さらに頻度制限）
                if config.DEBUG and hasattr(CameraController, '_debug_counter') and CameraController._debug_counter % 100 == 1:
                    futil.log(f'upベクトル安定化処理中', adsk.core.LogLevels.InfoLogLevel)
            else:
                # 通常時の処理
                rotated_up: adsk.core.Vector3D = q.transform_vector(up)
            
            # Z軸回転モードの場合、ジョイスティック入力があるときのみ画面垂直方向の傾きを補正
            if getattr(config, 'USE_Z_AXIS_ROTATION', False) and (abs(joystick_x) > 0.01 or abs(joystick_y) > 0.01):
                # 視線方向ベクトルを取得
                view_direction = new_eye.vectorTo(target)
                view_direction.normalize()
                
                # ワールドZ軸
                world_z_axis = adsk.core.Vector3D.create(0, 0, 1)
                
                # Z軸特異点（ジンバルロック）の検出
                # 視線方向がZ軸とほぼ平行な場合
                import math
                dot_with_z = abs(view_direction.dotProduct(world_z_axis))
                is_near_singularity = dot_with_z > 0.95  # 約18度以内
                
                if not is_near_singularity:
                    # 通常時のみ傾き補正を実行
                    # 現在の傾きを検査（視線方向とワールドZ軸に垂直な平面での右方向ベクトルを計算）
                    ideal_right = view_direction.crossProduct(world_z_axis)
                    
                    # 外積の長さが十分大きい場合のみ処理
                    if ideal_right.length > 0.1:
                        ideal_right.normalize()
                        
                        # 理想的なupベクトル（傾きなし）を計算
                        ideal_up = ideal_right.crossProduct(view_direction)
                        ideal_up.normalize()
                        
                        # 上下反転時は理想的なupベクトルの向きを調整
                        if view_direction.dotProduct(world_z_axis) < -0.9:  # ほぼ下を向いている
                            ideal_up.scaleBy(-1)  # upベクトルを反転
                        
                        # 現在のupベクトルと理想的なupベクトルの角度差を計算して傾きを判定
                        dot_product = rotated_up.dotProduct(ideal_up)
                        angle_diff = abs(1.0 - dot_product)  # 1に近いほど傾きが少ない
                        
                        # 傾きがデッドゾーン閾値の2倍以上ある場合のみ補正（閾値を上げて過敏な反応を抑制）
                        deadzone_threshold = getattr(config, 'DEAD_ZONE', 0.1) * 2.0
                        if angle_diff > deadzone_threshold:
                            # 急激な補正を避けるため、段階的に補正
                            blend_factor = 0.3  # 30%ずつ理想値に近づける
                            rotated_up.x = rotated_up.x * (1 - blend_factor) + ideal_up.x * blend_factor
                            rotated_up.y = rotated_up.y * (1 - blend_factor) + ideal_up.y * blend_factor
                            rotated_up.z = rotated_up.z * (1 - blend_factor) + ideal_up.z * blend_factor
                            rotated_up.normalize()
                            
                            if config.DEBUG:
                                futil.log(f'Z軸回転モード: 傾きを段階的に補正 (角度差: {angle_diff:.3f}, 閾値: {deadzone_threshold:.3f})', adsk.core.LogLevels.InfoLogLevel)
                        elif config.DEBUG and angle_diff > deadzone_threshold * 0.5:
                            futil.log(f'Z軸回転モード: 軽微な傾き検出 (角度差: {angle_diff:.3f}, 閾値: {deadzone_threshold:.3f}) - 補正なし', adsk.core.LogLevels.InfoLogLevel)
                else:
                    # 特異点付近では傾き補正を行わない
                    if config.DEBUG:
                        futil.log(f'Z軸回転モード: 特異点付近のため傾き補正をスキップ (Z軸との内積: {dot_with_z:.3f})', adsk.core.LogLevels.InfoLogLevel)
            
            # 極端な座標変化のチェック
            if abs(new_eye.x) > 1000 or abs(new_eye.y) > 1000 or abs(new_eye.z) > 1000:
                futil.log("Extreme position detected, skipping update", adsk.core.LogLevels.WarningLogLevel)
                return
                
            # x,z座標の符号が急に変わる問題を検出
            if eye.x * new_eye.x < 0 and eye.z * new_eye.z < 0:
                futil.log("Sign flip detected in both X and Z axes, applying correction", adsk.core.LogLevels.WarningLogLevel)
                # 動きを抑制
                new_eye = eye.copy()
                return
                
            # カメラの新しい位置と向きを設定
            camera.eye = new_eye
            camera.upVector = rotated_up
            camera.isSmoothTransition = False  # 滑らかな遷移を無効化
            app.activeViewport.camera = camera
            
            # ビューポートの明示的な更新を強制（デバッグログに関わらず反映）
            app.activeViewport.refresh()

        except:
            futil.log(f'Failed to update camera: {traceback.format_exc()}', adsk.core.LogLevels.ErrorLogLevel)

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
            orientation_names = {
                adsk.core.ViewOrientations.FrontViewOrientation: "前面",
                adsk.core.ViewOrientations.BackViewOrientation: "背面", 
                adsk.core.ViewOrientations.LeftViewOrientation: "左面",
                adsk.core.ViewOrientations.RightViewOrientation: "右面",
                adsk.core.ViewOrientations.TopViewOrientation: "上面",
                adsk.core.ViewOrientations.BottomViewOrientation: "下面"
            }
            
            selected_name = orientation_names.get(nearest_orientation, "不明")
            futil.log(f"現在の視線方向: [{view_direction.x:.3f}, {view_direction.y:.3f}, {view_direction.z:.3f}]", adsk.core.LogLevels.InfoLogLevel)
            futil.log(f"最寄りのViewCube面: {selected_name} (類似度: {max_dot_product:.3f})", adsk.core.LogLevels.InfoLogLevel)
            
            # 最寄りの面に移動
            self._set_viewcube_orientation(nearest_orientation)
            
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
        """スマート右回転：ViewCube面でない場合は最寄り面に移動してから90度回転"""
        if not self._is_on_viewcube_face():
            futil.log("現在ViewCube面を向いていないため、最寄り面に移動してから回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        self._rotate_screen_by_angle(90.0)
    
    def smart_rotate_left(self) -> None:
        """スマート左回転：ViewCube面でない場合は最寄り面に移動してから90度回転"""
        if not self._is_on_viewcube_face():
            futil.log("現在ViewCube面を向いていないため、最寄り面に移動してから回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        self._rotate_screen_by_angle(-90.0)
    
    def rotate_screen_up(self) -> None:
        """画面の水平軸で上に90度回転（直接回転）"""
        self._rotate_screen_vertical_by_angle(90.0)
    
    def rotate_screen_down(self) -> None:
        """画面の水平軸で下に90度回転（直接回転）"""
        self._rotate_screen_vertical_by_angle(-90.0)
    
    def smart_rotate_up(self) -> None:
        """スマート上回転：ViewCube面でない場合は最寄り面に移動してから90度回転"""
        if not self._is_on_viewcube_face():
            futil.log("現在ViewCube面を向いていないため、最寄り面に移動してから回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        self._rotate_screen_vertical_by_angle(90.0)
    
    def smart_rotate_down(self) -> None:
        """スマート下回転：ViewCube面でない場合は最寄り面に移動してから90度回転"""
        if not self._is_on_viewcube_face():
            futil.log("現在ViewCube面を向いていないため、最寄り面に移動してから回転します", adsk.core.LogLevels.InfoLogLevel)
            self._move_to_nearest_viewcube_face()
            # 少し待ってから回転（カメラの移動完了を待つ）
            import time
            time.sleep(0.1)
        self._rotate_screen_vertical_by_angle(-90.0)
    
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
            
            # Z軸特異点（ジンバルロック）の検出
            # 視線方向がZ軸とほぼ平行な場合
            import math
            dot_with_z = abs(view_direction.dotProduct(world_z))
            is_near_singularity = dot_with_z > 0.95  # 約18度以内
            
            if is_near_singularity:
                # 特異点付近では、画面の水平方向（X軸方向）を回転軸として使用
                # 現在のup_vectorから水平成分を抽出して回転軸を決定
                horizontal_up = adsk.core.Vector3D.create(up_vector.x, up_vector.y, 0)
                if horizontal_up.length > 0.1:
                    horizontal_up.normalize()
                    # 水平なup_vectorに垂直な方向を右方向として使用
                    right_vector = adsk.core.Vector3D.create(-horizontal_up.y, horizontal_up.x, 0)
                    right_vector.normalize()
                else:
                    # 完全に上面または下面を見ている場合、X軸を右方向とする
                    right_vector = adsk.core.Vector3D.create(1, 0, 0)
            else:
                # 通常の場合：ViewCube面の右方向ベクトルを計算（視線方向とup_vectorの外積）
                right_vector = view_direction.crossProduct(up_vector)
                # 外積の長さがゼロに近い場合の安全チェック
                if right_vector.length < 0.01:
                    # 代替として世界座標系のX軸を使用
                    right_vector = adsk.core.Vector3D.create(1, 0, 0)
                else:
                    right_vector.normalize()
            
            # 角度をラジアンに変換
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
            
            # 水平保持：Z成分をリセットして水平を保つ（ユーザー要求）
            # ただし、完全な上下逆転は許容する
            if not is_near_singularity:
                # 通常時は水平保持のためZ成分の大幅な変化を制限
                if abs(rotated_up.z) < 0.7:  # 45度以下の傾きの場合のみ水平化
                    rotated_up.z = 0
                    if rotated_up.length > 0.01:
                        rotated_up.normalize()
                    else:
                        # 安全のため、元のup_vectorを使用
                        rotated_up = up_vector
            
            # 新しいカメラパラメータを設定
            camera.eye = new_eye
            camera.target = target
            camera.upVector = rotated_up
            
            # スムースな移動を有効にして適用
            camera.isSmoothTransition = True
            viewport.camera = camera
            viewport.refresh()
            
            futil.log(f"ViewCube面を基準に上下{angle_degrees}度回転しました（特異点対応: {is_near_singularity}）", adsk.core.LogLevels.InfoLogLevel)
            
        except Exception as e:
            futil.log(f'ViewCube面上下回転に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    def _is_on_viewcube_face(self, tolerance: float = 0.9) -> bool:
        """現在の視点がViewCube面に近いかどうかを判定する"""
        try:
            viewport = app.activeViewport
            if not viewport:
                return False
            
            camera = viewport.camera
            if not camera:
                return False
            
            # カメラの視線方向ベクトルを取得
            eye = camera.eye
            target = camera.target
            view_direction = target.vectorTo(eye)
            view_direction.normalize()
            
            # 標準的なViewCube面の方向ベクトル
            standard_directions = [
                adsk.core.Vector3D.create(0, -1, 0),  # 前面
                adsk.core.Vector3D.create(0, 1, 0),   # 背面
                adsk.core.Vector3D.create(-1, 0, 0),  # 左面
                adsk.core.Vector3D.create(1, 0, 0),   # 右面
                adsk.core.Vector3D.create(0, 0, 1),   # 上面
                adsk.core.Vector3D.create(0, 0, -1)   # 下面
            ]
            
            # いずれかの面と十分に近い方向を向いているかチェック
            for direction in standard_directions:
                dot_product = view_direction.dotProduct(direction)
                if dot_product > tolerance:
                    return True
            
            return False
            
        except Exception as e:
            futil.log(f'ViewCube面判定でエラー: {str(e)}', adsk.core.LogLevels.WarningLogLevel)
            return False
