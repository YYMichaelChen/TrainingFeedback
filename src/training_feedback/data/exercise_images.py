"""受管动作图片的稳定文件映射与数据根内安全解析。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

EXERCISE_IMAGE_DIRECTORY = "exercise-images"

# 文件由用户放入当前数据根，不是应用二进制资源。稳定动作键只负责建立显式映射；
# 第 6 项双扩展名与当前真实文件名一致，不能在关联时静默改名。
BUNDLED_EXERCISE_IMAGE_FILES = {
    "launch.glute-bridge": "01-glute-bridge.png",
    "launch.clamshell": "02-clamshell.png",
    "launch.chair-squat": "03-chair-squat.png",
    "launch.dead-bug": "04-dead-bug.png",
    "launch.butterfly-glute-bridge": "05-frog-bridge.png",
    "launch.kneeling-hip-thrust": "06-kneeling-hip-thrust.png.png",
    "launch.static-glute-bridge": "07-isometric-glute-bridge.png",
    "launch.supine-360-diaphragmatic-breathing": "08-supine-360-breathing.png",
    "launch.small-cat-cow": "09-small-cat-cow.png",
    "launch.seated-90-90-hip-switch": "10-seated-90-90-switch.png",
    "launch.butterfly-stretch": "11-butterfly-stretch.png",
    "launch.supine-figure-four-stretch": "12-supine-figure-four-stretch.png",
    "launch.half-kneeling-hip-flexor-stretch": (
        "13-half-kneeling-hip-flexor-stretch.png"
    ),
    "launch.standing-forward-fold": "14-standing-forward-fold.png",
    "support.wall-calf-stretch": "15-wall-calf-stretch.png",
    "support.supine-single-knee-to-chest": "16-supine-single-knee-to-chest.png",
    "main.wall-supported-calf-raise": "17-wall-supported-calf-raise.png",
    "main.bird-dog": "18-bird-dog.png",
    "main.kneeling-straight-arm-lean": "19-kneeling-rock-back-push-up.png",
    "support.seated-upper-back-stretch": "20-kneeling-arms-forward-stretch.png",
}


def exercise_image_reference(filename: str) -> str:
    """把一个受管目录内的纯文件名转换为可随数据根搬迁的引用。"""
    value = PurePosixPath(str(filename).replace("\\", "/"))
    if value.is_absolute() or len(value.parts) != 1 or value.parts[0] in ("", ".", ".."):
        raise ValueError("Exercise image must be a filename inside exercise-images.")
    return f"{EXERCISE_IMAGE_DIRECTORY}/{value.parts[0]}"


def resolve_exercise_image_path(data_root: Path, reference: object) -> Path | None:
    """只解析数据根 exercise-images 内现存的普通文件；无效引用安全降级。"""
    if not isinstance(reference, str) or not reference:
        return None
    relative = PurePosixPath(reference.replace("\\", "/"))
    if relative.is_absolute() or not relative.parts:
        return None
    if relative.parts[0] != EXERCISE_IMAGE_DIRECTORY or ".." in relative.parts:
        return None
    root = Path(data_root).resolve()
    image_root = (root / EXERCISE_IMAGE_DIRECTORY).resolve()
    candidate = (root / Path(*relative.parts)).resolve()
    try:
        candidate.relative_to(image_root)
    except ValueError:
        return None
    if candidate == image_root or not candidate.is_file():
        return None
    return candidate
