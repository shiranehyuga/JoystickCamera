# Camera Utils チュートリアル

このチュートリアルでは、`cameraUtils`ライブラリを使用して、Fusion 360のカメラを簡単に操作する方法を学びます。

## 1. 基本的なカメラの動き

カメラを操作するための最初のステップを見てみましょう。

```python
import adsk.core
import adsk.fusion
import traceback

# カメラユーティリティライブラリをインポート
from lib.cameraUtils import CameraUtility

def run(context):
    try:
        # カメラユーティリティの初期化
        camera_util = CameraUtility()
        
        # ホームビューに移動
        camera_util.navigate_to_home_view()
        
        # 上面ビューに切り替え
        camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
        
        # カメラを90度右に回転
        camera_util.rotate_camera_horizontal(90.0)
        
    except:
        ui = adsk.core.Application.get().userInterface
        ui.messageBox('Error:\n{}'.format(traceback.format_exc()))
```

## 2. スムーズなカメラ回転

より高度なカメラ操作のために、`CameraRotations`クラスを使いましょう。

```python
from lib.cameraUtils import CameraUtility, CameraRotations

# カメラユーティリティの初期化
camera_util = CameraUtility()
rotations = CameraRotations(camera_util)

# スムーズに水平回転（90度、0.5秒かけて）
rotations.smooth_rotate_horizontal(90.0, 0.5, 30)

# スムーズに垂直回転（45度、0.5秒かけて）
rotations.smooth_rotate_vertical(45.0, 0.5, 30)

# カスタムの向きに回転
up = adsk.core.Vector3D.create(0, 0, 1)
eye = adsk.core.Vector3D.create(1, 1, 0.5)
rotations.rotate_to_orientation(up, eye, 1.0, 40)
```

## 3. ジョイスティック入力との連携

ジョイスティックやコントローラーからの入力を処理する方法です。

```python
def update_from_joystick(x_input, y_input, buttons):
    """
    ジョイスティック入力からカメラを更新
    
    引数:
        x_input: X軸の入力値（-1.0〜1.0）
        y_input: Y軸の入力値（-1.0〜1.0）
        buttons: ボタンの状態を表す辞書
    """
    # 入力値が一定以上ある場合のみ処理
    if abs(x_input) > 0.01 or abs(y_input) > 0.01:
        # カメラの現在の向きベクトルを取得
        forward, right, up = camera_util.get_camera_vectors()
        if not forward or not right or not up:
            return
        
        # 入力値をスケーリング
        rotation_scale = 0.01  # 感度調整
        x_scaled = x_input * rotation_scale
        y_scaled = y_input * rotation_scale
        
        # クォータニオン回転を計算
        from lib.cameraUtils.quaternion import Quaternion
        q_vertical = Quaternion.from_axis_angle(right, y_scaled)
        q_horizontal = Quaternion.from_axis_angle(up, -x_scaled)
        
        # 回転を組み合わせる
        q_combined = q_horizontal * q_vertical
        
        # カメラに回転を適用
        camera_util.rotate_camera_with_quaternion(q_combined)
    
    # ボタン入力の処理
    if buttons.get('button_1', False):
        camera_util.navigate_to_home_view()
    
    if buttons.get('button_2', False):
        camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
    
    if buttons.get('button_3', False):
        rotations.rotate_screen_horizontal(45.0)
```

## 4. UIコマンドとの連携

Fusion 360のUIコマンドから`cameraUtils`を使用する方法です。

```python
class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            cmd = args.command
            
            # UIコントロールの作成
            inputs = cmd.commandInputs
            
            # ボタンを追加
            home_btn = inputs.addBoolValueInput('homeBtn', 'ホームビュー', False, '', True)
            top_btn = inputs.addBoolValueInput('topBtn', '上面ビュー', False, '', True)
            rotate_btn = inputs.addBoolValueInput('rotateBtn', '回転', False, '', True)
            
            # イベントハンドラを設定
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            
        except:
            ui = adsk.core.Application.get().userInterface
            ui.messageBox('Error:\n{}'.format(traceback.format_exc()))

class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        self.camera_util = CameraUtility()
        self.rotations = CameraRotations(self.camera_util)
    
    def notify(self, args):
        try:
            cmd = args.command
            
            # ボタンの状態を確認して処理
            if cmd.commandInputs.itemById('homeBtn').value:
                self.camera_util.navigate_to_home_view()
            
            if cmd.commandInputs.itemById('topBtn').value:
                self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
            
            if cmd.commandInputs.itemById('rotateBtn').value:
                self.rotations.rotate_screen_horizontal(90.0)
            
        except:
            ui = adsk.core.Application.get().userInterface
            ui.messageBox('Error:\n{}'.format(traceback.format_exc()))
```

