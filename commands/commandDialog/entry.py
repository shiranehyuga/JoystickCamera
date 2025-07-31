import adsk.core
import os
import traceback
from ...lib import fusionAddInUtils as futil
from ... import config
from ...module.JoystickManager import JoystickManager

app = adsk.core.Application.get()
ui = app.userInterface

# コマンド情報の定義
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_joystickSettings'
CMD_NAME = 'ジョイスティック設定'
CMD_Description = 'ジョイスティックカメラの設定を行います'

# コマンドをパネルに表示するかどうか
IS_PROMOTED = True

# コマンドボタンの配置場所
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# アイコンのフォルダパス
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# イベントハンドラーの参照を保持するリスト
local_handlers = []


# アドイン起動時に実行される関数
def start():
    try:
        # コマンド定義を作成
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

        # コマンド作成時のイベントハンドラを定義
        futil.add_handler(cmd_def.commandCreated, command_created)

        # UIにボタンを追加
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        if workspace:
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            if panel:
                control = panel.controls.itemById(CMD_ID)
                if not control:
                    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
                    control.isPromoted = IS_PROMOTED
                    futil.log(f"設定ボタンをUIに追加しました: {CMD_NAME}")
            else:
                futil.log(f"指定されたパネルが見つかりません: {PANEL_ID}")
        else:
            futil.log(f"指定されたワークスペースが見つかりません: {WORKSPACE_ID}")

        futil.log("commandDialog start completed successfully")
    except Exception as e:
        futil.log(f"commandDialog起動エラー: {str(e)}")
        import traceback
        futil.log(traceback.format_exc())


# アドイン停止時に実行される関数
def stop():
    try:
        # UIからコマンドを削除
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        if workspace:
            panel = workspace.toolbarPanels.itemById(PANEL_ID)
            if panel:
                command_control = panel.controls.itemById(CMD_ID)
                if command_control:
                    command_control.deleteMe()
        
        # コマンド定義を削除
        command_definition = ui.commandDefinitions.itemById(CMD_ID)
        if command_definition:
            command_definition.deleteMe()
        
        futil.log("commandDialog stop completed successfully")
    except Exception as e:
        futil.log(f"commandDialog停止エラー: {str(e)}")
        import traceback
        futil.log(traceback.format_exc())


