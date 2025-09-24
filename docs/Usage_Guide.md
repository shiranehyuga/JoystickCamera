# カメラユーティリティライブラリの使用方法

このガイドでは、`cameraUtils`ライブラリを使って、Fusion 360のカメラを自分のアドインから操作する方法を説明します。

## 目次
- [初期設定](#初期設定)
- [基本的なカメラ操作](#基本的なカメラ操作)
- [高度なカメラ回転](#高度なカメラ回転)
- [クォータニオンの利用](#クォータニオンの利用)
- [トラブルシューティング](#トラブルシューティング)

## 初期設定

### 必要なインポート

```python
from lib.cameraUtils import CameraUtility, CameraRotations
from lib.cameraUtils.quaternion import Quaternion  # 必要に応じて
```

### 基本初期化

```python
class MyAddin:
    def __init__(self, context):
        # アドインの基本初期化...
        
        # カメラユーティリティの初期化
        self.camera_util = CameraUtility(
            rotation_scale=0.01,     # 回転の感度
            debug=False,             # デバッグ出力を無効化
            use_z_axis_rotation=False,  # Z軸回転の使用有無
            log_function=None        # カスタムログ関数（オプション）
        )
        
        # カメラ回転ヘルパークラスの初期化
        self.rotations = CameraRotations(self.camera_util)
```

### カスタムログ関数の利用

```python
def my_log_function(message, level=None):
    print(f"[MyAddin Camera] {message}")

# 初期化時にログ関数を渡す
self.camera_util = CameraUtility(log_function=my_log_function)
```

## 基本的なカメラ操作

### ビューの変更

```python
# ホームビューに移動
self.camera_util.navigate_to_home_view()

# 標準のビューに移動
# adsk.core.ViewOrientationsの定数を使用
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.TopViewOrientation)
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.BottomViewOrientation)
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.LeftViewOrientation)
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.RightViewOrientation)
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.FrontViewOrientation)
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.BackViewOrientation)
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.IsoTopRightViewOrientation)
self.camera_util.set_viewcube_orientation(adsk.core.ViewOrientations.IsoTopLeftViewOrientation)

# 現在のビューをリセット（フィット）
self.camera_util.reset_view()
```

### ジョイスティック/コントローラー入力との連携

```python
def on_input_event(self, x_input, y_input):
    """
    ジョイスティックやゲームコントローラーからの入力を処理
    x_input, y_input: -1.0〜1.0の範囲で正規化された値
    """
    # 入力値が十分に大きい場合のみ処理
    if abs(x_input) > 0.01 or abs(y_input) > 0.01:
        # カメラベクトルを取得
        forward, right, up = self.camera_util.get_camera_vectors()
        if forward and right and up:
            # スケーリング
            x_scaled = x_input * 0.01  # 適切な回転スケールに調整
            y_scaled = y_input * 0.01
            
            # クォータニオンを使用して回転
            from lib.cameraUtils.quaternion import Quaternion
            q_vertical = Quaternion.from_axis_angle(right, y_scaled)
            q_horizontal = Quaternion.from_axis_angle(up, -x_scaled)
            
            # 回転を結合して適用
            q_combined = q_horizontal * q_vertical
            self.camera_util.rotate_camera_with_quaternion(q_combined)
```

### 基本的なカメラ回転

```python
# 水平方向（Y軸周り）に回転
self.camera_util.rotate_camera_horizontal(45.0)  # 45度右回転

# 垂直方向（X軸周り）に回転
self.camera_util.rotate_camera_vertical(30.0)  # 30度上回転

# 任意の軸周りに回転
# 回転軸を定義
app = adsk.core.Application.get()
axis = app.activeProduct.rootComponent.zConstructionAxis.geometry.direction
# 軸周りに回転
self.camera_util.rotate_camera(axis, 60.0)  # 60度回転
```

### 感度の調整

```python
# 回転スケール（感度）を変更
self.camera_util.set_rotation_scale(0.005)  # より小さな値で感度を下げる
self.camera_util.set_rotation_scale(0.02)   # より大きな値で感度を上げる
```

## 高度なカメラ回転

### スクリーン座標系での回転

```python
# スクリーン座標系での水平方向回転（カメラの向きに関係なく水平方向）
self.rotations.rotate_screen_horizontal(90.0)  # 90度右回転

# スクリーン座標系での垂直方向回転
self.rotations.rotate_screen_vertical(45.0)  # 45度上回転

# スクリーン座標系でのZ軸（画面垂直方向）周り回転
self.rotations.rotate_around_screen_axis(30.0)  # 30度回転
```

### アニメーションを伴うスムーズな回転

```python
# 水平方向に90度をなめらかに回転（0.5秒かけて30ステップで）
self.rotations.smooth_rotate_horizontal(90.0, duration_seconds=0.5, steps=30)

# 垂直方向に45度をなめらかに回転
self.rotations.smooth_rotate_vertical(45.0, duration_seconds=0.7, steps=40)
```

### 特定の向きへの回転

```python
# 目標の方向ベクトルを作成
app = adsk.core.Application.get()
up_vector = adsk.core.Vector3D.create(0, 0, 1)  # 上方向をZ軸に
eye_vector = adsk.core.Vector3D.create(1, 1, 0)  # 視線方向

# アニメーションで特定の向きに回転
self.rotations.rotate_to_orientation(
    target_up=up_vector,
    target_eye=eye_vector,
    duration_seconds=0.8,
    steps=30
)
```

## クォータニオンの利用

より高度なカスタム回転を実装したい場合、クォータニオンクラスを直接使用できます：

```python
from lib.cameraUtils.quaternion import Quaternion
import math

# 軸と角度からクォータニオンを生成
app = adsk.core.Application.get()
axis = adsk.core.Vector3D.create(0, 1, 0)  # Y軸
angle_radians = math.radians(45.0)  # 45度をラジアンに変換
quat = Quaternion.from_axis_angle(axis, angle_radians)

# オイラー角からクォータニオンを生成
euler_quat = Quaternion.from_euler(
    math.radians(30),  # X軸周り回転
    math.radians(45),  # Y軸周り回転
    math.radians(0)    # Z軸周り回転
)

# ベクトルの回転
vector = adsk.core.Vector3D.create(1, 0, 0)
rotated_vector = quat.transform_vector(vector)

# 複数の回転の合成
quat1 = Quaternion.from_axis_angle(adsk.core.Vector3D.create(0, 1, 0), math.radians(30))
quat2 = Quaternion.from_axis_angle(adsk.core.Vector3D.create(1, 0, 0), math.radians(45))
combined_quat = quat1.multiply(quat2)  # 注：回転の順序に注意

# 合成した回転を適用
self.camera_util.rotate_camera_with_quaternion(combined_quat)
```

## トラブルシューティング

### デバッグ出力の有効化

問題がある場合、デバッグモードを有効にすることでより詳細な情報を得られます：

```python
# デバッグを有効化
self.camera_util = CameraUtility(debug=True)
```

### よくある問題と解決策

#### カメラが動かない

- アクティブなビューポートが取得できているか確認
- Fusion 360が背景で実行されているか確認

```python
# ビューポートが正しく取得できているか確認
viewport = self.camera_util.viewport
if not viewport:
    print("ビューポートが取得できません")
```

#### 回転が大きすぎる/小さすぎる

- 回転スケールを調整

```python
# 回転スケールを小さくして繊細な動きに
self.camera_util.set_rotation_scale(0.005)

# 回転スケールを大きくして大きな動きに
self.camera_util.set_rotation_scale(0.02)
```

#### アニメーション中にパフォーマンスが低下

- アニメーションのステップ数を減らす
- アニメーションの時間を短くする

```python
# よりシンプルなアニメーション設定
self.rotations.smooth_rotate_horizontal(90.0, duration_seconds=0.3, steps=15)
```

#### 予期しない回転方向

- 軸の向きを確認
- Z軸回転の使用設定を確認/変更

```python
# Z軸回転の設定を変更
self.camera_util.use_z_axis_rotation = True  # またはFalse
```