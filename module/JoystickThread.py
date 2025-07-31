import threading
import time
import traceback
import adsk.core
from ..lib import fusionAddInUtils as futil
from .JoystickManager import JoystickManager
from .SharedState import shared_state
from .. import config
import time

# アプリケーションとUIの取得
app = adsk.core.Application.get()
ui = app.userInterface

class JoystickThread(threading.Thread):
    def __init__(self, joystick_manager: JoystickManager, dead_zone: float = None):
        super().__init__(daemon=True)
        self.joystick_manager = joystick_manager
        self.stop_event = threading.Event()
        self.dead_zone = dead_zone if dead_zone is not None else getattr(config, 'DEAD_ZONE', 0.1)
        futil.log(f"JoystickThread initialized. Dead zone: {self.dead_zone}")

    def run(self) -> None:
        futil.log("JoystickThread started.")
        while not self.stop_event.is_set():
            try:
                # 毎ループでconfigからデッドゾーンを取得して更新された値を使用する
                from .. import config
                self.dead_zone = getattr(config, 'DEAD_ZONE', 0.1)
                
                # ジョイスティックの軸の値を取得
                axes = self.joystick_manager.get_axes()
                if axes:
                    joystick_x, joystick_y = axes
                    
                    # デバッグ用：ジョイスティック入力の詳細ログ
                    if config.DEBUG and (abs(joystick_x) > 0.01 or abs(joystick_y) > 0.01):
                        futil.log(f"Raw joystick input: X={joystick_x:.3f}, Y={joystick_y:.3f}", adsk.core.LogLevels.InfoLogLevel)
                else:
                    joystick_x, joystick_y = 0.0, 0.0

                # 反応曲線を取得
                response_curve = getattr(config, 'RESPONSE_CURVE', 1.0)
                
                # Apply dead zone
                if abs(joystick_x) < self.dead_zone:
                    joystick_x = 0.0
                if abs(joystick_y) < self.dead_zone:
                    joystick_y = 0.0
                
                # デッドゾーン適用後のデバッグログ
                if config.DEBUG and (abs(joystick_x) > 0.01 or abs(joystick_y) > 0.01):
                    futil.log(f"After deadzone (threshold={self.dead_zone:.3f}): X={joystick_x:.3f}, Y={joystick_y:.3f}", adsk.core.LogLevels.InfoLogLevel)
                    
                # 反応曲線を適用
                if joystick_x != 0.0:
                    # 入力値の符号を保持
                    sign_x = 1 if joystick_x > 0 else -1
                    # 曲線適用（1.0: 線形、>1.0: 二乗曲線、<1.0: 平方根曲線）
                    joystick_x = sign_x * (abs(joystick_x) ** response_curve)
                    
                if joystick_y != 0.0:
                    sign_y = 1 if joystick_y > 0 else -1
                    joystick_y = sign_y * (abs(joystick_y) ** response_curve)

                # ボタン機能が有効な場合のみ処理
                if config.BUTTON_ENABLED:
                    # 全ボタンの状態を取得して共有状態に保存
                    button_states = self.joystick_manager.get_all_button_states()
                    
                    # 現在押されているボタンの状態を更新
                    for i, is_pressed in enumerate(button_states):
                        shared_state.button_states[i] = is_pressed
                        
                    # デバッグ用：押されているボタンをログ出力
                    if config.DEBUG:
                        pressed_buttons = [i for i, pressed in enumerate(button_states) if pressed]
                        if pressed_buttons:
                            futil.log(f"押されているボタン: {pressed_buttons}", adsk.core.LogLevels.InfoLogLevel)
                else:
                    # ボタン機能が無効な場合は空の辞書
                    shared_state.button_states = {}

                # 十字キー機能が有効な場合のみ処理
                if getattr(config, 'DPAD_ENABLED', True):
                    # 十字キーの状態を取得して共有状態に保存
                    dpad_states = self.joystick_manager.get_dpad_button_states()
                    shared_state.dpad_states = dpad_states
                    
                    # デバッグ用：押されている十字キーをログ出力
                    if config.DEBUG:
                        pressed_dpad = [direction for direction, pressed in dpad_states.items() if pressed]
                        if pressed_dpad:
                            futil.log(f"押されている十字キー: {pressed_dpad}", adsk.core.LogLevels.InfoLogLevel)
                else:
                    # 十字キー機能が無効な場合は空の辞書
                    shared_state.dpad_states = {}

                # 入力をスムージングする
                # 前回の値と今回の値の間を取ることで急激な変化を防ぐ
                if hasattr(self, 'prev_x') and hasattr(self, 'prev_y'):
                    # 急激な変化を検出
                    if abs(joystick_x - self.prev_x) > 0.5 or abs(joystick_y - self.prev_y) > 0.5:
                        # デバッグモードがオンの場合のみログを表示
                        if getattr(config, 'DEBUG', False):
                            futil.log(f"Large input change detected: X {self.prev_x:.2f}->{joystick_x:.2f}, Y {self.prev_y:.2f}->{joystick_y:.2f}")
                        # 変化量を制限
                        joystick_x = self.prev_x + 0.1 * (joystick_x - self.prev_x)
                        joystick_y = self.prev_y + 0.1 * (joystick_y - self.prev_y)
                    else:
                        # 小さな変化はスムージング
                        joystick_x = self.prev_x * 0.7 + joystick_x * 0.3
                        joystick_y = self.prev_y * 0.7 + joystick_y * 0.3
                
                # 現在値を保存
                self.prev_x = joystick_x
                self.prev_y = joystick_y

                # 動きがある場合とその他の場合で更新頻度を変える
                if abs(joystick_x) > 0.001 or abs(joystick_y) > 0.001:  # 閾値を上げて微小入力をフィルタ
                    # 動きがある場合は更新して高頻度でポーリング
                    shared_state.joystick_x = joystick_x
                    shared_state.joystick_y = joystick_y
                    shared_state.is_dirty = True
                    
                    # デバッグ用：SharedStateへの更新ログ（頻度制限）
                    if config.DEBUG and not hasattr(self, '_log_counter'):
                        self._log_counter = 0
                    if config.DEBUG:
                        self._log_counter += 1
                        if self._log_counter % 50 == 1:  # 50回に1回のみログ出力
                            futil.log(f"SharedState更新中: X={joystick_x:.3f}, Y={joystick_y:.3f} (#{self._log_counter})", adsk.core.LogLevels.InfoLogLevel)
                    
                    # 動きがある場合は高頻度でポーリング（50Hz）
                    time.sleep(0.02)  # 20ms間隔でポーリング
                else:
                    # 動きがない場合：SharedStateをクリアして無駄な処理を防ぐ
                    if shared_state.joystick_x != 0.0 or shared_state.joystick_y != 0.0:
                        shared_state.joystick_x = 0.0
                        shared_state.joystick_y = 0.0
                        shared_state.is_dirty = False  # 処理不要フラグ
                    
                    # 動きがない場合は低頻度でポーリング（5Hz）- さらに負荷削減
                    time.sleep(0.2)  # 200ms間隔でポーリング
                
                # スリープはif-else文に移動したため、ここでは行わない

            except Exception as e:
                if "video system not initialized" in str(e):
                    # Pygame初期化エラーの場合は再初期化を試みる
                    futil.log("Pygame video system not initialized, attempting to reinitialize...", adsk.core.LogLevels.WarningLogLevel)
                    try:
                        self.joystick_manager.quit_pygame()
                        time.sleep(0.5)  # 少し待ってから再初期化
                        self.joystick_manager.initialize_pygame()
                        self.joystick_manager.get_joysticks()  # ジョイスティックを再取得
                    except Exception as reinit_error:
                        futil.log(f"Failed to reinitialize pygame: {reinit_error}", adsk.core.LogLevels.ErrorLogLevel)
                        time.sleep(1.0)  # エラー後は少し長めに待つ
                else:
                    futil.log(f"Error in JoystickThread: {e}", adsk.core.LogLevels.ErrorLogLevel)
                    futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
                    time.sleep(0.5)  # エラー後は少し待つ

        futil.log("JoystickThread stopped.")

    def stop(self) -> None:
        self.stop_event.set()
