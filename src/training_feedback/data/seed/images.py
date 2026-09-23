"""Application-owned source illustrations for the bundled catalog."""

from pathlib import Path

IMAGE_DIRECTORY = Path(__file__).with_name("images")

BUNDLED_IMAGE_FILENAMES = {
    "臀桥": "01-glute-bridge.png",
    "蚌式开合": "02-clamshell.png",
    "椅子深蹲": "03-chair-squat.png",
    "死虫式": "04-dead-bug.png",
    "蝴蝶臀桥": "05-frog-bridge.png",
    "跪姿臀冲": "06-kneeling-hip-thrust.png",
    "静态臀桥": "07-isometric-glute-bridge.png",
    "仰卧360°膈肌呼吸": "08-supine-360-breathing.png",
    "小幅猫牛式": "09-small-cat-cow.png",
    "坐姿90/90髋转换": "10-seated-90-90-switch.png",
    "蝴蝶式": "11-butterfly-stretch.png",
    "仰卧4字臀部拉伸": "12-supine-figure-four-stretch.png",
    "半跪髋屈肌拉伸": "13-half-kneeling-hip-flexor-stretch.png",
    "站立体前屈": "14-standing-forward-fold.png",
    "扶墙小腿拉伸": "15-wall-calf-stretch.png",
    "仰卧单膝抱胸": "16-supine-single-knee-to-chest.png",
    "扶墙提踵": "17-wall-supported-calf-raise.png",
    "鸟狗式": "18-bird-dog.png",
    "跪姿冲肩": "19-kneeling-rock-back-push-up.png",
    "跪姿双臂前伸拉伸": "20-kneeling-arms-forward-stretch.png",
    "仰卧直腿开合": "21-supine-straight-leg-open-close.png",
    "卷腹伸腿": "22-seated-supported-leg-extension.png",
    "卷腹踩单车": "23-seated-supported-bicycle.png",
    "卷腹并腿左右伸": "24-seated-supported-lateral-extension.png",
    "卷腹并腿分腿交替伸": "25-seated-supported-combination-extension.png",
    "臀桥腿开合": "26-glute-bridge-leg-open-close.png",
    "臀桥单侧踢腿": "27-glute-bridge-single-leg-kick.png",
    "单腿臀桥": "28-single-leg-glute-bridge.png",
    "直腿后踢": "29-quadruped-straight-leg-kickback.png",
    "驴踢": "30-donkey-kick.png",
    "驴踢脉冲": "31-donkey-kick-pulse.png",
    "斜向驴踢": "32-diagonal-donkey-kick.png",
    "消防栓": "33-fire-hydrant.png",
    "俯卧直腿抬腿": "34-prone-straight-leg-raise.png",
    "俯卧屈腿抬腿": "35-prone-bent-knee-leg-raise.png",
    "俯卧双腿屈腿抬腿": "36-prone-double-bent-knee-leg-raise.png",
}


def bundled_image_reference(canonical_name: str) -> dict:
    filename = BUNDLED_IMAGE_FILENAMES[canonical_name]
    return {
        "path": f"images/{filename}",
        "caption": f"{canonical_name}动作示意图",
        "status": "available",
    }


def bundled_image_assets() -> dict[str, bytes]:
    expected = set(BUNDLED_IMAGE_FILENAMES.values())
    actual = {path.name for path in IMAGE_DIRECTORY.iterdir() if path.is_file()}
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(
            f"Bundled image source inventory differs: missing={missing}, unexpected={unexpected}"
        )
    return {
        f"images/{filename}": (IMAGE_DIRECTORY / filename).read_bytes()
        for filename in sorted(expected)
    }
