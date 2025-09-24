# Fusion 360 カメラユーティリティライブラリ

このライブラリは、Fusion 360のカメラ操作機能を提供し、アドインからカメラの制御を容易に行うためのものです。特にジョイスティックや他の入力デバイスによるカメラのナビゲーション機能の実装に役立ちます。

## 機能概要

- カメラの回転・移動の制御
- クォータニオンを使用した滑らかな回転処理
- 標準ビュー（前面、側面、上面など）への移動
- アイソメトリックビューの設定
- 回転操作（水平、垂直、軸方向）
- ViewCubeの面に合わせた「スマート回転」機能

## インストール方法

1. アドインプロジェクト内に `lib/cameraUtils` ディレクトリをコピーします
2. 必要に応じて、`fusionAddInUtils`（ログ出力など）もコピーします

### ディレクトリ構造

```
your_addin/
  |- lib/
     |- cameraUtils/
        |- __init__.py
        |- quaternion.py
        |- camera_utility.py
        |- camera_rotations.py
```

## 基本的な使い方

### インポート

```python
# シンプルなインポート方法
from your_addin.lib.cameraUtils import CameraUtility, CameraRotations

# または個別にインポート
from your_addin.lib.cameraUtils.camera_utility import CameraUtility
from your_addin.lib.cameraUtils.camera_rotations import CameraRotations
from your_addin.lib.cameraUtils.quaternion import Quaternion
```

### 初期化

```python
# 基本的な初期化
camera_util = CameraUtility()

# カスタム設定での初期化
camera_util = CameraUtility(
    rotation_scale=0.01,        # カメラ回転の速度係数
    debug=True,                 # デバッグログの有効化
    use_z_axis_rotation=False,  # Z軸回転モードの使用
    log_function=my_log_func    # カスタムログ関数（オプション）
)

# 回転操作用のインスタンスを初期化
rotations = CameraRotations(camera_util)
```

### 基本的なカメラ操作

```python
# ホームビュー（正面図）に移動
camera_util.navigate_to_home_view()

# 現在のビューを全体表示（フィット）
camera_util.fit_view()

# 標準ビューの設定（ViewCube面）
camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.FrontViewOrientation)
camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.RightViewOrientation)

# アイソメトリックビューの設定
camera_util.set_isometric_view()

# カメラ位置の更新（ジョイスティック入力などに基づく）
# joystick_x, joystick_y: -1.0 から 1.0 の範囲の値
camera_util.update_camera_position(joystick_x, joystick_y)
```

### 回転操作

```python
# 水平方向の回転（右：正の値、左：負の値）
rotations.rotate_screen_horizontal(90.0)   # 右に90度回転
rotations.rotate_screen_horizontal(-90.0)  # 左に90度回転

# 垂直方向の回転（上：正の値、下：負の値）
rotations.rotate_screen_vertical(90.0)    # 上に90度回転
rotations.rotate_screen_vertical(-90.0)   # 下に90度回転

# 視線方向軸での回転（時計回り：正の値、反時計回り：負の値）
rotations.rotate_screen_axial(90.0)    # 時計回りに90度回転
rotations.rotate_screen_axial(-90.0)   # 反時計回りに90度回転
```

### スマート回転操作

スマート回転は、現在の視点が標準ViewCube面でない場合、まず最も近いViewCube面に移動してから回転を行います。

```python
# 最寄りのViewCube面に移動
rotations.move_to_nearest_viewcube_face()

# スマート水平回転
rotations.smart_rotate_horizontal(90.0)   # スマート右回転
rotations.smart_rotate_horizontal(-90.0)  # スマート左回転

# スマート垂直回転
rotations.smart_rotate_vertical(90.0)    # スマート上回転
rotations.smart_rotate_vertical(-90.0)   # スマート下回転

# スマート軸回転
rotations.smart_rotate_axial(90.0)    # スマート時計回り回転
rotations.smart_rotate_axial(-90.0)   # スマート反時計回り回転
```

## アドインへの統合例

### 1. クラス内での使用例

```python
import adsk.core
import adsk.fusion
from .lib.cameraUtils import CameraUtility, CameraRotations

class MyAddin:
    def __init__(self):
        # カメラユーティリティを初期化
        self.camera_util = CameraUtility(
            rotation_scale=0.01,
            debug=False,
            use_z_axis_rotation=False,
            log_function=self.log
        )
        
        # 回転操作用のクラスを初期化
        self.rotations = CameraRotations(self.camera_util)
    
    def log(self, message, level=adsk.core.LogLevels.InfoLogLevel):
        print(f"[MyAddin] {message}")
    
    def handle_joystick_input(self, x_axis, y_axis):
        # ジョイスティック入力に基づいてカメラ位置を更新
        self.camera_util.update_camera_position(x_axis, y_axis)
    
    def handle_button_press(self, button_id):
        if button_id == "home":
            self.camera_util.navigate_to_home_view()
        elif button_id == "top_view":
            self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
        elif button_id == "rotate_right":
            self.rotations.smart_rotate_horizontal(90.0)
        # その他のボタン処理...
```