## 5. クォータニオンを使った高度な回転

クォータニオンを直接扱って複雑な回転を実装する方法です。

```python
from lib.cameraUtils.quaternion import Quaternion
import math

# 軸と角度からクォータニオンを作成
axis = adsk.core.Vector3D.create(0, 1, 0)  # Y軸
angle_radians = math.radians(45.0)
quat = Quaternion.from_axis_angle(axis, angle_radians)

# オイラー角からクォータニオンを作成
euler_quat = Quaternion.from_euler(
    math.radians(30),  # X軸回転
    math.radians(45),  # Y軸回転
    math.radians(0)    # Z軸回転
)

# ベクトルを回転させる
vector = adsk.core.Vector3D.create(1, 0, 0)
rotated_vector = quat.transform_vector(vector)

# 複数の回転を合成
quat1 = Quaternion.from_axis_angle(adsk.core.Vector3D.create(0, 1, 0), math.radians(30))
quat2 = Quaternion.from_axis_angle(adsk.core.Vector3D.create(1, 0, 0), math.radians(45))
combined_quat = quat1.multiply(quat2)

# カメラに適用
camera_util = CameraUtility()
viewport = camera_util.viewport
eye = viewport.camera.eye
target = viewport.camera.target
up = viewport.camera.upVector

# 視線ベクトルと上方向ベクトルを計算
eye_vector = adsk.core.Vector3D.create(
    eye.x - target.x,
    eye.y - target.y,
    eye.z - target.z
)

# ベクトルを回転
new_eye_vector = combined_quat.transform_vector(eye_vector)
new_up_vector = combined_quat.transform_vector(up)

# 新しいカメラ位置を計算
new_eye = adsk.core.Point3D.create(
    target.x + new_eye_vector.x,
    target.y + new_eye_vector.y,
    target.z + new_eye_vector.z
)

# カメラに適用
viewport.camera.eye = new_eye
viewport.camera.upVector = new_up_vector
viewport.camera.isSmoothTransition = False
viewport.refresh()
```

## 6. カスタム設定とログ

カスタム設定とログ機能を使う方法です。

```python
def my_log_function(message, level=None):
    print(f"[CameraUtils] {message}")

# カスタムログ関数を使用してカメラユーティリティを初期化
camera_util = CameraUtility(
    rotation_scale=0.015,  # 回転スケールをカスタマイズ
    debug=True,            # デバッグ出力を有効化
    use_z_axis_rotation=True,  # Z軸回転を使用
    log_function=my_log_function  # カスタムログ関数を設定
)

# 後から設定を変更
camera_util.set_rotation_scale(0.02)  # 回転スケールを変更
camera_util.use_z_axis_rotation = False  # Z軸回転を無効化
```

## 7. エラー処理とトラブルシューティング

エラーを適切に処理する方法です。

```python
try:
    # カメラ操作を試みる
    camera_util = CameraUtility(debug=True)
    camera_util.rotate_camera_horizontal(45.0)
except Exception as e:
    # エラーを捕捉して処理
    ui = adsk.core.Application.get().userInterface
    
    # エラーの種類に応じたメッセージ
    if "viewport" in str(e).lower():
        ui.messageBox("ビューポートが取得できません。Fusionが正しく起動しているか確認してください。")
    elif "camera" in str(e).lower():
        ui.messageBox("カメラが取得できません。別のビューを開いてみてください。")
    else:
        ui.messageBox(f"カメラ操作中にエラーが発生しました：{str(e)}")
    
    # デバッグ情報をログに出力
    print(f"[ERROR] カメラエラー: {str(e)}")
    print(traceback.format_exc())
```

## 8. まとめ

カメラユーティリティライブラリを使いこなすことで、Fusion 360のカメラを簡単に操作できます。基本的なビュー変更から高度なアニメーション、クォータニオンを使った複雑な回転まで、様々なカメラ操作が可能です。

また、`docs`ディレクトリの`API_Reference.md`を参照して、さらに詳細なAPIドキュメントを確認することができます。

これらの例を自分のアドインに組み込んで、より使いやすいインターフェースを実現しましょう！