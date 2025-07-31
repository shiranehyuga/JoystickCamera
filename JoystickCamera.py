import adsk.core
import traceback
import time
import threading
from . import commands
from .lib import fusionAddInUtils as futil
from .module.JoystickAddIn import JoystickAddIn
from .module.CameraController import CameraController
from .module.SharedState import shared_state

app = adsk.core.Application.get()
ui = app.userInterface

# Event ID for the timer
TIMER_EVENT_ID = 'AutoRotateCameraTimerEvent'

# --- Event Handler: Runs in the main thread, updates camera --- #
class CameraUpdateHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()
        self.camera_controller = CameraController()
        self.last_update_time = time.time()
        
        # configから更新間隔を取得
        from . import config
        # 最低10ms間隔で更新（100fps）
        self.update_interval = min(getattr(config, 'UPDATE_RATE', 0.01), 0.01)
        
        # ボタンの前回の状態を追跡する辞書
        self.prev_button_states = {}
        # 十字キーの前回の状態を追跡する辞書
        self.prev_dpad_states = {}

    def notify(self, args: adsk.core.CustomEventArgs):
        try:
            # configから最新の設定を取得
            from . import config
            self.update_interval = getattr(config, 'UPDATE_RATE', 0.01)
            
            # デバッグ設定を更新
            futil.log_level = config.LOG_LEVEL
            
            # 前回の更新からの経過時間をチェック
            current_time = time.time()
            elapsed = current_time - self.last_update_time
            
            # 自動リセット機能の処理
            global last_reset_time
            if config.AUTO_RESET_ENABLED:
                # 分を秒に変換（例: 60分 = 3600秒）
                reset_interval_seconds = config.AUTO_RESET_INTERVAL * 60
                time_since_last_reset = current_time - last_reset_time
                
                # リセット間隔を超えたら自動リセットを実行
                if time_since_last_reset > reset_interval_seconds:
                    futil.log(f'自動リセットを実行します（間隔: {config.AUTO_RESET_INTERVAL}分）', adsk.core.LogLevels.InfoLogLevel)
                    
                    # ジョイスティック処理をリセット
                    from .module.JoystickAddIn import JoystickAddIn
                    joystick_addin = JoystickAddIn()
                    
                    # スレッドを一度停止してから再開始
                    joystick_addin.stop_joystick_thread()
                    
                    # Pygameを完全に再初期化
                    from .module.JoystickManager import JoystickManager
                    joystick_manager = JoystickManager()
                    joystick_manager.quit_pygame()
                    time.sleep(0.5)  # 少し待機して確実に終了させる
                    
                    joystick_manager.initialize_pygame()
                    joysticks = joystick_manager.get_joysticks()
                    
                    # スレッドを再開
                    joystick_addin.start_joystick_thread()
                    
                    # リセット時間を更新
                    last_reset_time = current_time
                    futil.log('自動リセットが完了しました', adsk.core.LogLevels.InfoLogLevel)
            
            # 一定間隔以上空いていない場合はスキップ
            if elapsed < self.update_interval:
                return
                
            # 新しいジョイスティックデータがあるか確認
            if shared_state.is_dirty:
                # 共有状態から値を取得
                joystick_x = shared_state.joystick_x
                joystick_y = shared_state.joystick_y
                
                # 最新の回転感度を設定に反映
                self.camera_controller.rotation_scale = getattr(config, 'ROTATION_SCALE', 0.008)
                
                # カメラ位置を更新
                self.camera_controller.update_camera_position(joystick_x, joystick_y)
                
                # データ処理完了をマーク
                shared_state.is_dirty = False
                
            # ボタン機能の処理
            if config.BUTTON_ENABLED and hasattr(config, 'BUTTON_ASSIGNMENTS'):
                # 現在のボタン状態を確認
                current_button_states = getattr(shared_state, 'button_states', {})
                
                for button_index, function_name in config.BUTTON_ASSIGNMENTS.items():
                    if function_name == "none":
                        continue
                        
                    # 現在の状態と前回の状態を比較
                    current_pressed = current_button_states.get(button_index, False)
                    prev_pressed = self.prev_button_states.get(button_index, False)
                    
                    # ボタンが押された瞬間（前回False、今回True）の場合のみ機能を実行
                    if current_pressed and not prev_pressed:
                        # デバッグ用：実際の function_name の値を表示
                        futil.log(f"ボタン {button_index} が押されました。機能コード '{function_name}' を実行します。", adsk.core.LogLevels.InfoLogLevel)
                        futil.log(f"DEBUG: BUTTON_ASSIGNMENTS = {config.BUTTON_ASSIGNMENTS}", adsk.core.LogLevels.InfoLogLevel)
                        self.camera_controller.execute_button_function(function_name)
                
                # 前回の状態を更新
                self.prev_button_states = current_button_states.copy()

                # 十字キー機能が有効な場合の処理
                if getattr(config, 'DPAD_ENABLED', True):
                    # 現在の十字キー状態を確認
                    current_dpad_states = getattr(shared_state, 'dpad_states', {})
                    
                    # DPAD_ASSIGNMENTSが存在しない場合は空の辞書として処理
                    dpad_assignments = getattr(config, 'DPAD_ASSIGNMENTS', {})
                    
                    for direction, function_name in dpad_assignments.items():
                        if function_name == "none":
                            continue
                            
                        # 現在の状態と前回の状態を比較
                        current_pressed = current_dpad_states.get(direction, False)
                        prev_pressed = self.prev_dpad_states.get(direction, False)
                        
                        # 十字キーが押された瞬間（前回False、今回True）の場合のみ機能を実行
                        if current_pressed and not prev_pressed:
                            futil.log(f"十字キー {direction} が押されました。機能コード '{function_name}' を実行します。", adsk.core.LogLevels.InfoLogLevel)
                            self.camera_controller.execute_button_function(function_name)
                    
                    # 前回の状態を更新
                    self.prev_dpad_states = current_dpad_states.copy()
            else:
                # データがない場合はビューポート更新を最小限にする
                # 必要な場合にのみ更新（10回に1回程度）
                current_time_ms = int(current_time * 1000)
                if current_time_ms % 10 == 0:  # 10回に1回程度の頻度で更新
                    app.activeViewport.refresh()
                
            # 更新時間を記録
            self.last_update_time = current_time

        except Exception as e:
            futil.log(f'Error in CameraUpdateHandler: {e}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)

# --- Timer Thread: Fires events at a regular interval --- #
class TimerThread(threading.Thread):
    def __init__(self, event: adsk.core.CustomEvent):
        super().__init__(daemon=True)
        self.stop_event = threading.Event()
        self.timer_event = event
        
        # Import here to avoid circular imports
        from . import config
        self.update_rate = getattr(config, 'UPDATE_RATE', 0.016)
        fps = int(1.0 / self.update_rate)
        futil.log(f'TimerThreadの更新頻度を設定: {fps} FPS ({self.update_rate:.4f}秒)')

    def run(self):
        futil.log('TimerThread started for camera updates.')
        while not self.stop_event.is_set():
            # イベント発火
            app.fireCustomEvent(TIMER_EVENT_ID, '')
            
            # 現在の設定を動的に反映
            from . import config
            current_rate = getattr(config, 'UPDATE_RATE', self.update_rate)
            if current_rate != self.update_rate:
                old_fps = int(1.0 / self.update_rate)
                new_fps = int(1.0 / current_rate)
                if config.DEBUG:
                    futil.log(f'更新頻度を変更: {old_fps} FPS -> {new_fps} FPS ({current_rate:.4f}秒)')
                self.update_rate = current_rate
                
            # ビューポート更新の頻度を下げて、全体的な負荷を軽減
            if app.activeViewport and int(time.time() * 1000) % 50 == 0:  # 約50回に1回の頻度で更新
                app.activeViewport.refresh()
                
            time.sleep(self.update_rate)
        futil.log('TimerThread stopped.')

    def stop(self):
        self.stop_event.set()

# --- Global variables for handlers and threads --- #
camera_update_handler: CameraUpdateHandler = None
timer_event: adsk.core.CustomEvent = None
timer_thread: TimerThread = None

# 自動リセット用の変数
last_reset_time = time.time()  # 最後にリセットした時間

def run(context):
    global camera_update_handler, timer_event, timer_thread
    try:
        futil.log('Starting JoystickCamera Add-in')
        
        # 保存された設定を読み込む
        from . import config
        if config.load_settings():
            futil.log('保存された設定を読み込みました:')
            futil.log(f'  DEBUG: {config.DEBUG}')
            futil.log(f'  ROTATION_SCALE: {config.ROTATION_SCALE}')
            futil.log(f'  DEAD_ZONE: {config.DEAD_ZONE}')
            futil.log(f'  UPDATE_RATE: {config.UPDATE_RATE}')
            futil.log(f'  SELECTED_JOYSTICK: {config.SELECTED_JOYSTICK}')
            futil.log(f'  USE_Z_AXIS_ROTATION: {config.USE_Z_AXIS_ROTATION}')
            futil.log(f'  BUTTON_ENABLED: {config.BUTTON_ENABLED}')
            futil.log(f'  BUTTON_ASSIGNMENTS: {config.BUTTON_ASSIGNMENTS}')
            # 各ボタン割り当ての詳細表示
            for btn_idx, func_name in config.BUTTON_ASSIGNMENTS.items():
                futil.log(f'    ボタン {btn_idx}: {func_name} (type: {type(func_name)})')
        else:
            futil.log('設定の読み込みに失敗したため、デフォルト値を使用します')
            # 初回起動時は設定を保存して次回以降使えるようにする
            futil.log(f'デフォルトBUTTON_ASSIGNMENTS: {config.BUTTON_ASSIGNMENTS}')
            config.save_settings()
            
        # LOG_LEVELを設定に合わせて更新
        futil.log_level = config.LOG_LEVEL
        futil.log('ログレベルを設定しました: ' + ('INFO' if config.DEBUG else 'WARNING'))
        
        # CameraControllerの回転感度を設定
        from .module.CameraController import CameraController
        CameraController.rotation_scale = config.ROTATION_SCALE
        futil.log(f'CameraController回転感度を設定: {CameraController.rotation_scale}')

        # Initialize joystick controller
        joystick_addin = JoystickAddIn()
        joystick_addin.run(context)

        # Create the handler for camera updates
        camera_update_handler = CameraUpdateHandler()

        # Register the custom event and connect the handler
        timer_event = app.registerCustomEvent(TIMER_EVENT_ID)
        timer_event.add(camera_update_handler)

        # Create and start the dedicated timer thread
        timer_thread = TimerThread(timer_event)
        timer_thread.start()

        commands.start()
        
        # 設定に基づいてウェルカムメッセージを表示
        if config.SHOW_WELCOME_MESSAGE:
            try:
                futil.log("起動メッセージを表示します")
                ui.messageBox('JoystickCameraアドインが起動しました。\n\n設定メニューの「ジョイスティック設定」ボタンをクリックすると設定画面が開きます。', 'JoystickCamera')
            except Exception as e:
                futil.log(f"メッセージボックス表示でエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
                futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
        else:
            futil.log("起動メッセージの表示はスキップされました")
        
        futil.log('JoystickCamera Add-in started successfully')

    except:
        futil.handle_error('run')

def stop(context):
    global camera_update_handler, timer_event, timer_thread
    try:
        futil.log('Stopping JoystickCamera Add-in')

        # Stop joystick controller
        joystick_addin = JoystickAddIn()
        joystick_addin.stop(context)

        # Stop all threads and handlers
        if timer_thread:
            timer_thread.stop()

        if timer_event and camera_update_handler:
            timer_event.remove(camera_update_handler)
            app.unregisterCustomEvent(TIMER_EVENT_ID)

        futil.clear_handlers()
        commands.stop()
        futil.log('JoystickCamera Add-in stopped successfully')

    except:
        futil.handle_error('stop')
