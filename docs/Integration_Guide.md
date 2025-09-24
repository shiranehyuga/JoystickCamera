# カメラユーティリティの別アドインへの組み込み手順

このドキュメントでは、カメラユーティリティライブラリを自分のアドインプロジェクトに組み込む手順を説明します。

## 1. ファイルコピー

1. `JoystickCamera/lib/cameraUtils` ディレクトリを自分のアドインの `lib` ディレクトリにコピーします。

   ```
   JoystickCamera/lib/cameraUtils/* → YourAddin/lib/cameraUtils/
   ```

2. 必要に応じて、`JoystickCamera/lib/fusionAddInUtils` ディレクトリもコピーします（ログ機能などを使用する場合）。

## 2. モジュール構造の確認

アドインの構造が以下のようになっていることを確認します：

```
YourAddin/
  |- lib/
     |- cameraUtils/
        |- __init__.py
        |- quaternion.py
        |- camera_utility.py
        |- camera_rotations.py
     |- fusionAddInUtils/  （オプション）
        |- __init__.py
        |- ...
```

## 3. アドインへの統合

### 3.1 インポート方法

アドインのメインコード（例：YourAddin.py）で、以下のようにライブラリをインポートします：

```python
# アドインのルートからの相対インポート
from .lib.cameraUtils import CameraUtility, CameraRotations

# または、アドインのコマンドモジュール内からの場合
from ..lib.cameraUtils import CameraUtility, CameraRotations
```

### 3.2 初期化

ライブラリをアドインクラスのインスタンス変数として初期化します：

```python
def __init__(self, context):
    # 他のアドイン初期化コード...
    
    # カメラユーティリティを初期化
    self.camera_util = CameraUtility(
        rotation_scale=0.01,  # 適切なスケール値を設定
        debug=False,          # 通常は本番環境ではFalse
        use_z_axis_rotation=False,  # 必要に応じて変更
        log_function=self.log # カスタムログ関数を渡す
    )
    
    # 回転操作のヘルパークラスを初期化
    self.rotations = CameraRotations(self.camera_util)
    
def log(self, message, level=adsk.core.LogLevels.InfoLogLevel):
    # アドイン独自のログ機能を実装
    print(f"[MyAddin] {message}")
    # または fusionAddInUtils のログ関数を使用
    # from .lib import fusionAddInUtils as futil
    # futil.log(message, level)
```

## 4. イベント処理への統合

### 4.1 ジョイスティック/コントローラー入力との連携

```python
def on_controller_input(self, x_axis, y_axis, buttons):
    # ジョイスティック/コントローラーの入力を処理
    
    # 入力値が十分に大きい場合のみ処理
    if abs(x_axis) > 0.01 or abs(y_axis) > 0.01:
        # 回転スケールの設定
        rotation_scale = 0.01  # 適切な値に調整
        
        # カメラのベクトルを取得
        forward, right, up = self.camera_util.get_camera_vectors()
        if forward and right and up:
            # クォータニオン計算用の値を準備
            x_scaled = x_axis * rotation_scale
            y_scaled = y_axis * rotation_scale
            
            # クォータニオンの作成
            from lib.cameraUtils.quaternion import Quaternion
            q_vertical = Quaternion.from_axis_angle(right, y_scaled)
            q_horizontal = Quaternion.from_axis_angle(up, -x_scaled)
            
            # 回転を結合して適用
            q_combined = q_horizontal * q_vertical
            self.camera_util.rotate_camera_with_quaternion(q_combined)
    
    # ボタン入力の処理
    for btn_id, is_pressed in buttons.items():
        if is_pressed:
            self.handle_button(btn_id)

def handle_button(self, button_id):
    # ボタン押下時の処理
    if button_id == "btn_home":
        self.camera_util.navigate_to_home_view()
    elif button_id == "btn_front":
        self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.FrontViewOrientation)
    elif button_id == "btn_rotate_right":
        self.rotations.rotate_screen_horizontal(90.0)
    # その他のボタンに応じた処理...
```

### 4.2 コマンドとの統合

```python
def on_command_created(self, args):
    cmd = args.command
    inputs = cmd.commandInputs
    
    # コマンド入力を作成
    self.home_btn = inputs.addBoolValueInput("homeBtn", "ホームビュー", False, "", True)
    self.top_btn = inputs.addBoolValueInput("topBtn", "上面ビュー", False, "", True)
    self.rotate_btn = inputs.addBoolValueInput("rotateBtn", "右回転", False, "", True)
    
    # イベントハンドラを設定
    on_execute = MyCommandExecuteHandler(self.camera_util, self.rotations)
    cmd.execute.add(on_execute)
    
class MyCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, camera_util, rotations):
        super().__init__()
        self.camera_util = camera_util
        self.rotations = rotations
        
    def notify(self, args):
        cmd = args.command
        
        # 押されたボタンに応じた処理
        if cmd.commandInputs.itemById("homeBtn").value:
            self.camera_util.navigate_to_home_view()
        
        if cmd.commandInputs.itemById("topBtn").value:
            self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
        
        if cmd.commandInputs.itemById("rotateBtn").value:
            self.rotations.rotate_screen_horizontal(90.0)
```

## 5. カスタマイズと拡張

### 5.1 設定の調整

アドインの設定UIを通じてカメラの挙動をカスタマイズする例：

```python
def on_settings_changed(self, settings):
    # ユーザー設定からカメラの設定を更新
    rotation_speed = settings.get("camera_rotation_speed", 0.01)
    use_z_rotation = settings.get("use_z_axis_rotation", False)
    
    # カメラユーティリティの設定を更新
    self.camera_util.set_rotation_scale(rotation_speed)
    self.camera_util.use_z_axis_rotation = use_z_rotation
```

### 5.2 ライブラリの拡張

独自のカメラ機能を追加したい場合は、ライブラリのクラスを継承して拡張することも可能です：

```python
from .lib.cameraUtils import CameraUtility

class MyEnhancedCameraUtility(CameraUtility):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 追加の初期化...
        
    def my_custom_camera_function(self):
        # 独自のカメラ機能を実装
        # 基本クラスのメソッドは super() で呼び出せます
        
    def orbit_around_target(self, angle_degrees):
        # 例：ターゲット周りの軌道回転を実装
        # ...
```

## 6. トラブルシューティング

### 6.1 インポートエラー

```python
# モジュールのパスが正しく設定されていない場合、システムパスに追加する方法
import sys
import os
from os.path import dirname, join, abspath

# アドインのルートディレクトリを取得
addin_root = dirname(abspath(__file__))

# libディレクトリへのパスを追加
lib_path = join(addin_root, 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

# その後、通常の方法でインポート
from cameraUtils import CameraUtility, CameraRotations
```

### 6.2 カメラ操作が動作しない

- Fusion 360のアクティブなビューポートが正しく取得できているか確認する
- デバッグ出力を有効にして問題を特定する
- パラメータ値が極端に大きいまたは小さくないか確認する

### 6.3 パフォーマンスの問題

- 頻繁なカメラ更新はパフォーマンスに影響する可能性があるため、更新頻度を調整する
- 回転スケールを小さくして更新の影響を軽減する
- デバッグログを無効にして処理負荷を減らす