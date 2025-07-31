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
                
                # デッドゾーン適用
                if abs(joystick_x) < self.dead_zone:
                    joystick_x = 0.0
                if abs(joystick_y) < self.dead_zone:
                    joystick_y = 0.0
                    
                # 反応曲線を適用（シンプル化）
                if joystick_x != 0.0:
                    sign_x = 1 if joystick_x > 0 else -1
                    joystick_x = sign_x * (abs(joystick_x) ** response_curve)
                    
                if joystick_y != 0.0:
                    sign_y = 1 if joystick_y > 0 else -1
                    joystick_y = sign_y * (abs(joystick_y) ** response_curve)

                # ボタン処理（すべての状態を保存）
                if config.BUTTON_ENABLED:
                    button_states = self.joystick_manager.get_all_button_states()
                    # すべてのボタンの状態を保存（押された/離されたの両方を検出するため）
                    shared_state.button_states = {i: pressed for i, pressed in enumerate(button_states)}
                else:
                    shared_state.button_states = {}

                # 十字キー処理（すべての状態を保存）
                if getattr(config, 'DPAD_ENABLED', True):
                    dpad_states = self.joystick_manager.get_dpad_button_states()
                    # すべての十字キーの状態を保存（押された/離されたの両方を検出するため）
                    shared_state.dpad_states = {direction: pressed for direction, pressed in dpad_states.items()}
                else:
                    shared_state.dpad_states = {}

                # 簡単なスムージング（軽量化）
                if hasattr(self, 'prev_x') and hasattr(self, 'prev_y'):
                    # 急激な変化のみチェック
                    if abs(joystick_x - self.prev_x) > 0.8 or abs(joystick_y - self.prev_y) > 0.8:
                        joystick_x = self.prev_x * 0.5 + joystick_x * 0.5
                        joystick_y = self.prev_y * 0.5 + joystick_y * 0.5
                
                # 現在値を保存
                self.prev_x = joystick_x
                self.prev_y = joystick_y

                # SharedStateの更新（軽量化）
                input_activity = abs(joystick_x) > 0.005 or abs(joystick_y) > 0.005
                button_activity = any(shared_state.button_states.values()) if hasattr(shared_state, 'button_states') else False
                dpad_activity = any(shared_state.dpad_states.values()) if hasattr(shared_state, 'dpad_states') else False
                
                if input_activity:  # ジョイスティック入力がある場合
                    shared_state.joystick_x = joystick_x
                    shared_state.joystick_y = joystick_y
                    shared_state.is_dirty = True
                    
                    # 動きがある場合は高頻度でポーリング（30Hz）- 負荷軽減
                    time.sleep(0.033)  # 33ms間隔
                elif button_activity or dpad_activity:  # ボタンまたは十字キーが押されている場合
                    # ボタン処理のためにより高頻度でポーリング
                    time.sleep(0.05)  # 50ms間隔 - ボタンレスポンス向上
                else:
                    # 動きがない場合：無駄な更新を避ける
                    if shared_state.is_dirty:
                        shared_state.joystick_x = 0.0
                        shared_state.joystick_y = 0.0
                        shared_state.is_dirty = False
                    
                    # 動きがない場合は低頻度でポーリング（10Hz）- ボタンレスポンス向上のため間隔短縮
                    time.sleep(0.1)  # 100ms間隔 - ボタン押下の検出速度向上
                
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
