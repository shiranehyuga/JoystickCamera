# 設定をリセットして正しいフォーマットで保存するスクリプト

import os
import sys

# パスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# configモジュールをインポート
import config

def reset_config():
    """設定をデフォルト値に戻して保存"""
    
    # デフォルト値を設定
    config.DEBUG = True
    config.ROTATION_SCALE = 0.008
    config.DEAD_ZONE = 0.15
    config.UPDATE_RATE = 0.032
    config.SELECTED_JOYSTICK = 0
    config.AXIS_X = 0
    config.AXIS_Y = 1
    config.RESPONSE_CURVE = 1.0
    config.USE_Z_AXIS_ROTATION = False
    config.SHOW_WELCOME_MESSAGE = False
    config.AUTO_RESET_ENABLED = False
    config.AUTO_RESET_INTERVAL = 60
    config.BUTTON_ENABLED = True
    
    # 正しい機能名でボタン割り当てを設定
    config.BUTTON_ASSIGNMENTS = {
        0: "viewcube_front",   # ボタン0にビューキューブ前面機能を割り当て
        1: "viewcube_back",    # ボタン1にビューキューブ背面機能を割り当て
        2: "viewcube_left",    # ボタン2にビューキューブ左面機能を割り当て
        3: "viewcube_right",   # ボタン3にビューキューブ右面機能を割り当て
    }
    
    # 設定を保存
    if config.save_settings():
        print("設定をリセットして保存しました")
        return True
    else:
        print("設定の保存に失敗しました")
        return False

if __name__ == "__main__":
    reset_config()
