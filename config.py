# Application Global Variables
# This module serves as a way to share variables across different
# modules (global variables).

import os
import json
import adsk.core
from .lib import fusionAddInUtils as futil

# Flag that indicates to run in Debug mode or not. When running in Debug mode
# more information is written to the Text Command window. Generally, it's useful
# to set this to True while developing an add-in and set it to False when you
# are ready to distribute it.
DEBUG = True

# Log level
# Use InfoLogLevel for general messages, or DebugLogLevel for detailed debugging.
LOG_LEVEL = adsk.core.LogLevels.InfoLogLevel if DEBUG else adsk.core.LogLevels.WarningLogLevel

# Gets the name of the add-in from the name of the folder the py file is in.
# This is used when defining unique internal names for various UI elements 
# that need a unique name. It's also recommended to use a company name as 
# part of the ID to better ensure the ID is unique.
ADDIN_NAME = os.path.basename(os.path.dirname(__file__))
COMPANY_NAME = 'ACME'

# Joystick settings
ROTATION_SCALE = 0.008  # 回転感度（低めの値で設定）
DEAD_ZONE = 0.15        # デッドゾーン（少し大きめに設定して小さな入力を無視）
UPDATE_RATE = 0.032     # カメラ更新間隔（秒）、~30 FPS（遅めに設定して安定性を高める）
SELECTED_JOYSTICK = 0   # 選択されたジョイスティック（コントローラー）のインデックス
AXIS_X = 0              # X軸として使用するジョイスティック軸のインデックス
AXIS_Y = 1              # Y軸として使用するジョイスティック軸のインデックス
RESPONSE_CURVE = 1.0    # ジョイスティック反応曲線（1.0は線形、2.0は二乗カーブ、0.5は平方根カーブ）
USE_Z_AXIS_ROTATION = False  # Z軸回転モードを使用するかどうか（新しい操作パターン）
SHOW_WELCOME_MESSAGE = False  # 起動時のウェルカムメッセージを表示するかどうか
AUTO_RESET_ENABLED = False    # 定期的な自動リセットを有効にするかどうか
AUTO_RESET_INTERVAL = 60      # 自動リセットの間隔（分）

# ボタン機能の割り当て設定
BUTTON_ASSIGNMENTS = {
    0: "viewcube_front",     # ボタン0にビューキューブ前面機能を割り当て
    1: "viewcube_back",      # ボタン1にビューキューブ背面機能を割り当て
    2: "viewcube_left",      # ボタン2にビューキューブ左面機能を割り当て
    3: "viewcube_right",     # ボタン3にビューキューブ右面機能を割り当て
    4: "nearest_viewcube",   # ボタン4に最寄りのビューキューブ面機能を割り当て
    # 追加のボタン設定はここに追加
}
BUTTON_ENABLED = True    # ボタン機能を有効にするかどうか

# 十字キー（D-pad）の機能割り当て設定
DPAD_ASSIGNMENTS = {
    # "dpad_up": "viewcube_top",     # 十字キー上
    # "dpad_down": "viewcube_bottom", # 十字キー下
    # "dpad_left": "viewcube_left",   # 十字キー左
    # "dpad_right": "viewcube_right", # 十字キー右
}
DPAD_ENABLED = True      # 十字キー機能を有効にするかどうか

# 古い設定との互換性のために保持（内部的には使用されない）
HOME_VIEW_BUTTON = 0     # 旧形式の設定との互換性用

# 利用可能な機能リスト（ボタンに割り当て可能な機能）
AVAILABLE_FUNCTIONS = [
    ("機能なし", "none"),
    ("ホームビュー", "home_view"),  
    ("フィットビュー", "fit_view"),
    ("最寄りのビューキューブ面", "nearest_viewcube"),
    ("ビューキューブ前面", "viewcube_front"),
    ("ビューキューブ背面", "viewcube_back"),
    ("ビューキューブ左面", "viewcube_left"),
    ("ビューキューブ右面", "viewcube_right"),
    ("ビューキューブ上面", "viewcube_top"),
    ("ビューキューブ下面", "viewcube_bottom"),
    ("アイソメトリックビュー", "iso_view"),
    ("画面右回転90度", "rotate_screen_right"),
    ("画面左回転90度", "rotate_screen_left"),
    ("スマート右回転90度", "smart_rotate_right"),
    ("スマート左回転90度", "smart_rotate_left"),
    ("画面上回転90度", "rotate_screen_up"),
    ("画面下回転90度", "rotate_screen_down"),
    ("スマート上回転90度", "smart_rotate_up"),
    ("スマート下回転90度", "smart_rotate_down"),
    ("画面垂直時計回り90度", "rotate_screen_clockwise"),
    ("画面垂直反時計回り90度", "rotate_screen_counter_clockwise"),
    ("スマート垂直時計回り90度", "smart_rotate_clockwise"),
    ("スマート垂直反時計回り90度", "smart_rotate_counter_clockwise"),
]

