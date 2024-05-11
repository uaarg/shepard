from PIL import Image
import hashlib
import os

from src.modules.imaging.camera import DebugCamera


def md5sum(path: str | os.PathLike) -> bytes:
    with open(path, "rb") as f:
        contents = f.read()
        return hashlib.md5(contents).digest()


def test_debug_camera(tmp_path):
    cam = DebugCamera("res/test-image.jpeg")

    # Simple image capture
    im = cam.capture()
    assert im.width == 600
    assert im.height == 400

    # Can capture the image as an ndarray
    im_np = cam.caputure_as_ndarry()
    assert im_np.shape == (400, 600, 3)
    assert im_np.sum() == 121089435  # Stupid simple checksum

    # Can save the image to a path
    im_path = tmp_path / "copy.jpeg"
    cam.caputure_to(im_path)
    im_md5 = md5sum(im_path)

    # Manually save a copy of 'test-image.jpeg'.
    # This is required as Image.save() may differ slightly from
    # 'test-image.jpeg' due to changes from re-compression.
    og_im_path = tmp_path / "og.jpeg"
    og_im = Image.open("res/test-image.jpeg")
    og_im.save(og_im_path)
    og_im_md5 = md5sum(og_im_path)

    assert im_md5 == og_im_md5

    # Can shrink the size
    cam.set_size((100, 100))
    im = cam.capture()
    assert im.width == 100
    assert im.height == 100

    # Can increase the size
    cam.set_size((1000, 1000))
    im = cam.capture()
    assert im.width == 1000
    assert im.height == 1000

    # Can round-trip even after changing size
    cam.set_size((600, 400))
    im = cam.capture()
    assert im.tobytes() == og_im.tobytes()
