import adsk.core
import adsk.fusion
import traceback
import os
from typing import List, Dict, Any

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # ライブラリのインポート
        import sys
        from os.path import dirname, join, abspath
        
        # このスクリプトのパスを取得（Fusion 360のスクリプトとして実行する場合）
        script_path = dirname(abspath(__file__))
        
        # ライブラリのパスをシステムパスに追加
        lib_path = abspath(join(script_path, '..'))
        if lib_path not in sys.path:
            sys.path.append(lib_path)
        
        # ライブラリをインポート
        from lib.cameraUtils import CameraUtility, CameraRotations
        
        # カメラユーティリティの初期化
        camera_util = CameraUtility(
            rotation_scale=0.01,
            debug=True,
            use_z_axis_rotation=False,
            log_function=lambda msg, lvl: print(f"[CameraDemo] {msg}")
        )
        
        # 回転操作用のヘルパークラスを初期化
        rotations = CameraRotations(camera_util)
        
        # カメラ操作デモのコマンドを作成
        demo_commands = [
            {
                'name': 'ホームビュー',
                'action': lambda: camera_util.navigate_to_home_view()
            },
            {
                'name': 'フィットビュー',
                'action': lambda: camera_util.fit_view()
            },
            {
                'name': '前面ビュー',
                'action': lambda: camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.FrontViewOrientation)
            },
            {
                'name': '上面ビュー',
                'action': lambda: camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
            },
            {
                'name': '右面ビュー',
                'action': lambda: camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.RightViewOrientation)
            },
            {
                'name': 'アイソメトリックビュー',
                'action': lambda: camera_util.set_isometric_view()
            },
            {
                'name': '右に90度回転',
                'action': lambda: rotations.rotate_screen_horizontal(90.0)
            },
            {
                'name': '左に90度回転',
                'action': lambda: rotations.rotate_screen_horizontal(-90.0)
            },
            {
                'name': '上に90度回転',
                'action': lambda: rotations.rotate_screen_vertical(90.0)
            },
            {
                'name': 'スマート右回転',
                'action': lambda: rotations.smart_rotate_horizontal(90.0)
            },
        ]
        
        # デモ用ダイアログを表示
        cmd_items = []
        for i, cmd in enumerate(demo_commands):
            cmd_items.append(f"{i+1}: {cmd['name']}")
        
        selection = ui.listItems(
            'カメラユーティリティデモ',
            'テストしたい操作を選択してください:',
            cmd_items
        )
        
        if selection:
            # インデックスは1から始まるので、-1して配列インデックスに変換
            index = int(selection.split(':')[0]) - 1
            if 0 <= index < len(demo_commands):
                # 選択されたアクションを実行
                demo_commands[index]['action']()
                ui.messageBox(f"「{demo_commands[index]['name']}」を実行しました。")

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Clean up the UI
        # (この例ではクリーンアップするUIはありません)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))