# 設定ファイルのパス
SETTINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'joystick_settings.json')

# 設定を保存する関数
def save_settings():
    try:
        # 数値型で直接保存する
        settings = {
            'DEBUG': DEBUG,
            'ROTATION_SCALE': float(ROTATION_SCALE),  # 明示的に数値型で保存
            'DEAD_ZONE': float(DEAD_ZONE),  # 明示的に数値型で保存
            'UPDATE_RATE': float(UPDATE_RATE),  # 明示的に数値型で保存
            'SELECTED_JOYSTICK': int(SELECTED_JOYSTICK),  # 確実に整数として保存
            'AXIS_X': int(AXIS_X),  # X軸のインデックス
            'AXIS_Y': int(AXIS_Y),  # Y軸のインデックス
            'RESPONSE_CURVE': float(RESPONSE_CURVE),  # 反応曲線設定も数値型で保存
            'USE_Z_AXIS_ROTATION': bool(USE_Z_AXIS_ROTATION),  # Z軸回転モードの設定
            'SHOW_WELCOME_MESSAGE': bool(SHOW_WELCOME_MESSAGE),  # ウェルカムメッセージの表示設定
            'AUTO_RESET_ENABLED': bool(AUTO_RESET_ENABLED),  # 自動リセットの有効/無効
            'AUTO_RESET_INTERVAL': int(AUTO_RESET_INTERVAL),  # 自動リセットの間隔（分）
            'BUTTON_ASSIGNMENTS': dict(BUTTON_ASSIGNMENTS),  # ボタン機能の割り当て設定
            'BUTTON_ENABLED': bool(BUTTON_ENABLED),  # ボタン機能の有効/無効
            'DPAD_ASSIGNMENTS': dict(DPAD_ASSIGNMENTS),  # 十字キー機能の割り当て設定
            'DPAD_ENABLED': bool(DPAD_ENABLED)  # 十字キー機能の有効/無効
        }
        
        # 設定ファイルのディレクトリが存在するか確認し、存在しなければ作成
        settings_dir = os.path.dirname(SETTINGS_FILE_PATH)
        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)
            
        with open(SETTINGS_FILE_PATH, 'w') as f:
            json.dump(settings, f, indent=2)  # インデントを付けて読みやすく
        
        if 'futil' in globals():
            futil.log(f'設定を保存しました: {SETTINGS_FILE_PATH}')
        return True
    except Exception as e:
        if 'futil' in globals():
            futil.log(f'設定の保存に失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
        return False

# 設定を読み込む関数
def load_settings():
    global DEBUG, LOG_LEVEL, ROTATION_SCALE, DEAD_ZONE, UPDATE_RATE, SELECTED_JOYSTICK, AXIS_X, AXIS_Y, RESPONSE_CURVE, USE_Z_AXIS_ROTATION, SHOW_WELCOME_MESSAGE, AUTO_RESET_ENABLED, AUTO_RESET_INTERVAL, BUTTON_ASSIGNMENTS, BUTTON_ENABLED, DPAD_ASSIGNMENTS, DPAD_ENABLED
    
    try:
        if os.path.exists(SETTINGS_FILE_PATH):
            if 'futil' in globals():
                futil.log(f'設定ファイルを読み込み中: {SETTINGS_FILE_PATH}')
            with open(SETTINGS_FILE_PATH, 'r') as f:
                settings = json.load(f)
            
            # 設定を読み込む（型変換を適用して確実に正しい型で読み込む）
            DEBUG = bool(settings.get('DEBUG', DEBUG))
            
            # 浮動小数点数の設定（文字列または数値として保存された値を読み込む）
            try:
                value = settings.get('ROTATION_SCALE', None)
                if value is not None:
                    # 文字列または数値のどちらでも処理できるよう対応
                    try:
                        ROTATION_SCALE = float(value)
                    except (ValueError, TypeError):
                        if 'futil' in globals():
                            futil.log(f'回転感度の値が無効です: {value}。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
                if 'futil' in globals():
                    futil.log(f'回転感度を読み込みました: {ROTATION_SCALE}')
            except Exception as e:
                if 'futil' in globals():
                    futil.log(f'回転感度の読み込みに失敗しました: {str(e)}', adsk.core.LogLevels.WarningLogLevel)
            
            try:
                value = settings.get('DEAD_ZONE', None)
                if value is not None:
                    try:
                        DEAD_ZONE = float(value)
                    except (ValueError, TypeError):
                        if 'futil' in globals():
                            futil.log(f'デッドゾーンの値が無効です: {value}。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
                if 'futil' in globals():
                    futil.log(f'デッドゾーンを読み込みました: {DEAD_ZONE}')
            except Exception as e:
                if 'futil' in globals():
                    futil.log(f'デッドゾーンの読み込みに失敗しました: {str(e)}', adsk.core.LogLevels.WarningLogLevel)
            
            try:
                value = settings.get('UPDATE_RATE', None)
                if value is not None:
                    try:
                        UPDATE_RATE = float(value)
                    except (ValueError, TypeError):
                        if 'futil' in globals():
                            futil.log(f'更新間隔の値が無効です: {value}。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
                if 'futil' in globals():
                    futil.log(f'更新間隔を読み込みました: {UPDATE_RATE}秒 ({int(1/UPDATE_RATE)} FPS)')
            except Exception as e:
                if 'futil' in globals():
                    futil.log('更新間隔の値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
            
            try:
                SELECTED_JOYSTICK = int(settings.get('SELECTED_JOYSTICK', SELECTED_JOYSTICK))
                if 'futil' in globals():
                    futil.log(f'選択ジョイスティックを読み込みました: {SELECTED_JOYSTICK}')
            except (ValueError, TypeError):
                if 'futil' in globals():
                    futil.log('選択ジョイスティックの値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
                    
            # 軸の設定を読み込む
            try:
                AXIS_X = int(settings.get('AXIS_X', AXIS_X))
                AXIS_Y = int(settings.get('AXIS_Y', AXIS_Y))
                if 'futil' in globals():
                    futil.log(f'軸設定を読み込みました: X軸={AXIS_X}, Y軸={AXIS_Y}')
            except (ValueError, TypeError):
                if 'futil' in globals():
                    futil.log('軸設定の値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
                    
            # 反応曲線の設定を読み込む
            try:
                value = settings.get('RESPONSE_CURVE', None)
                if value is not None:
                    try:
                        RESPONSE_CURVE = float(value)
                    except (ValueError, TypeError):
                        if 'futil' in globals():
                            futil.log(f'反応曲線の値が無効です: {value}。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
                if 'futil' in globals():
                    futil.log(f'反応曲線を読み込みました: {RESPONSE_CURVE}')
            except Exception as e:
                if 'futil' in globals():
                    futil.log(f'反応曲線の読み込みに失敗しました: {str(e)}', adsk.core.LogLevels.WarningLogLevel)
            
            # Z軸回転モードの設定を読み込む
            try:
                USE_Z_AXIS_ROTATION = bool(settings.get('USE_Z_AXIS_ROTATION', USE_Z_AXIS_ROTATION))
                if 'futil' in globals():
                    futil.log(f'Z軸回転モード設定を読み込みました: {USE_Z_AXIS_ROTATION}')
            except (ValueError, TypeError):
                if 'futil' in globals():
                    futil.log('Z軸回転モードの値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
            
            # ウェルカムメッセージの表示設定を読み込む
            try:
                SHOW_WELCOME_MESSAGE = bool(settings.get('SHOW_WELCOME_MESSAGE', SHOW_WELCOME_MESSAGE))
                if 'futil' in globals():
                    futil.log(f'ウェルカムメッセージ設定を読み込みました: {SHOW_WELCOME_MESSAGE}')
            except (ValueError, TypeError):
                if 'futil' in globals():
                    futil.log('ウェルカムメッセージ設定の値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
            
            # 自動リセット設定を読み込む
            try:
                AUTO_RESET_ENABLED = bool(settings.get('AUTO_RESET_ENABLED', AUTO_RESET_ENABLED))
                AUTO_RESET_INTERVAL = int(settings.get('AUTO_RESET_INTERVAL', AUTO_RESET_INTERVAL))
                if 'futil' in globals():
                    futil.log(f'自動リセット設定を読み込みました: 有効={AUTO_RESET_ENABLED}, 間隔={AUTO_RESET_INTERVAL}分')
            except (ValueError, TypeError):
                if 'futil' in globals():
                    futil.log('自動リセット設定の値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
            
            # ボタン設定を読み込む
            try:
                # 新しいボタン設定方式の読み込み
                button_assignments_data = settings.get('BUTTON_ASSIGNMENTS', None)
                if button_assignments_data is not None:
                    # 辞書の各キーを整数に変換し、値も正しい機能名に変換する
                    BUTTON_ASSIGNMENTS = {}
                    
                    # 日本語表示名から機能名への変換マップ
                    display_name_to_function = {display: func for display, func in AVAILABLE_FUNCTIONS}
                    
                    for k, v in button_assignments_data.items():
                        button_index = int(k)
                        # 値が既に正しい機能名の場合はそのまま使用
                        if v in [func for _, func in AVAILABLE_FUNCTIONS]:
                            BUTTON_ASSIGNMENTS[button_index] = v
                        # 値が日本語表示名の場合は機能名に変換
                        elif v in display_name_to_function:
                            BUTTON_ASSIGNMENTS[button_index] = display_name_to_function[v]
                            if 'futil' in globals():
                                futil.log(f'ボタン{button_index}の設定を変換: {v} -> {display_name_to_function[v]}')
                        else:
                            if 'futil' in globals():
                                futil.log(f'ボタン{button_index}の設定が無効です: {v}', adsk.core.LogLevels.WarningLogLevel)
                else:
                    # 古い設定がある場合は変換する
                    old_home_button = settings.get('HOME_VIEW_BUTTON', None)
                    if old_home_button is not None:
                        BUTTON_ASSIGNMENTS = {int(old_home_button): "home_view"}
                        if 'futil' in globals():
                            futil.log(f'古い設定を新しい形式に変換しました: ボタン{old_home_button}->ホームビュー')
                    
                BUTTON_ENABLED = bool(settings.get('BUTTON_ENABLED', BUTTON_ENABLED))
                if 'futil' in globals():
                    futil.log(f'ボタン設定を読み込みました: 割り当て={BUTTON_ASSIGNMENTS}, 有効={BUTTON_ENABLED}')
            except (ValueError, TypeError):
                if 'futil' in globals():
                    futil.log('ボタン設定の値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
            
            # 十字キー設定の読み込み
            try:
                dpad_assignments_data = settings.get('DPAD_ASSIGNMENTS', {})
                if isinstance(dpad_assignments_data, dict):
                    # 日本語表示名から機能名への変換辞書
                    display_name_to_function = {display_name: func_name for display_name, func_name in AVAILABLE_FUNCTIONS}
                    
                    DPAD_ASSIGNMENTS = {}
                    for direction, v in dpad_assignments_data.items():
                        # 値が既に正しい機能名の場合はそのまま使用
                        if v in [func for _, func in AVAILABLE_FUNCTIONS]:
                            DPAD_ASSIGNMENTS[direction] = v
                        # 値が日本語表示名の場合は機能名に変換
                        elif v in display_name_to_function:
                            DPAD_ASSIGNMENTS[direction] = display_name_to_function[v]
                            if 'futil' in globals():
                                futil.log(f'十字キー{direction}の設定を変換: {v} -> {display_name_to_function[v]}')
                        else:
                            if 'futil' in globals():
                                futil.log(f'十字キー{direction}の設定が無効です: {v}', adsk.core.LogLevels.WarningLogLevel)
                    
                DPAD_ENABLED = bool(settings.get('DPAD_ENABLED', DPAD_ENABLED))
                if 'futil' in globals():
                    futil.log(f'十字キー設定を読み込みました: 割り当て={DPAD_ASSIGNMENTS}, 有効={DPAD_ENABLED}')
            except (ValueError, TypeError):
                if 'futil' in globals():
                    futil.log('十字キー設定の値が無効です。デフォルト値を使用します。', adsk.core.LogLevels.WarningLogLevel)
            
            # ログレベルの更新
            LOG_LEVEL = adsk.core.LogLevels.InfoLogLevel if DEBUG else adsk.core.LogLevels.WarningLogLevel
            
            if 'futil' in globals():
                futil.log('設定を読み込みました')
            return True
    except Exception as e:
        if 'futil' in globals():
            futil.log(f'設定の読み込みに失敗しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
    
    return False

# Gets the name of the add-in from the name of the folder the py file is in.
# This is used when defining unique internal names for various UI elements 
# that need a unique name. It's also recommended to use a company name as 
# part of the ID to better ensure the ID is unique.
ADDIN_NAME = os.path.basename(os.path.dirname(__file__))
COMPANY_NAME = 'JoystickCamera'

# Palettes
sample_palette_id = f'{COMPANY_NAME}_{ADDIN_NAME}_palette_id'
