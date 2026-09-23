import pytest
from PySide6.QtGui import QColor, QImage

from training_feedback.data.exercise_images import (
    exercise_image_reference,
    resolve_exercise_image_path,
)
from training_feedback.ui.guidance_widgets import GuidanceView, render_guidance_html


def test_managed_image_reference_and_resolution_stay_inside_data_root(tmp_path):
    root = tmp_path / "data"
    images = root / "exercise-images"
    images.mkdir(parents=True)
    target = images / "动作图.png"
    target.write_bytes(b"fixture")

    reference = exercise_image_reference("动作图.png")

    assert reference == "exercise-images/动作图.png"
    assert resolve_exercise_image_path(root, reference) == target.resolve()
    assert resolve_exercise_image_path(root, "exercise-images/../secret.png") is None
    assert resolve_exercise_image_path(root, "../exercise-images/动作图.png") is None
    assert resolve_exercise_image_path(root, str(target.resolve())) is None
    with pytest.raises(ValueError):
        exercise_image_reference("nested/动作图.png")


def test_guidance_view_embeds_decodable_managed_image_and_degrades_if_missing(
    tmp_path, qt_app
):
    root = tmp_path / "data"
    images = root / "exercise-images"
    images.mkdir(parents=True)
    target = images / "view.png"
    bitmap = QImage(32, 24, QImage.Format.Format_RGB32)
    bitmap.fill(QColor("purple"))
    assert bitmap.save(str(target), "PNG")
    guidance = {
        "images": [
            {
                "path": "exercise-images/view.png",
                "caption": "测试动作示意图",
                "status": "available",
            }
        ]
    }

    html = render_guidance_html(guidance, data_root=root)
    view = GuidanceView(guidance, data_root=root)

    assert '<img src="file:' in html
    assert "测试动作示意图" in view.toPlainText()
    target.unlink()
    missing_html = render_guidance_html(guidance, data_root=root)
    assert "图片文件不可用" in missing_html
    assert "<img " not in missing_html