# コマンドのUIを構築する関数
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # デバッグログ
    futil.log(f'{CMD_NAME} コマンドが作成されました')

    # コマンド入力の取得
    inputs = args.command.commandInputs

    # --- 設定項目の追加 ---
    
    # 1. ログ出力の設定
    debug_input = inputs.addBoolValueInput('debug_setting', 'デバッグログを表示', True, '', config.DEBUG)
    debug_input.tooltip = 'オンにするとデバッグログが出力されます'

    # 2. ジョイスティック（コントローラー）の選択
    joystick_dropdown = inputs.addDropDownCommandInput('joystick_selection', 'コントローラー', 
                                                     adsk.core.DropDownStyles.TextListDropDownStyle)
    joystick_dropdown.tooltip = '使用するゲームコントローラーを選択します'
    
    # 3. X軸とY軸の選択用ドロップダウン
    axis_x_dropdown = inputs.addDropDownCommandInput('axis_x_selection', 'X軸（左右）', 
                                                   adsk.core.DropDownStyles.TextListDropDownStyle)
    axis_x_dropdown.tooltip = 'カメラの左右回転に使用する軸を選択します'
    
    axis_y_dropdown = inputs.addDropDownCommandInput('axis_y_selection', 'Y軸（上下）', 
                                                   adsk.core.DropDownStyles.TextListDropDownStyle)
    axis_y_dropdown.tooltip = 'カメラの上下回転に使用する軸を選択します'
    
    # ジョイスティック一覧と軸情報を取得して表示
    try:
        # シングルトンなので、既存のインスタンスを取得
        joystick_manager = JoystickManager()
        
        # すでに初期化されている場合は再初期化しない
        if not joystick_manager.is_initialized:
            joystick_manager.initialize_pygame()
        
        joysticks = joystick_manager.get_joysticks()
        
        if joysticks:
            for i, joystick in enumerate(joysticks):
                # 既存の設定があれば、それを選択
                is_selected = (i == config.SELECTED_JOYSTICK) if i < len(joysticks) else (i == 0)
                joystick_dropdown.listItems.add(joystick.get_name(), is_selected)
            
            # 軸の選択肢を取得
            axis_names = joystick_manager.get_axis_names()
            
            # X軸の選択肢を設定
            for i, axis_name in enumerate(axis_names):
                is_selected = (i == config.AXIS_X)
                axis_x_dropdown.listItems.add(axis_name, is_selected)
            
            # Y軸の選択肢を設定
            for i, axis_name in enumerate(axis_names):
                is_selected = (i == config.AXIS_Y)
                axis_y_dropdown.listItems.add(axis_name, is_selected)
        else:
            joystick_dropdown.listItems.add('コントローラーが見つかりません', True)
            axis_x_dropdown.listItems.add('軸が見つかりません', True)
            axis_y_dropdown.listItems.add('軸が見つかりません', True)
    except Exception as e:
        futil.log(f"ジョイスティック情報の取得でエラーが発生しました: {str(e)}")
        futil.log(traceback.format_exc())
        joystick_dropdown.listItems.add('ジョイスティック情報の取得に失敗しました', True)

    # 区切り線の追加
    inputs.addTextBoxCommandInput('divider1', '', '<hr>', 1, True)
    
    # 3. カメラモード設定
    camera_mode_group = inputs.addGroupCommandInput('camera_mode_group', 'カメラモード')
    camera_mode_group.isExpanded = True
    camera_mode_group.isEnabledCheckBoxDisplayed = False
    camera_mode_inputs = camera_mode_group.children
    
    # Z軸回転モードの設定
    z_rotation_input = camera_mode_inputs.addBoolValueInput('z_rotation_mode', 'Z軸回転モードを有効にする', True, '', config.USE_Z_AXIS_ROTATION)
    z_rotation_input.tooltip = '有効にすると、ジョイスティックの動きによってカメラをZ軸周りに回転できます'
    
    # 区切り線の追加
    inputs.addTextBoxCommandInput('divider_camera', '', '<hr>', 1, True)
    
    # 4. ボタン設定用のグループ - UIの先頭に配置して確実に表示されるようにする
    button_group = inputs.addGroupCommandInput('button_group', 'ボタン設定')
    button_group.isExpanded = True
    button_group.isEnabledCheckBoxDisplayed = False
    button_inputs = button_group.children
    
    # 4-1. ボタン機能の有効/無効
    button_enabled = button_inputs.addBoolValueInput('button_enabled', 'ボタン機能を有効にする', True, '', config.BUTTON_ENABLED)
    button_enabled.tooltip = 'ジョイスティックボタンの機能を有効にするかどうかを設定します'
    
    # 4-2. ボタンごとの機能割り当て
    try:
        # シングルトンなので、既存のインスタンスを取得
        joystick_manager = JoystickManager()
        
        # すでに初期化されている場合は再初期化しない
        if not joystick_manager.is_initialized:
            joystick_manager.initialize_pygame()
            
        # ジョイスティック情報を取得
        joysticks = joystick_manager.get_joysticks()
        
        if joysticks and joystick_manager.joystick:
            # ボタン数を取得
            num_buttons = joystick_manager.joystick.get_numbuttons()
            
            # 各ボタンに対して機能割り当てドロップダウンを作成
            for i in range(min(num_buttons, 8)):  # 最大8個のボタンまで表示
                button_dropdown = button_inputs.addDropDownCommandInput(
                    f'button_{i}_function', 
                    f'ボタン {i}', 
                    adsk.core.DropDownStyles.TextListDropDownStyle
                )
                button_dropdown.tooltip = f'ボタン {i} に割り当てる機能を選択します'
                
                # 利用可能な機能を追加
                current_function = config.BUTTON_ASSIGNMENTS.get(i, "none")
                for display_name, function_name in config.AVAILABLE_FUNCTIONS:
                    is_selected = (function_name == current_function)
                    button_dropdown.listItems.add(display_name, is_selected)
        else:
            # コントローラーが見つからない場合の表示
            no_controller_text = button_inputs.addTextBoxCommandInput(
                'no_controller_message', 
                '', 
                'コントローラーが見つかりません。コントローラーを接続してから設定してください。', 
                2, 
                True
            )
            futil.log("コントローラーが見つからないか、初期化されていません", adsk.core.LogLevels.WarningLogLevel)
    except Exception as e:
        futil.log(f"ボタン情報の取得でエラーが発生しました: {str(e)}")
        futil.log(traceback.format_exc())
        # エラー時の表示
        error_text = button_inputs.addTextBoxCommandInput(
            'button_error_message', 
            '', 
            'ボタン設定の読み込みでエラーが発生しました。', 
            2, 
            True
        )
    
    # 区切り線の追加
    inputs.addTextBoxCommandInput('divider_button', '', '<hr>', 1, True)
    
    # 4. 感度設定用のグループ
    sensitivity_group = inputs.addGroupCommandInput('sensitivity_group', '感度設定')
    sensitivity_group.isExpanded = True
    sensitivity_group.isEnabledCheckBoxDisplayed = False
    sensitivity_inputs = sensitivity_group.children
    
    # 3-1. 回転感度の設定（スライダー）
    rotation_slider = sensitivity_inputs.addFloatSliderCommandInput('rotation_scale_slider', '回転感度', '', 0.001, 0.5)
    rotation_slider.valueOne = config.ROTATION_SCALE
    rotation_slider.tooltip = '値が大きいほど、ジョイスティックの動きに対するカメラの回転が大きくなります'
    
    # 3-2. デッドゾーンの設定
    deadzone_slider = sensitivity_inputs.addFloatSliderCommandInput('deadzone_slider', 'デッドゾーン', '', 0.01, 0.5)
    deadzone_slider.valueOne = config.DEAD_ZONE
    deadzone_slider.tooltip = '小さな入力を無視する範囲を設定します。手ぶれを防止するために使用します'
    
    # 3-3. 更新頻度の設定（FPSで表示）
    # 秒からFPSへの変換（例: 0.032秒 → 約31FPS）
    min_fps = 10  # 最小FPS
    max_fps = 100 # 最大FPS
    current_fps = int(1 / config.UPDATE_RATE)
    
    # 更新間隔は内部的には秒単位で保持するが、スライダーはFPSで表示
    fps_slider = sensitivity_inputs.addFloatSliderCommandInput('fps_slider', '更新頻度(FPS)', '', min_fps, max_fps)
    fps_slider.valueOne = float(current_fps)
    fps_slider.tooltip = 'カメラの更新頻度を設定します。値が大きいほど滑らかになりますが、負荷が高くなります'
    
    # 3-4. 反応曲線の設定
    response_curve_slider = sensitivity_inputs.addFloatSliderCommandInput('response_curve_slider', '反応曲線', '', 0.1, 3.0)
    response_curve_slider.valueOne = config.RESPONSE_CURVE
    response_curve_slider.tooltip = '1.0: 線形（デフォルト）、<1.0: 高感度（平方根曲線）、>1.0: 低感度（二乗曲線）'
    
    # カメラ操作モードは上部に移動しました（削除）

    # イベントハンドラの登録
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# OKボタンをクリックした時の処理
def command_execute(args: adsk.core.CommandEventArgs):
    # デバッグログ
    futil.log(f'{CMD_NAME} コマンド実行')

    # 入力値の取得
    inputs = args.command.commandInputs
    
    # デバッグ設定
    debug_input = inputs.itemById('debug_setting')
    config.DEBUG = debug_input.value
    config.LOG_LEVEL = adsk.core.LogLevels.InfoLogLevel if config.DEBUG else adsk.core.LogLevels.WarningLogLevel
    
    # ジョイスティック選択（今後拡張予定）
    joystick_dropdown = inputs.itemById('joystick_selection')
    selected_joystick = joystick_dropdown.selectedItem.name if joystick_dropdown.selectedItem else None
    futil.log(f'選択されたジョイスティック: {selected_joystick}')
    
    # 回転感度
    rotation_scale_slider = inputs.itemById('rotation_scale_slider')
    if rotation_scale_slider:
        old_value = config.ROTATION_SCALE
        config.ROTATION_SCALE = rotation_scale_slider.valueOne
        futil.log(f'回転感度を更新: {old_value} -> {config.ROTATION_SCALE}')
        
        # CameraControllerのstatic変数を直接更新
        from ...module.CameraController import CameraController
        CameraController.rotation_scale = config.ROTATION_SCALE
        futil.log(f'CameraControllerの回転感度を設定: {CameraController.rotation_scale}')
    
    # デッドゾーン
    deadzone_slider = inputs.itemById('deadzone_slider')
    if deadzone_slider:
        old_value = config.DEAD_ZONE
        config.DEAD_ZONE = deadzone_slider.valueOne
        futil.log(f'デッドゾーンを更新: {old_value} -> {config.DEAD_ZONE}')
    
    # 更新間隔（FPSから秒に変換）
    fps_slider = inputs.itemById('fps_slider')
    if fps_slider:
        old_fps = int(1.0 / config.UPDATE_RATE)
        new_fps = fps_slider.valueOne
        # FPSから秒に変換
        config.UPDATE_RATE = 1.0 / new_fps
        futil.log(f'更新頻度を更新: {old_fps} FPS -> {new_fps} FPS ({config.UPDATE_RATE:.4f}秒)')
        
    # 反応曲線
    response_curve_slider = inputs.itemById('response_curve_slider')
    if response_curve_slider:
        old_value = config.RESPONSE_CURVE
        config.RESPONSE_CURVE = response_curve_slider.valueOne
        futil.log(f'反応曲線を更新: {old_value} -> {config.RESPONSE_CURVE}')
    
    # 設定を保存
    try:
        # 選択されたジョイスティック（コントローラー）のインデックスを保存
        if joystick_dropdown.selectedItem and joystick_dropdown.selectedItem.name != 'コントローラーが見つかりません':
            config.SELECTED_JOYSTICK = joystick_dropdown.selectedItem.index
            
        # X軸とY軸の設定を保存
        axis_x_dropdown = inputs.itemById('axis_x_selection')
        if axis_x_dropdown and axis_x_dropdown.selectedItem:
            config.AXIS_X = axis_x_dropdown.selectedItem.index
            futil.log(f'X軸設定を更新: {config.AXIS_X}')
            
        axis_y_dropdown = inputs.itemById('axis_y_selection')
        if axis_y_dropdown and axis_y_dropdown.selectedItem:
            config.AXIS_Y = axis_y_dropdown.selectedItem.index
            futil.log(f'Y軸設定を更新: {config.AXIS_Y}')
            
        # ボタン設定を保存
        button_enabled_input = inputs.itemById('button_enabled')
        if button_enabled_input:
            config.BUTTON_ENABLED = button_enabled_input.value
            futil.log(f'ボタン機能設定を更新: {config.BUTTON_ENABLED}')
            
        # 各ボタンの機能割り当てを保存
        for i in range(8):  # 最大8個のボタンまで
            button_dropdown = inputs.itemById(f'button_{i}_function')
            if button_dropdown and button_dropdown.selectedItem:
                # 選択された機能の内部名を取得
                selected_display_name = button_dropdown.selectedItem.name
                selected_function = "none"  # デフォルト値
                
                # 表示名から内部名を取得
                for display_name, function_name in config.AVAILABLE_FUNCTIONS:
                    if display_name == selected_display_name:
                        selected_function = function_name
                        break
                
                # ボタン割り当てを更新
                if selected_function == "none":
                    # "機能なし"の場合は辞書から削除
                    if i in config.BUTTON_ASSIGNMENTS:
                        del config.BUTTON_ASSIGNMENTS[i]
                else:
                    config.BUTTON_ASSIGNMENTS[i] = selected_function
                
                futil.log(f'ボタン {i} の機能を更新: {selected_function}')
            
        # Z軸回転モードの設定を保存
        z_rotation_input = inputs.itemById('z_rotation_mode')
        if z_rotation_input:
            config.USE_Z_AXIS_ROTATION = z_rotation_input.value
            futil.log(f'Z軸回転モード設定を更新: {config.USE_Z_AXIS_ROTATION}')
            
        # CameraControllerに設定を直接反映
        from ...module.CameraController import CameraController
        CameraController.rotation_scale = config.ROTATION_SCALE
            
        # 設定をファイルに保存（メッセージボックスなし）
        if not config.save_settings():
            ui.messageBox('設定の保存に失敗しました。')
    except Exception as e:
        futil.log(f'エラー: {str(e)}')
        ui.messageBox(f'エラーが発生しました: {str(e)}')


