import adsk.core
import os
import traceback
import importlib
import time
import threading
from ...lib import fusionAddInUtils as futil
from ... import config
from ...module.JoystickManager import JoystickManager
from ...module.CameraController import CameraController

# グローバル変数
app = adsk.core.Application.get()
ui = app.userInterface

# コマンド情報の定義
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_settingsDialog'
CMD_NAME = 'ジョイスティック設定'
CMD_Description = 'ジョイスティックカメラの設定を行います'

# UI更新用タイマー
ui_update_timer = None
active_command = None

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
        # コマンド定義を追加または取得
        cmd_def = ui.commandDefinitions.itemById(CMD_ID)
        if not cmd_def:
            cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)
        
        # コマンド作成時のイベントハンドラを定義
        futil.add_handler(cmd_def.commandCreated, command_created)
        
        # UIにボタンを追加
        workspace = ui.workspaces.itemById(WORKSPACE_ID)
        panel = workspace.toolbarPanels.itemById(PANEL_ID)
        control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)
        control.isPromoted = IS_PROMOTED
        
        futil.log("settingsDialog start completed successfully")
        
    except Exception as e:
        futil.log(f"settingsDialog起動エラー: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
        
        # エラー発生時にはUIのワークスペースとパネルの情報を詳細にログ出力
        try:
            futil.log("利用可能なワークスペースを確認中...", adsk.core.LogLevels.InfoLogLevel)
            for i in range(ui.workspaces.count):
                workspace = ui.workspaces.item(i)
                futil.log(f"  ワークスペース: {workspace.name}, ID: {workspace.id}", adsk.core.LogLevels.InfoLogLevel)
                
                if workspace.id == WORKSPACE_ID:
                    futil.log(f"  '{WORKSPACE_ID}' ワークスペースが見つかりました", adsk.core.LogLevels.InfoLogLevel)
                    futil.log("  パネルを確認中...", adsk.core.LogLevels.InfoLogLevel)
                    
                    for j in range(workspace.toolbarPanels.count):
                        panel = workspace.toolbarPanels.item(j)
                        futil.log(f"    パネル: {panel.id}", adsk.core.LogLevels.InfoLogLevel)
                        
                    # 指定したパネルIDを確認
                    panel = workspace.toolbarPanels.itemById(PANEL_ID)
                    if panel:
                        futil.log(f"  '{PANEL_ID}' パネルが見つかりました", adsk.core.LogLevels.InfoLogLevel)
                    else:
                        futil.log(f"  '{PANEL_ID}' パネルが見つかりません", adsk.core.LogLevels.WarningLogLevel)
        except Exception as inner_e:
            futil.log(f"UIパネル情報の取得中にエラーが発生しました: {str(inner_e)}", adsk.core.LogLevels.ErrorLogLevel)
        
        futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    except Exception as e:
        futil.log(f"settingsDialog起動エラー: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
        futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)


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
                    futil.log(f"コマンドコントロールを削除しました: {CMD_ID}")
            else:
                futil.log(f"指定されたパネルが見つかりません: {PANEL_ID}", adsk.core.LogLevels.WarningLogLevel)
        else:
            futil.log(f"指定されたワークスペースが見つかりません: {WORKSPACE_ID}", adsk.core.LogLevels.WarningLogLevel)
        
        # コマンド定義を削除
        command_definition = ui.commandDefinitions.itemById(CMD_ID)
        if command_definition:
            command_definition.deleteMe()
            futil.log(f"コマンド定義を削除しました: {CMD_ID}")
        
        futil.log("settingsDialog stop completed successfully")
    except Exception as e:
        futil.log(f"settingsDialog停止エラー: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
        futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)


# コマンドのUIを構築する関数
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # デバッグログ
    futil.log(f'{CMD_NAME} コマンドが作成されました')

    # コマンドとそのUI要素を取得
    cmd = args.command
    inputs = cmd.commandInputs
    
    # ダイアログのサイズを設定（幅、高さ）- サイズを調整して全項目が表示されるようにする
    cmd.setDialogMinimumSize(500, 700)
    cmd.setDialogInitialSize(550, 750)
    
    # タイトルを設定してダイアログを明確にする
    cmd.dialogTitle = 'ジョイスティックカメラ設定'
    
    # UI設定を最適化
    cmd.okButtonText = '設定を保存'
    cmd.cancelButtonText = 'キャンセル'
    
    # デバッグ用にサイズを確認するログ
    futil.log(f"ダイアログサイズを設定しました: 最小 500x800, 初期 550x900", adsk.core.LogLevels.InfoLogLevel)
    
    # デバッグ用に設定値をログ出力 - 初期値を詳細に記録
    futil.log(f"設定ダイアログを作成 - 設定値確認", adsk.core.LogLevels.InfoLogLevel)
    futil.log(f"  ウェルカムメッセージ表示: {config.SHOW_WELCOME_MESSAGE} (型: {type(config.SHOW_WELCOME_MESSAGE)})", adsk.core.LogLevels.InfoLogLevel)
    futil.log(f"  自動リセット有効: {config.AUTO_RESET_ENABLED} (型: {type(config.AUTO_RESET_ENABLED)})", adsk.core.LogLevels.InfoLogLevel)
    futil.log(f"  自動リセット間隔: {config.AUTO_RESET_INTERVAL}分 (型: {type(config.AUTO_RESET_INTERVAL)})", adsk.core.LogLevels.InfoLogLevel)

    # タブを使わない、シンプルな垂直レイアウト
    
    # ========================
    # セクションごとに見出しを付ける
    # ========================
    
    # === 基本設定セクション ===
    inputs.addTextBoxCommandInput('header1', '', '<div style="font-size:14px; font-weight:bold; color:#0078d7; margin-bottom:10px;">コントローラー設定</div>', 1, True)
    
    # デバッグ設定
    debug_input = inputs.addBoolValueInput('debug_setting', 'デバッグログを表示', True, '', config.DEBUG)
    debug_input.tooltip = 'オンにするとデバッグログが出力されます'
    
    # コントローラー選択
    joystick_dropdown = inputs.addDropDownCommandInput('joystick_selection', 'コントローラー', 
                                                     adsk.core.DropDownStyles.TextListDropDownStyle)
    joystick_dropdown.tooltip = '使用するゲームコントローラーを選択します'
    
    # 軸選択
    axis_x_dropdown = inputs.addDropDownCommandInput('axis_x_selection', 'X軸（左右）', 
                                                   adsk.core.DropDownStyles.TextListDropDownStyle)
    axis_x_dropdown.tooltip = 'カメラの左右回転に使用する軸を選択します'
    
    axis_y_dropdown = inputs.addDropDownCommandInput('axis_y_selection', 'Y軸（上下）', 
                                                   adsk.core.DropDownStyles.TextListDropDownStyle)
    axis_y_dropdown.tooltip = 'カメラの上下回転に使用する軸を選択します'
    
    # ジョイスティック情報を取得
    try:
        joystick_manager = JoystickManager()
        if not joystick_manager.is_initialized:
            joystick_manager.initialize_pygame()
        
        joysticks = joystick_manager.get_joysticks()
        
        if joysticks:
            for i, joystick in enumerate(joysticks):
                is_selected = (i == config.SELECTED_JOYSTICK) if i < len(joysticks) else (i == 0)
                joystick_dropdown.listItems.add(joystick.get_name(), is_selected)
            
            axis_names = joystick_manager.get_axis_names()
            for i, axis_name in enumerate(axis_names):
                axis_x_dropdown.listItems.add(axis_name, (i == config.AXIS_X))
                axis_y_dropdown.listItems.add(axis_name, (i == config.AXIS_Y))
        else:
            joystick_dropdown.listItems.add('コントローラーが見つかりません', True)
            axis_x_dropdown.listItems.add('軸が見つかりません', True)
            axis_y_dropdown.listItems.add('軸が見つかりません', True)
    except Exception as e:
        futil.log(f"ジョイスティック情報の取得でエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
        joystick_dropdown.listItems.add('ジョイスティック情報の取得に失敗しました', True)
    
    # === カメラ操作モード ===
    inputs.addTextBoxCommandInput('header_camera_mode', '', '<div style="font-size:14px; font-weight:bold; color:#0078d7; margin-bottom:10px;">カメラ操作モード</div>', 1, True)
    
    # Z軸回転モード選択
    try:
        z_axis_mode_input = inputs.addBoolValueInput('use_z_axis_rotation', 'Z軸回転モードを使用', True, '', config.USE_Z_AXIS_ROTATION)
        z_axis_mode_input.tooltip = 'オンにすると、ジョイスティックのX軸操作でFusion内の3D空間の絶対Z軸周り（上下方向）に回転します。Z軸が画面上で上向きか下向きかで回転方向が反転します'
        futil.log(f'Z軸回転モード設定: {config.USE_Z_AXIS_ROTATION} (型: {type(config.USE_Z_AXIS_ROTATION)})', adsk.core.LogLevels.InfoLogLevel)
    except Exception as e:
        futil.log(f'Z軸回転モード設定の追加でエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
    
    # モード説明
    mode_description = '標準モード（オフ）: カメラ基準の水平・垂直軸で回転\nZ軸回転モード（オン）: 水平入力でFusionの絶対Z軸（上下方向）周りに回転、垂直入力は通常通り'
    inputs.addTextBoxCommandInput('mode_description', '', mode_description, 2, True)
    
    # === ボタン設定セクション ===
    inputs.addTextBoxCommandInput('header_button_settings', '', '<div style="font-size:14px; font-weight:bold; color:#0078d7; margin-bottom:10px;">ボタン設定</div>', 1, True)
    
    # ボタン機能の有効/無効
    try:
        button_enabled_input = inputs.addBoolValueInput('button_enabled', 'ボタン機能を有効にする', True, '', config.BUTTON_ENABLED)
        button_enabled_input.tooltip = 'ジョイスティックボタンの機能を有効にするかどうかを設定します'
        futil.log(f'ボタン機能設定: {config.BUTTON_ENABLED} (型: {type(config.BUTTON_ENABLED)})', adsk.core.LogLevels.InfoLogLevel)
    except Exception as e:
        futil.log(f'ボタン機能設定の追加でエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
    
    # ホームビューボタン選択を削除し、ボタン機能割り当て設定に変更
    try:
        # ジョイスティック情報を取得
        joystick_manager = JoystickManager()
        if not joystick_manager.is_initialized:
            joystick_manager.initialize_pygame()
        
        joysticks = joystick_manager.get_joysticks()
        
        if joysticks and joystick_manager.joystick:
            # ボタン数を取得
            num_buttons = joystick_manager.joystick.get_numbuttons()
            
            # ボタン機能割り当て設定のヘッダー
            inputs.addTextBoxCommandInput('button_assignment_header', '', '<b>ボタン機能の割り当て</b>', 1, True)
            inputs.addTextBoxCommandInput('button_assignment_info', '', f'検出されたボタン数: {num_buttons}', 1, True)
            
            # 利用可能な機能のリストを取得（config.pyと同じ形式に統一）
            available_functions = getattr(config, 'AVAILABLE_FUNCTIONS', [
                ("機能なし", "none"),
                ("ホームビュー", "home_view"),
                ("フィットビュー", "fit_view"),
                ("ビューキューブ前面", "viewcube_front"),
                ("ビューキューブ背面", "viewcube_back"),
                ("ビューキューブ左面", "viewcube_left"),
                ("ビューキューブ右面", "viewcube_right"),
                ("ビューキューブ上面", "viewcube_top"),
                ("ビューキューブ下面", "viewcube_bottom"),
                ("アイソメトリックビュー", "iso_view")
            ])
            
            # 最大10個のボタンまで設定可能
            max_buttons_to_show = min(num_buttons, 10)
            
            for i in range(max_buttons_to_show):
                # ボタン名はシンプルにインデックスのみ
                button_name = f"ボタン {i}"
                
                # このボタンに現在割り当てられている機能を取得
                current_assignment = config.BUTTON_ASSIGNMENTS.get(i, "none")
                
                # ドロップダウンを作成
                dropdown = inputs.addDropDownCommandInput(f'button_{i}_function', button_name, adsk.core.DropDownStyles.TextListDropDownStyle)
                dropdown.tooltip = f'ボタン {i} に割り当てる機能を選択してください'
                
                # 機能の選択肢を追加
                for display_name, func_id in available_functions:
                    is_selected = (func_id == current_assignment)
                    dropdown.listItems.add(display_name, is_selected)
                    
            futil.log(f'ボタン機能割り当てUI作成完了: {max_buttons_to_show} 個のボタン', adsk.core.LogLevels.InfoLogLevel)
            
    except Exception as e:
        futil.log(f'ボタン機能割り当て設定でエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
        futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    # === 十字キー設定セクション ===
    inputs.addTextBoxCommandInput('header_dpad_settings', '', '<div style="font-size:14px; font-weight:bold; color:#0078d7; margin-bottom:10px;">十字キー設定</div>', 1, True)
    
    # 十字キー機能の有効/無効
    try:
        dpad_enabled_input = inputs.addBoolValueInput('dpad_enabled', '十字キー機能を有効にする', True, '', getattr(config, 'DPAD_ENABLED', True))
        dpad_enabled_input.tooltip = '十字キー（D-pad）の機能を有効にするかどうかを設定します'
        futil.log(f'十字キー機能設定: {getattr(config, "DPAD_ENABLED", True)} (型: {type(getattr(config, "DPAD_ENABLED", True))})', adsk.core.LogLevels.InfoLogLevel)
    except Exception as e:
        futil.log(f'十字キー機能設定の追加でエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)

    # 十字キー機能割り当て設定
    try:
        # 十字キー機能割り当て設定のヘッダー
        inputs.addTextBoxCommandInput('dpad_assignment_header', '', '<b>十字キー機能の割り当て</b>', 1, True)
        inputs.addTextBoxCommandInput('dpad_assignment_info', '', '十字キーの各方向に機能を割り当てることができます', 1, True)
        
        # 十字キーの方向リスト
        dpad_directions = [
            ('dpad_up', '十字キー上'),
            ('dpad_down', '十字キー下'),
            ('dpad_left', '十字キー左'),
            ('dpad_right', '十字キー右')
        ]
        
        # 十字キーの各方向に対してドロップダウンを作成
        dpad_assignments = getattr(config, 'DPAD_ASSIGNMENTS', {})
        for direction_id, direction_name in dpad_directions:
            # この方向に現在割り当てられている機能を取得
            current_assignment = dpad_assignments.get(direction_id, "none")
            
            dropdown = inputs.addDropDownCommandInput(f'{direction_id}_function', direction_name, 
                                                    adsk.core.DropDownStyles.TextListDropDownStyle)
            dropdown.tooltip = f'{direction_name} に割り当てる機能を選択してください'
            
            # 利用可能な機能をドロップダウンに追加
            for display_name, func_id in config.AVAILABLE_FUNCTIONS:
                is_selected = (func_id == current_assignment)
                dropdown.listItems.add(display_name, is_selected)
                
        futil.log(f'十字キー機能割り当てUI作成完了: {len(dpad_directions)} 個の方向', adsk.core.LogLevels.InfoLogLevel)
        
    except Exception as e:
        futil.log(f'十字キー機能割り当て設定でエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
        futil.log(traceback.format_exc(), adsk.core.LogLevels.ErrorLogLevel)
    
    # 区切り線
    inputs.addTextBoxCommandInput('divider1', '', '<hr style="margin:15px 0px;">', 1, True)
    
    # === 感度設定セクション ===
    inputs.addTextBoxCommandInput('header2', '', '<div style="font-size:14px; font-weight:bold; color:#0078d7; margin-bottom:10px;">感度設定</div>', 1, True)
    inputs.addTextBoxCommandInput('sensitivity_info', '', 'カメラの動きと反応を調整します', 1, True)
    
    # 回転感度の設定（スライダー）
    futil.log(f'現在の回転感度: {config.ROTATION_SCALE}')
    rotation_slider = inputs.addFloatSliderCommandInput('rotation_scale_slider', '回転感度', '', 0.001, 0.5)
    rotation_slider.valueOne = config.ROTATION_SCALE
    rotation_slider.tooltip = '値が大きいほど、ジョイスティックの動きに対するカメラの回転が大きくなります'
    
    # デッドゾーンの設定
    deadzone_slider = inputs.addFloatSliderCommandInput('deadzone_slider', 'デッドゾーン', '', 0.01, 0.5)
    deadzone_slider.valueOne = config.DEAD_ZONE
    deadzone_slider.tooltip = '小さな入力を無視する範囲を設定します。手ぶれを防止するために使用します'
    
    # 更新頻度の設定（FPSで表示）
    min_fps = 10  # 最小FPS
    max_fps = 100 # 最大FPS
    current_fps = int(1 / config.UPDATE_RATE)
    fps_slider = inputs.addFloatSliderCommandInput('fps_slider', '更新頻度(FPS)', '', min_fps, max_fps)
    fps_slider.valueOne = float(current_fps)
    fps_slider.tooltip = 'カメラの更新頻度を設定します。値が大きいほど滑らかになりますが、負荷が高くなります'
    
    # 反応曲線の設定
    response_curve_slider = inputs.addFloatSliderCommandInput('response_curve_slider', '反応曲線', '', 0.1, 3.0)
    response_curve_slider.valueOne = config.RESPONSE_CURVE
    response_curve_slider.tooltip = '1.0: 線形（デフォルト）、<1.0: 高感度（平方根曲線）、>1.0: 低感度（二乗曲線）'
    
    # 区切り線
    inputs.addTextBoxCommandInput('divider2', '', '<hr style="margin:15px 0px;">', 1, True)
    
    # === システム設定セクション ===
    inputs.addTextBoxCommandInput('header3', '', '<div style="font-size:14px; font-weight:bold; color:#0078d7; margin-bottom:10px;">システム設定</div>', 1, True)
    
    try:
        # 起動時のメッセージ表示
        welcome_message_input = inputs.addBoolValueInput('show_welcome_message', '起動時のメッセージを表示', True, '', config.SHOW_WELCOME_MESSAGE)
        welcome_message_input.tooltip = 'チェックを入れると、アドイン起動時にウェルカムメッセージが表示されます'
        futil.log(f'ウェルカムメッセージ設定: {config.SHOW_WELCOME_MESSAGE} (型: {type(config.SHOW_WELCOME_MESSAGE)})', adsk.core.LogLevels.InfoLogLevel)
    except Exception as e:
        futil.log(f'ウェルカムメッセージ設定の追加でエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
    
    # 区切り線
    inputs.addTextBoxCommandInput('divider3', '', '<hr style="margin:15px 0px;">', 1, True)
    
    # === リセット機能セクション ===
    inputs.addTextBoxCommandInput('header4', '', '<div style="font-size:14px; font-weight:bold; color:#0078d7; margin-bottom:10px;">リセット機能</div>', 1, True)
    
    # マニュアルリセット機能
    reset_button = inputs.addBoolValueInput('reset_system', 'システムリセットを実行', False, '', False)
    reset_button.tooltip = '長時間使用時のパフォーマンス低下時に押してください。ジョイスティック処理をリセットします'
    
    # 空白を入れる
    inputs.addTextBoxCommandInput('reset_space', '', ' ', 1, True)
    
    try:
        # 自動リセット設定
        auto_reset_enable = inputs.addBoolValueInput('auto_reset_enable', '自動リセットを有効にする', True, '', config.AUTO_RESET_ENABLED)
        auto_reset_enable.tooltip = '定期的に自動でシステムをリセットします。長時間使用時のパフォーマンス低下を防ぎます'
        futil.log(f'自動リセット設定: {config.AUTO_RESET_ENABLED} (型: {type(config.AUTO_RESET_ENABLED)})', adsk.core.LogLevels.InfoLogLevel)
        
        # 自動リセットの間隔設定（分）
        interval_input = inputs.addIntegerSpinnerCommandInput('auto_reset_interval', 'リセット間隔（分）', 15, 240, 15, config.AUTO_RESET_INTERVAL)
        interval_input.tooltip = '何分おきに自動リセットを実行するか設定します'
        futil.log(f'リセット間隔設定: {config.AUTO_RESET_INTERVAL}分 (型: {type(config.AUTO_RESET_INTERVAL)})', adsk.core.LogLevels.InfoLogLevel)
    except Exception as e:
        futil.log(f'自動リセット設定の追加でエラーが発生しました: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)

    # イベントハンドラの登録
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)
    
    # ボタン検出機能のためにタイマーを設定
    from ...module.SharedState import shared_state
    shared_state.button_detect_mode = False  # 初期状態はオフ


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
    
    # Z軸回転モード設定
    z_axis_mode_input = inputs.itemById('use_z_axis_rotation')
    if z_axis_mode_input:
        old_value = config.USE_Z_AXIS_ROTATION
        config.USE_Z_AXIS_ROTATION = z_axis_mode_input.value
        futil.log(f'Z軸回転モード設定を更新: {old_value} -> {config.USE_Z_AXIS_ROTATION}')
    
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
            
        # ウェルカムメッセージ表示設定を更新
        welcome_message_input = inputs.itemById('show_welcome_message')
        if welcome_message_input:
            config.SHOW_WELCOME_MESSAGE = welcome_message_input.value
            futil.log(f'ウェルカムメッセージ表示設定を更新: {config.SHOW_WELCOME_MESSAGE}')
        else:
            futil.log(f'ウェルカムメッセージ設定の取得に失敗しました', adsk.core.LogLevels.WarningLogLevel)
        
        # 自動リセット設定を更新
        auto_reset_enable = inputs.itemById('auto_reset_enable')
        if auto_reset_enable:
            config.AUTO_RESET_ENABLED = auto_reset_enable.value
            futil.log(f'自動リセット有効設定を更新: {config.AUTO_RESET_ENABLED}')
        else:
            futil.log(f'自動リセット有効設定の取得に失敗しました', adsk.core.LogLevels.WarningLogLevel)
            
        auto_reset_interval = inputs.itemById('auto_reset_interval')
        if auto_reset_interval:
            config.AUTO_RESET_INTERVAL = auto_reset_interval.value
            futil.log(f'自動リセット間隔を更新: {config.AUTO_RESET_INTERVAL}分')
        else:
            futil.log(f'自動リセット間隔設定の取得に失敗しました', adsk.core.LogLevels.WarningLogLevel)
            
        # ボタン機能設定を更新
        button_enabled_input = inputs.itemById('button_enabled')
        if button_enabled_input:
            config.BUTTON_ENABLED = button_enabled_input.value
            futil.log(f'ボタン機能設定を更新: {config.BUTTON_ENABLED}')
        else:
            futil.log(f'ボタン機能設定の取得に失敗しました', adsk.core.LogLevels.WarningLogLevel)
        
        # ボタン機能の割り当て設定を更新
        new_button_assignments = {}
        
        # 利用可能な機能のリストを取得（config.pyと統一）
        available_functions = getattr(config, 'AVAILABLE_FUNCTIONS', [
            ("機能なし", "none"),
            ("ホームビュー", "home_view"),
            ("フィットビュー", "fit_view"),
            ("ビューキューブ前面", "viewcube_front"),
            ("ビューキューブ背面", "viewcube_back"),
            ("ビューキューブ左面", "viewcube_left"),
            ("ビューキューブ右面", "viewcube_right"),
            ("ビューキューブ上面", "viewcube_top"),
            ("ビューキューブ下面", "viewcube_bottom"),
            ("アイソメトリックビュー", "iso_view")
        ])
        
        # 最大10個のボタンの設定を確認
        for i in range(10):
            dropdown_id = f'button_{i}_function'
            dropdown = inputs.itemById(dropdown_id)
            
            if dropdown and dropdown.selectedItem:
                selected_index = dropdown.selectedItem.index
                if selected_index < len(available_functions):
                    # available_functionsは(display_name, function_id)の形式なので[1]で機能IDを取得
                    function_id = available_functions[selected_index][1]
                    if function_id != "none":  # "none"の場合は割り当てに追加しない
                        new_button_assignments[i] = function_id
                        futil.log(f'ボタン {i} に機能 "{function_id}" を割り当てました')
        
        # 設定を更新
        config.BUTTON_ASSIGNMENTS = new_button_assignments
        futil.log(f'ボタン機能割り当て設定を更新: {config.BUTTON_ASSIGNMENTS}')

        # 十字キー機能設定を更新
        dpad_enabled_input = inputs.itemById('dpad_enabled')
        if dpad_enabled_input:
            config.DPAD_ENABLED = dpad_enabled_input.value
            futil.log(f'十字キー機能設定を更新: {config.DPAD_ENABLED}')
        else:
            futil.log(f'十字キー機能設定の取得に失敗しました', adsk.core.LogLevels.WarningLogLevel)
        
        # 十字キー機能の割り当て設定を更新
        new_dpad_assignments = {}
        
        # 十字キーの方向リスト
        dpad_directions = ['dpad_up', 'dpad_down', 'dpad_left', 'dpad_right']
        
        for direction in dpad_directions:
            dropdown_id = f'{direction}_function'
            dropdown = inputs.itemById(dropdown_id)
            
            if dropdown and dropdown.selectedItem:
                selected_index = dropdown.selectedItem.index
                if selected_index < len(available_functions):
                    # available_functionsは(display_name, function_id)の形式なので[1]で機能IDを取得
                    function_id = available_functions[selected_index][1]
                    if function_id != "none":  # "none"の場合は割り当てに追加しない
                        new_dpad_assignments[direction] = function_id
                        futil.log(f'十字キー {direction} に機能 "{function_id}" を割り当てました')
        
        # 設定を更新
        config.DPAD_ASSIGNMENTS = new_dpad_assignments
        futil.log(f'十字キー機能割り当て設定を更新: {config.DPAD_ASSIGNMENTS}')
            
        # 設定項目のログ出力（デバッグ）
        try:
            for i in range(inputs.count):
                input_item = inputs.item(i)
                futil.log(f'設定項目 [{i}]: ID={input_item.id}, 種類={input_item.objectType}', adsk.core.LogLevels.InfoLogLevel)
        except:
            pass
        
        # リセットボタンがオンになっていたらシステムをリセット
        reset_button = inputs.itemById('reset_system')
        if reset_button and reset_button.value:
            futil.log('システムリセットが要求されました')
            
            # 既存のジョイスティック処理をリセット
            from ...module.JoystickAddIn import JoystickAddIn
            joystick_addin = JoystickAddIn()
            
            # スレッドを一度停止してから再開始
            joystick_addin.stop_joystick_thread()
            futil.log('ジョイスティックスレッドを停止しました')
            
            # Pygameを完全に再初期化
            from ...module.JoystickManager import JoystickManager
            joystick_manager = JoystickManager()
            joystick_manager.quit_pygame()
            futil.log('Pygameを終了しました')
            time.sleep(0.5)  # 少し待機して確実に終了させる
            
            joystick_manager.initialize_pygame()
            joysticks = joystick_manager.get_joysticks()
            futil.log(f'{len(joysticks)}個のジョイスティックを検出しました')
            
            # スレッドを再開
            joystick_addin.start_joystick_thread()
            futil.log('ジョイスティックスレッドを再開しました')
            
            ui.messageBox('システムが正常にリセットされました。パフォーマンスが改善されるはずです。', 'システムリセット')
        
        # CameraControllerに設定を直接反映
        from ...module.CameraController import CameraController
        CameraController.rotation_scale = config.ROTATION_SCALE
            
        # 設定をファイルに保存（メッセージボックスなし）
        if not config.save_settings():
            ui.messageBox('設定の保存に失敗しました。')
    except Exception as e:
        futil.log(f'エラー: {str(e)}', adsk.core.LogLevels.ErrorLogLevel)
        ui.messageBox(f'エラーが発生しました: {str(e)}')


# プレビュー更新時の処理 - タイマーベースの更新に任せるため最小限にする
def command_preview(args: adsk.core.CommandEventArgs):
    try:
        # ボタン機能割り当て設定用のプレビュー処理（必要に応じて追加）
        pass
    except Exception as e:
        futil.log(f"プレビュー更新でエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)


# UI更新タイマー関数
def start_ui_update_timer(command):
    global ui_update_timer, active_command
    
    # アクティブコマンドを保存
    active_command = command
    
    # すでにタイマーが動いていれば停止
    if ui_update_timer:
        ui_update_timer.cancel()
    
    # タイマー関数を定義
    def check_and_update_ui():
        global ui_update_timer
        try:
            from ...module.SharedState import shared_state
            
            # 検出モードがオンでボタン検出に変更があった場合
            if shared_state.button_detect_mode and shared_state.button_detection_changed:
                try:
                    if active_command:
                        # 検出結果表示ラベルを更新
                        inputs = active_command.commandInputs
                        detected_label = inputs.itemById('detected_button_label')
                        if detected_label:
                            detected_label.text = f"検出されたボタン: {shared_state.detected_button}"
                        
                        # 適用ボタンを有効化
                        apply_button = inputs.itemById('apply_detected_button')
                        if apply_button and shared_state.detected_button >= 0:
                            apply_button.value = True
                        
                        futil.log(f"UIを更新しました: ボタン {shared_state.detected_button}", adsk.core.LogLevels.InfoLogLevel)
                    
                    # フラグをリセット
                    shared_state.button_detection_changed = False
                except:
                    futil.log(f"UI更新でエラーが発生: {traceback.format_exc()}", adsk.core.LogLevels.WarningLogLevel)
            
            # 検出モードがアクティブな場合はタイマーを継続
            if shared_state.button_detect_mode:
                ui_update_timer = threading.Timer(0.1, check_and_update_ui)
                ui_update_timer.start()
        except:
            futil.log(f"タイマー関数でエラーが発生: {traceback.format_exc()}", adsk.core.LogLevels.ErrorLogLevel)
    
    # タイマー開始
    ui_update_timer = threading.Timer(0.1, check_and_update_ui)
    ui_update_timer.start()
    futil.log("ボタン検出用UIタイマーを開始しました", adsk.core.LogLevels.InfoLogLevel)


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
    
    # ボタン機能割り当ての変更処理
    elif changed_input.id.startswith('button_') and changed_input.id.endswith('_function'):
        # ボタン機能の割り当てが変更された場合
        button_index = changed_input.id.replace('button_', '').replace('_function', '')
        if button_index.isdigit():
            selected_function = changed_input.selectedItem.name if changed_input.selectedItem else "機能なし"
            futil.log(f'ボタン {button_index} の機能が変更されました: {selected_function}')
    
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
            futil.log(f"軸リスト更新でエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)


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
    
    # ボタン検出モードをオフにする
    try:
        from ...module.SharedState import shared_state
        if shared_state.button_detect_mode:
            shared_state.button_detect_mode = False
            shared_state.detected_button = -1
            futil.log("ボタン検出モードをオフにしました")
    except Exception as e:
        futil.log(f"ボタン検出モード終了でエラーが発生しました: {str(e)}", adsk.core.LogLevels.ErrorLogLevel)
    
    # ローカルハンドラーのクリア
    global local_handlers
    local_handlers = []
