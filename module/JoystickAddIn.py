import adsk.core
import traceback
from typing import Optional
from ..lib import fusionAddInUtils as futil
from .JoystickManager import JoystickManager
from .JoystickThread import JoystickThread

app = adsk.core.Application.get()
ui = app.userInterface

class JoystickAddIn:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JoystickAddIn, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            futil.log('Initializing JoystickAddIn')
            self.joystick_manager = JoystickManager()
            self.joystick_thread: Optional[JoystickThread] = None
            self.handlers = []
            self.initialized = True

    def run(self, context):
        try:
            futil.log("Joystick Add-In started")
            self.joystick_manager.initialize_pygame()
            joysticks = self.joystick_manager.get_joysticks()

            if not joysticks:
                futil.log('No joysticks found.')
                
                # 設定からウェルカムメッセージの表示有無を確認
                from .. import config
                if config.SHOW_WELCOME_MESSAGE:
                    ui.messageBox('ジョイスティックが見つかりませんでした。ジョイスティックを接続して、アドインを再起動してください。', 'JoystickCamera')
                    
                adsk.autoTerminate(False)
                return

            futil.log(f'{len(joysticks)} joysticks found.')
            self.start_joystick_thread()

            adsk.autoTerminate(False)

        except Exception as e:
            futil.log(f"Error in run function: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
            futil.log(f"Traceback: {traceback.format_exc()}", adsk.core.LogLevels.ErrorLogLevel)
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    def stop(self, context):
        try:
            futil.log("Joystick Add-In stopped")
            self.stop_joystick_thread()
            self.joystick_manager.quit_pygame()
            futil.clear_handlers()

        except Exception as e:
            futil.log(f'Error in stop function: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(f'Traceback: {traceback.format_exc()}', adsk.core.LogLevels.ErrorLogLevel)
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

    def start_joystick_thread(self):
        try:
            if self.joystick_thread and self.joystick_thread.is_alive():
                futil.log('Joystick thread is already running.')
                return

            futil.log('Starting joystick thread...')
            self.joystick_thread = JoystickThread(self.joystick_manager)
            self.joystick_thread.start()
            futil.log('Joystick thread started successfully.')

        except Exception as e:
            futil.log(f'Failed to start joystick thread: {e}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(f'Traceback: {traceback.format_exc()}', adsk.core.LogLevels.ErrorLogLevel)

    def stop_joystick_thread(self):
        try:
            if self.joystick_thread and self.joystick_thread.is_alive():
                futil.log('Stopping joystick thread...')
                self.joystick_thread.stop()
                self.joystick_thread.join(timeout=5)
                if self.joystick_thread.is_alive():
                    futil.log("Failed to stop joystick thread in time.", adsk.core.LogLevels.WarningLogLevel)
                else:
                    futil.log("Joystick thread stopped successfully.")
            self.joystick_thread = None
        except Exception as e:
            futil.log(f'Error stopping joystick thread: {e}', adsk.core.LogLevels.ErrorLogLevel)
            futil.log(f'Traceback: {traceback.format_exc()}', adsk.core.LogLevels.ErrorLogLevel)
