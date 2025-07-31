import adsk.core
import traceback
from typing import List, Optional
from ..lib import fusionAddInUtils as futil

# Attempt to import pygame
try:
    import pygame
except ImportError:
    futil.log("Pygame library not found. Please install it to use this add-in.", adsk.core.LogLevels.ErrorLogLevel)
    pygame = None

class JoystickManager:
    _instance = None
    
    # シングルトンパターンの実装
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JoystickManager, cls).__new__(cls)
            cls._instance.joystick = None
            cls._instance.is_initialized = False
        return cls._instance
    
    def __init__(self):
        # __new__メソッドでインスタンス変数は初期化済み
        pass

    def initialize_pygame(self) -> None:
        # すでに初期化されている場合は何もしない
        if self.is_initialized:
            futil.log("Pygame is already initialized.")
            return
            
        if not pygame:
            futil.log("Pygame library not found. Please install it to use this add-in.", adsk.core.LogLevels.ErrorLogLevel)
            return
            
        try:
            # 完全にクリーンな状態から始める
            if hasattr(pygame, 'quit'):
                pygame.quit()
                
            pygame.init()
            pygame.joystick.init()
            self.is_initialized = True
            futil.log("Pygame and joystick module initialized.")
        except Exception as e:
            futil.log(f"Failed to initialize pygame: {e}", adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
            self.is_initialized = False

    def get_joysticks(self) -> List:
        if not pygame:
            futil.log("Pygame is not available, cannot get joysticks.", adsk.core.LogLevels.ErrorLogLevel)
            return []
            
        try:
            # ジョイスティック一覧を取得
            joystick_count = pygame.joystick.get_count()
            futil.log(f"Found {joystick_count} joysticks")
            
            if joystick_count == 0:
                return []
            
            joysticks = []
            for i in range(joystick_count):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                joysticks.append(joy)
                futil.log(f"Joystick {i}: {joy.get_name()}, Axes: {joy.get_numaxes()}")
            
            # 設定から選択されたジョイスティックのインデックスを取得
            from .. import config
            selected_index = getattr(config, 'SELECTED_JOYSTICK', 0)
            futil.log(f"Using joystick at index {selected_index} from config")
            
            # インデックスが範囲外の場合は最初のジョイスティックを使用
            if selected_index >= len(joysticks):
                futil.log(f"Selected joystick index {selected_index} is out of range, using first joystick instead")
                selected_index = 0
            
            # 選択されたジョイスティックを使用
            if joysticks:
                self.joystick = joysticks[selected_index]
                futil.log(f"Selected joystick: {self.joystick.get_name()}")
            
            return joysticks
        except Exception as e:
            futil.log(f"Error getting joysticks: {e}", adsk.core.LogLevels.ErrorLogLevel)
            futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
            return []
            
    def get_axis_names(self) -> List[str]:
        """現在のジョイスティックの軸一覧を取得する"""
        if not self.joystick:
            return []
            
        try:
            num_axes = self.joystick.get_numaxes()
            axis_names = []
            
            # 一般的な軸の名前を提供
            common_names = [
                "左スティック左右 (X)",  # 0
                "左スティック上下 (Y)",  # 1
                "右スティック左右 (X)",  # 2
                "右スティック上下 (Y)",  # 3
                "L2/RT (アナログ)",      # 4
                "R2/LT (アナログ)"       # 5
            ]
            
            for i in range(num_axes):
                if i < len(common_names):
                    name = f"軸{i}: {common_names[i]}"
                else:
                    name = f"軸{i}"
                axis_names.append(name)
                
            return axis_names
        except Exception as e:
            futil.log(f"軸情報の取得でエラーが発生: {e}", adsk.core.LogLevels.ErrorLogLevel)
            return []

    def get_axes(self) -> Optional[List[float]]:
        # ジョイスティックが初期化されていない場合
        if not self.joystick:
            # 設定を確認し、選択されたジョイスティックを再取得
            from .. import config
            self.initialize_pygame()
            joysticks = self.get_joysticks()
            if not joysticks:
                return None
            
        # Pygameが初期化されていない場合は再初期化を試みる
        if not self.is_initialized:
            self.initialize_pygame()
            # 初期化に失敗した場合
            if not self.is_initialized:
                return None
                
        try:
            # イベントを処理（これがないとジョイスティックの状態が更新されない）
            pygame.event.pump()
            
            # ジョイスティックが有効かチェック
            if not pygame.joystick.get_init() or not hasattr(self.joystick, 'get_numaxes'):
                futil.log("Joystick subsystem is not initialized or joystick is invalid, reinitializing...", adsk.core.LogLevels.WarningLogLevel)
                pygame.joystick.init()
                # ジョイスティック再取得
                joysticks = self.get_joysticks()
                if not joysticks:
                    return None
            
            # 軸の数を取得
            num_axes = self.joystick.get_numaxes()
            if num_axes < 2:
                futil.log("Joystick has less than 2 axes.", adsk.core.LogLevels.WarningLogLevel)
                return None
            
            # 設定から軸のインデックスを取得
            from .. import config
            axis_x_index = getattr(config, 'AXIS_X', 0)
            axis_y_index = getattr(config, 'AXIS_Y', 1)
            
            # 指定された軸のインデックスが範囲内かチェック
            if axis_x_index >= num_axes or axis_y_index >= num_axes:
                futil.log(f"選択された軸が範囲外です。X軸: {axis_x_index}, Y軸: {axis_y_index}, 有効範囲: 0-{num_axes-1}", 
                          adsk.core.LogLevels.WarningLogLevel)
                # デフォルトの軸を使用
                axis_x_index = 0
                axis_y_index = 1
            
            # 設定された軸を使用
            axis_x = self.joystick.get_axis(axis_x_index)
            axis_y = self.joystick.get_axis(axis_y_index)
            return [axis_x, axis_y]
        except Exception as e:
            # エラーが発生した場合は再初期化を試みる
            if "video system not initialized" in str(e):
                futil.log("Video system not initialized, trying to reinitialize pygame...", adsk.core.LogLevels.WarningLogLevel)
                self.is_initialized = False
                self.initialize_pygame()
                # 再初期化後も問題があれば静かに失敗する
                return [0.0, 0.0]  # エラー時はニュートラル位置を返す
            else:
                futil.log(f"Error getting joystick axes: {e}", adsk.core.LogLevels.ErrorLogLevel)
                return None

    def get_hat_values(self) -> Optional[List[tuple]]:
        """ジョイスティックの十字キー（ハット）の状態を取得する
        
        Returns:
            List[tuple]: 各ハットの(x, y)値のリスト。x, yは-1, 0, 1の値
        """
        if not self.joystick or not self.is_initialized:
            return None
            
        try:
            # イベントを処理
            pygame.event.pump()
            
            # ハットの数を取得
            num_hats = self.joystick.get_numhats()
            if num_hats == 0:
                return None
                
            # 各ハットの値を取得
            hat_values = []
            for i in range(num_hats):
                hat_value = self.joystick.get_hat(i)
                hat_values.append(hat_value)
                
            return hat_values
        except Exception as e:
            futil.log(f"Error getting hat values: {e}", adsk.core.LogLevels.ErrorLogLevel)
            return None

    def get_hat_as_axis(self, hat_index=0) -> Optional[List[float]]:
        """十字キーをアナログスティック風の値として取得する
        
        Args:
            hat_index (int): 使用するハットのインデックス（通常は0）
            
        Returns:
            List[float]: [x, y]の値（-1.0から1.0の範囲）
        """
        hat_values = self.get_hat_values()
        if not hat_values or hat_index >= len(hat_values):
            return [0.0, 0.0]
            
        hat_x, hat_y = hat_values[hat_index]
        # 十字キーの値(-1, 0, 1)をそのまま浮動小数点として返す
        # Y軸は反転（十字キーの上が-1だが、カメラ制御では上が正の値になるべき）
        return [float(hat_x), -float(hat_y)]

    def get_dpad_button_states(self) -> dict:
        """十字キーの各方向をボタンとして扱い、その状態を取得する
        
        Returns:
            dict: {"dpad_up": bool, "dpad_down": bool, "dpad_left": bool, "dpad_right": bool}
        """
        states = {"dpad_up": False, "dpad_down": False, "dpad_left": False, "dpad_right": False}
        
        hat_values = self.get_hat_values()
        if not hat_values:
            return states
            
        # 最初のハットを使用
        hat_x, hat_y = hat_values[0]
        
        # 十字キーの状態をボタンとして解釈
        if hat_x == -1:  # 左
            states["dpad_left"] = True
        elif hat_x == 1:  # 右
            states["dpad_right"] = True
            
        if hat_y == -1:  # 下（pygameでは十字キーの下が-1）
            states["dpad_down"] = True
        elif hat_y == 1:  # 上（pygameでは十字キーの上が1）
            states["dpad_up"] = True
            
        return states

    def get_button_state(self, button_index=0):
        """ジョイスティックの特定のボタンの状態を取得する
        
        Args:
            button_index (int): 確認するボタンのインデックス（デフォルトは0、通常は中央ボタン）
            
        Returns:
            bool: ボタンが押されていればTrue、そうでなければFalse
        """
        # ジョイスティックが初期化されていない場合
        if not self.joystick or not self.is_initialized:
            return False
        
        try:
            # イベントを処理（これがないとボタンの状態が更新されない）
            pygame.event.pump()
            
            # ボタン数を確認
            num_buttons = self.joystick.get_numbuttons()
            if button_index >= num_buttons:
                futil.log(f"ボタンインデックス {button_index} は範囲外です（最大: {num_buttons-1}）", 
                         adsk.core.LogLevels.WarningLogLevel)
                return False
            
            # ボタンの状態を取得（押されていれば1、そうでなければ0）
            is_pressed = self.joystick.get_button(button_index)
            return bool(is_pressed)
        except Exception as e:
            futil.log(f"ボタン状態の取得でエラーが発生しました: {e}", adsk.core.LogLevels.ErrorLogLevel)
            return False
            
    def get_all_button_states(self):
        """ジョイスティックの全ボタンの状態を取得する
        
        Returns:
            list: 各ボタンの状態（True/False）のリスト
        """
        # ジョイスティックが初期化されていない場合
        if not self.joystick or not self.is_initialized:
            return []
        
        try:
            # イベントを処理（これがないとボタンの状態が更新されない）
            pygame.event.pump()
            
            # ボタン数を取得
            num_buttons = self.joystick.get_numbuttons()
            button_states = []
            
            # 全ボタンの状態を取得
            for i in range(num_buttons):
                is_pressed = bool(self.joystick.get_button(i))
                button_states.append(is_pressed)
                
            return button_states
        except Exception as e:
            futil.log(f"ボタン状態の取得でエラーが発生しました: {e}", adsk.core.LogLevels.ErrorLogLevel)
            return []
    
    def get_button_count(self):
        """ジョイスティックのボタン数を取得する
        
        Returns:
            int: ボタン数、取得できない場合は0
        """
        if not self.joystick or not self.is_initialized:
            return 0
            
        try:
            num_buttons = self.joystick.get_numbuttons()
            return num_buttons
        except Exception as e:
            futil.log(f"ボタン数の取得でエラーが発生しました: {e}", adsk.core.LogLevels.ErrorLogLevel)
            return 0
            
    def quit_pygame(self) -> None:
        if pygame:
            try:
                # ジョイスティックを解放
                if self.joystick:
                    # Pygameのバージョンによってはquitメソッドがない場合もある
                    if hasattr(self.joystick, 'quit'):
                        self.joystick.quit()
                    self.joystick = None
                
                # Pygameのサブシステムを順番に終了
                if hasattr(pygame.joystick, 'quit'):
                    pygame.joystick.quit()
                
                # Pygameを完全に終了
                pygame.quit()
                
                self.is_initialized = False
                futil.log("Pygame quit successfully.")
            except Exception as e:
                futil.log(f"Error quitting pygame: {e}", adsk.core.LogLevels.ErrorLogLevel)
                futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