# プレビュー更新時の処理
def command_preview(args: adsk.core.CommandEventArgs):
    # 本アプリでは特に何もしない
    pass


# 入力値が変更された時の処理
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs
    
    # 入力に応じたリアルタイム処理をここに記述
    if changed_input.id == 'rotation_scale_slider':
        rotation_scale = changed_input.valueOne
        futil.log(f'回転感度が変更されました: {rotation_scale}')
    
    elif changed_input.id == 'fps_slider':
        fps = changed_input.valueOne
        # FPSから秒への変換
        update_rate = 1.0 / fps
        futil.log(f'更新頻度が変更されました: {fps} FPS ({update_rate:.4f}秒)')
    
    # コントローラーが変更された場合、軸のリストを更新
    elif changed_input.id == 'joystick_selection':
        try:
            joystick_dropdown = changed_input
            selected_index = joystick_dropdown.selectedItem.index if joystick_dropdown.selectedItem else 0
            futil.log(f'コントローラーが変更されました: インデックス {selected_index}')
            
            # シングルトンなので、既存のインスタンスを取得
            joystick_manager = JoystickManager()
            
            # すでに初期化されている場合は再初期化しない
            if not joystick_manager.is_initialized:
                joystick_manager.initialize_pygame()
            
            # 選択されたコントローラーを設定
            joysticks = joystick_manager.get_joysticks()
            if joysticks and selected_index < len(joysticks):
                joystick_manager.joystick = joysticks[selected_index]
                
                # 軸の選択肢を更新
                axis_names = joystick_manager.get_axis_names()
                
                # X軸ドロップダウンを更新
                axis_x_dropdown = inputs.itemById('axis_x_selection')
                if axis_x_dropdown:
                    axis_x_dropdown.listItems.clear()
                    for i, axis_name in enumerate(axis_names):
                        is_selected = (i == config.AXIS_X)
                        axis_x_dropdown.listItems.add(axis_name, is_selected)
                
                # Y軸ドロップダウンを更新
                axis_y_dropdown = inputs.itemById('axis_y_selection')
                if axis_y_dropdown:
                    axis_y_dropdown.listItems.clear()
                    for i, axis_name in enumerate(axis_names):
                        is_selected = (i == config.AXIS_Y)
                        axis_y_dropdown.listItems.add(axis_name, is_selected)
        except Exception as e:
            futil.log(f"軸リスト更新でエラーが発生しました: {str(e)}")


# 入力値の検証
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # 全ての入力値が有効かどうかを確認
    # 問題がなければtrue, あればfalseを設定
    args.areInputsValid = True


# コマンド終了時の処理
def command_destroy(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} コマンド終了')

    # 注意: 設定ダイアログでPygameを終了しないように変更
    # ジョイスティック機能を継続的に使用できるようにするため
    
    # JoystickThreadとJoystickManagerはシングルトンのまま動作し続ける
    
    # ローカルハンドラーのクリア
    global local_handlers
    local_handlers = []
