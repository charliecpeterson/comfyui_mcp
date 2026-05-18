"""Image utilities and OpenPose drawing constants."""
from __future__ import annotations


def _resize_image_for_inline(data: bytes, max_long_edge: int = 2048, quality: int = 85) -> bytes | None:
    """Resize an image so its long edge is ≤ max_long_edge, encode as JPEG.
    Returns None if PIL unavailable or resize fails; caller falls back to metadata."""
    try:
        from PIL import Image as PILImage  # type: ignore[import-not-found]
        import io
    except ImportError:
        return None
    try:
        img = PILImage.open(io.BytesIO(data))
        if img.mode in ("RGBA", "LA", "P"):
            # JPEG can't carry alpha; flatten onto white
            bg = PILImage.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        long_edge = max(w, h)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
            img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return None


# OpenPose 18-keypoint connections (1-indexed in original; 0-indexed here).
# Standard COCO_18 / BODY_25 layout — first 18 indices are body, then optional ears.
_OPENPOSE_LIMB_PAIRS = [
    (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),  # arms
    (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),  # legs
    (1, 0), (0, 14), (14, 16), (0, 15), (15, 17),  # head/face
]
_OPENPOSE_LIMB_COLORS = [
    (255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0),
    (170, 255, 0), (85, 255, 0), (0, 255, 0), (0, 255, 85),
    (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
    (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255),
    (255, 0, 170),
]
_OPENPOSE_JOINT_COLORS = [
    (255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0),
    (170, 255, 0), (85, 255, 0), (0, 255, 0), (0, 255, 85),
    (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
    (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255),
    (255, 0, 170), (255, 0, 85),
]
