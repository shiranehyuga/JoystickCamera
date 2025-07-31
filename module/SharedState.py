# A simple class to hold the shared state between threads
class SharedState:
    def __init__(self):
        self.joystick_x = 0.0
        self.joystick_y = 0.0
        self.is_dirty = False # Flag to indicate new data is available
        self.button_states = {}  # ボタンの状態を保存する辞書 {button_index: is_pressed}
        self.dpad_states = {}    # 十字キーの状態を保存する辞書 {direction: is_pressed}

# Global instance
shared_state = SharedState()
