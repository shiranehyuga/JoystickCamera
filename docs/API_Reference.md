# Camera Utilities Library API Reference

## CameraUtility Class

### Constructor

```python
CameraUtility(
    rotation_scale: float = DEFAULT_ROTATION_SCALE,  # Default: 0.01
    debug: bool = DEFAULT_DEBUG,  # Default: False
    use_z_axis_rotation: bool = DEFAULT_USE_Z_AXIS_ROTATION,  # Default: False
    log_function: callable = None  # Optional custom logging function
)
```

### Methods

| Method | Description |
|--------|-------------|
| `log(message: str, level: adsk.core.LogLevels)` | ログメッセージを出力します |
| `set_rotation_scale(value: float)` | カメラの回転スケールを設定します |
| `navigate_to_home_view()` | カメラをホームビュー（正面図）に移動します |
| `fit_view()` | 現在のビューを全体表示（フィット）します |
| `rotate_camera_with_quaternion(rotation_quaternion: Quaternion)` | クォータニオンを使用してカメラを回転させます<br>rotation_quaternion: 回転を表すQuaternion |
| `get_camera_vectors()` | カメラの現在の視線ベクトルと上方向ベクトルを取得します<br>戻り値: (forward, right, up) タプル |
| `set_viewcube_orientation(orientation: adsk.core.ViewOrientations)` | 指定されたViewCubeの向きにカメラを設定します |
| `set_isometric_view()` | アイソメトリック（等角投影）ビューを設定します |
| `rotate_camera(rotation_axis: adsk.core.Vector3D, angle_degrees: float = 90.0, smooth: bool = True)` | カメラを指定された軸と角度で回転します |

## CameraRotations Class

### Constructor

```python
CameraRotations(camera_util: CameraUtility)
```

### Methods

| Method | Description |
|--------|-------------|
| `_is_on_viewcube_face() -> bool` | 現在のカメラがViewCubeの標準面を向いているかをチェックします |
| `move_to_nearest_viewcube_face()` | 現在のカメラ視点から最も近いViewCube面に移動します |
| `rotate_screen_horizontal(angle_degrees: float)` | 画面の垂直軸で水平方向に回転します（右が正、左が負） |
| `rotate_screen_vertical(angle_degrees: float)` | 画面の水平軸で垂直方向に回転します（上が正、下が負） |
| `rotate_screen_axial(angle_degrees: float)` | 画面の視線方向軸で回転します（時計回りが正、反時計回りが負） |
| `smart_rotate_horizontal(angle_degrees: float)` | スマート水平回転：任意の向きの場合は最寄り面に移動してから回転します |
| `smart_rotate_vertical(angle_degrees: float)` | スマート垂直回転：任意の向きの場合は最寄り面に移動してから回転します |
| `smart_rotate_axial(angle_degrees: float)` | スマート軸回転：任意の向きの場合は最寄り面に移動してから回転します |

## Quaternion Class

### Constructor

```python
Quaternion(w: float, x: float, y: float, z: float)
```

### Static Methods

| Method | Description |
|--------|-------------|
| `from_axis_angle(axis: adsk.core.Vector3D, angle: float) -> Quaternion` | 軸と角度からクォータニオンを生成します |

### Instance Methods

| Method | Description |
|--------|-------------|
| `__mul__(other: Quaternion) -> Quaternion` | クォータニオン積を計算します（演算子 * を使用） |
| `to_matrix3d() -> list` | クォータニオンから3x3回転行列（4x4形式）を生成します |
| `transform_vector(vector: adsk.core.Vector3D) -> adsk.core.Vector3D` | ベクトルをこのクォータニオンで回転します |

## ViewOrientation Constants

ViewCubeの面の設定に使用する主な定数です。

| Constant | Description |
|----------|-------------|
| `adsk.core.ViewOrientations.FrontViewOrientation` | 前面 |
| `adsk.core.ViewOrientations.BackViewOrientation` | 背面 |
| `adsk.core.ViewOrientations.LeftViewOrientation` | 左面 |
| `adsk.core.ViewOrientations.RightViewOrientation` | 右面 |
| `adsk.core.ViewOrientations.TopViewOrientation` | 上面 |
| `adsk.core.ViewOrientations.BottomViewOrientation` | 下面 |
| `adsk.core.ViewOrientations.IsoTopRightViewOrientation` | 等角右上 |
| `adsk.core.ViewOrientations.IsoTopLeftViewOrientation` | 等角左上 |
| `adsk.core.ViewOrientations.IsoBottomRightViewOrientation` | 等角右下 |
| `adsk.core.ViewOrientations.IsoBottomLeftViewOrientation` | 等角左下 |
| `adsk.core.ViewOrientations.ArbitraryViewOrientation` | 任意の向き |