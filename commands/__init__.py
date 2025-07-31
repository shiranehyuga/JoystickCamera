# Here you define the commands that will be added to your add-in.
import sys
import importlib
import os
import traceback
import adsk.core

# 直接モジュールをインポート
try:
    # 新しい設定ダイアログのみ使用
    from .settingsDialog import entry as settingsDialog
    print("設定ダイアログをインポートしました")
except Exception as e:
    print(f"設定ダイアログのインポートに失敗しました: {e}")
    traceback.print_exc()

# Fusion will automatically call the start() and stop() functions.
def start():
    """
    コマンドの起動処理を行う
    """
    try:
        # 新しい方法: 直接インポートしたモジュールを使用
        try:
            # 新しい設定ダイアログのみ実行
            if 'settingsDialog' in globals():
                print("settingsDialog.startを実行します")
                settingsDialog.start()
            else:
                print("settingsDialogモジュールがインポートされていません")
        except Exception as e:
            print(f"設定ダイアログの実行でエラーが発生しました: {e}")
            traceback.print_exc()

        # パレット関連のコマンドを実行
        # paletteShow
        import_and_execute_command('paletteShow')
        
        # paletteSend
        import_and_execute_command('paletteSend')
        
        print("All commands started successfully")
    except Exception as e:
        print(f"Error starting commands: {e}")
        traceback.print_exc()

def stop():
    """
    コマンドの終了処理を行う
    """
    try:
        # 新しい方法: 直接インポートしたモジュールを使用
        try:
            # 新しい設定ダイアログのみ停止
            if 'settingsDialog' in globals():
                print("settingsDialog.stopを実行します")
                settingsDialog.stop()
            else:
                print("settingsDialogモジュールがインポートされていません")
        except Exception as e:
            print(f"設定ダイアログの停止でエラーが発生しました: {e}")
            traceback.print_exc()

        # 従来の方法（必要に応じて）
        # paletteShow
        clean_command('paletteShow')
        
        # paletteSend
        clean_command('paletteSend')
        
        # settingsDialog
        clean_command('settingsDialog')
        
        print("All commands stopped successfully")
    except Exception as e:
        print(f"Error stopping commands: {e}")
        traceback.print_exc()

def import_and_execute_command(command_name):
    """
    指定されたコマンド名のエントリポイントを実行する
    """
    try:
        # コマンドのエントリポイントパスを取得
        entry_path = os.path.join(os.path.dirname(__file__), command_name, 'entry.py')
        
        # そのファイルのコードを実行する
        with open(entry_path, 'r', encoding='utf-8') as file:
            code = file.read()
            # ファイル実行のためのグローバル名前空間を作成
            namespace = {
                '__file__': entry_path,
                'adsk': adsk
            }
            # コードを実行
            exec(code, namespace)
            
            # start関数があれば実行
            if 'start' in namespace:
                namespace['start']()
            else:
                print(f"Warning: {command_name} has no start function")
    except Exception as e:
        print(f"Error executing {command_name}: {e}")
        traceback.print_exc()

def clean_command(command_name):
    """
    指定されたコマンド名のUIを削除する
    """
    try:
        # コマンドのエントリポイントパスを取得
        entry_path = os.path.join(os.path.dirname(__file__), command_name, 'entry.py')
        
        # そのファイルのコードを実行する
        with open(entry_path, 'r', encoding='utf-8') as file:
            code = file.read()
            # ファイル実行のためのグローバル名前空間を作成
            namespace = {
                '__file__': entry_path,
                'adsk': adsk
            }
            # コードを実行
            exec(code, namespace)
            
            # stop関数があれば実行
            if 'stop' in namespace:
                namespace['stop']()
            else:
                print(f"Warning: {command_name} has no stop function")
    except Exception as e:
        print(f"Error cleaning {command_name}: {e}")
        traceback.print_exc()