### 2. コマンド/イベントでの使用例

```python
import adsk.core
import adsk.fusion
import traceback
from .lib.cameraUtils import CameraUtility, CameraRotations

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # カメラユーティリティを初期化
        camera_util = CameraUtility()
        rotations = CameraRotations(camera_util)
        
        # コマンド作成
        cmd_def = ui.commandDefinitions.addButtonDefinition(
            'myCameraControlCmd', 'カメラコントロール', 'カメラを操作します')
            
        # コマンドイベントハンドラを設定
        cmd_handler = MyCommandHandler(camera_util, rotations)
        cmd_def.commandCreated.add(cmd_handler)
        cmd_def.execute()
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyCommandHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, camera_util, rotations):
        super().__init__()
        self.camera_util = camera_util
        self.rotations = rotations
    
    def notify(self, args):
        try:
            cmd = args.command
            
            # ボタンを作成
            inputs = cmd.commandInputs
            home_btn = inputs.addBoolValueInput('homeBtn', 'ホームビュー', False)
            rotate_btn = inputs.addBoolValueInput('rotateRightBtn', '右に回転', False)
            
            # ボタン押下時のイベントハンドラを設定
            on_execute = MyExecuteHandler(self.camera_util, self.rotations)
            cmd.execute.add(on_execute)
            
        except:
            ui = adsk.core.Application.get().userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class MyExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, camera_util, rotations):
        super().__init__()
        self.camera_util = camera_util
        self.rotations = rotations
    
    def notify(self, args):
        try:
            cmd = args.command
            
            # 押されたボタンに対応するアクションを実行
            inputs = cmd.commandInputs
            home_btn = inputs.itemById('homeBtn')
            rotate_btn = inputs.itemById('rotateRightBtn')
            
            if home_btn.value:
                self.camera_util.navigate_to_home_view()
            
            if rotate_btn.value:
                self.rotations.smart_rotate_horizontal(90.0)
            
        except:
            ui = adsk.core.Application.get().userInterface
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
```

## クォータニオンの直接使用

高度なカメラ操作や独自の回転処理を実装したい場合は、Quaternionクラスを直接使用できます。

```python
from your_addin.lib.cameraUtils.quaternion import Quaternion
import adsk.core
import math

# 軸と角度からクォータニオンを作成
axis = adsk.core.Vector3D.create(0, 0, 1)  # Z軸
angle = math.radians(45)  # 45度をラジアンに変換
q = Quaternion.from_axis_angle(axis, angle)

# ベクトルをクォータニオンで回転
vector = adsk.core.Vector3D.create(1, 0, 0)
rotated_vector = q.transform_vector(vector)

# クォータニオンの合成
q1 = Quaternion.from_axis_angle(adsk.core.Vector3D.create(1, 0, 0), math.radians(30))
q2 = Quaternion.from_axis_angle(adsk.core.Vector3D.create(0, 1, 0), math.radians(45))
combined_q = q1 * q2  # q2の回転の後にq1の回転を適用
```

## 注意事項

- このライブラリはFusion 360のAPIを使用しており、Fusion 360の環境内でのみ動作します
- カメラ操作は視覚的な要素のため、パフォーマンスに影響を与える可能性があります
- 大きな回転値や頻繁な更新は、スムーズな動作を妨げる可能性があります
- Fusion 360のAPIの変更により、将来的に動作が変わる可能性があります

## トラブルシューティング

### カメラが更新されない
- アクティブなビューポートが取得できているか確認してください
- 回転スケールが適切な値に設定されているか確認してください

### 回転が意図した方向と異なる
- `use_z_axis_rotation`の設定を変更してみてください
- Z軸方向の回転と通常の回転モードでは、回転の挙動が変わります

### パフォーマンスの問題
- 回転スケールを小さくして更新頻度を下げてみてください
- デバッグモードをオフにしてログ出力を減らしてください

## ライセンス

このライブラリはオープンソースソフトウェアであり、自由に使用、改変、再配布できます。
ただし、使用にあたっては自己責任でお願いします。