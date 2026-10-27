"""Generate tileable PBR textures for the hotel laundry props.

Run inside Blender (numpy is bundled). Writes PNGs to TEX_DIR.
All textures are periodic (FFT filtered) so they tile without seams.
Normal maps use the OpenGL (+Y up) convention, which glTF and Blender expect.
"""
import os
import numpy as np
import bpy

TEX_DIR = os.path.expanduser("~/Documents/Blender/HotelLaundry/textures")
os.makedirs(TEX_DIR, exist_ok=True)
RNG = np.random.default_rng(7)


def filtered_noise(n, sx, sy):
    """Periodic gaussian-filtered white noise, normalised to 0..1.

    sx, sy are blur widths in pixels; a large sx with small sy gives
    horizontal streaks (brushed metal).
    """
    white = RNG.standard_normal((n, n))
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    kernel = np.exp(-2 * (np.pi ** 2) * ((fx * sx) ** 2 + (fy * sy) ** 2))
    out = np.real(np.fft.ifft2(np.fft.fft2(white) * kernel))
    out -= out.min()
    return out / max(out.max(), 1e-8)


def height_to_normal(h, strength):
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5 * strength
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5 * strength
    nz = np.ones_like(h)
    length = np.sqrt(dx * dx + dy * dy + nz * nz)
    # Rows run bottom-to-top in Blender images, so +dy already points up.
    return np.stack([(-dx / length) * 0.5 + 0.5,
                     (-dy / length) * 0.5 + 0.5,
                     (nz / length) * 0.5 + 0.5], axis=-1)


def save(name, rgb, non_color=False):
    """Save an (n, n) or (n, n, 3) float array as PNG in TEX_DIR."""
    if rgb.ndim == 2:
        rgb = np.repeat(rgb[..., None], 3, axis=-1)
    n = rgb.shape[0]
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((n, n, 1))], axis=-1)
    img = bpy.data.images.get(name) or bpy.data.images.new(name, n, n, alpha=False, float_buffer=False)
    if img.size[0] != n:
        img.scale(n, n)
    img.colorspace_settings.name = "Non-Color" if non_color else "sRGB"
    img.pixels.foreach_set(rgba.astype(np.float32).ravel())
    path = os.path.join(TEX_DIR, name + ".png")
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return path


def brushed_steel(n=1024):
    fine = filtered_noise(n, 180, 0.6)
    coarse = filtered_noise(n, 400, 6)
    smudge = filtered_noise(n, 60, 60)
    h = 0.75 * fine + 0.25 * coarse
    base = 0.62 + 0.06 * (h - 0.5) - 0.03 * smudge
    rough = 0.22 + 0.16 * h + 0.10 * smudge ** 3
    tint = np.stack([base * 0.985, base * 0.995, base * 1.0], axis=-1)
    save("steel_brushed_basecolor", tint)
    save("steel_brushed_roughness", rough, non_color=True)
    save("steel_brushed_normal", height_to_normal(h, 2.5), non_color=True)


def perforated_drum(n=1024, holes=16):
    """Stainless drum skin with a staggered grid of round holes."""
    y, x = np.mgrid[0:n, 0:n] / n * holes
    xs = x + 0.5 * (np.floor(y) % 2)
    d = np.hypot(xs % 1 - 0.5, y % 1 - 0.5)
    hole = np.clip((0.17 - d) / 0.02, 0, 1)            # 1 inside a hole
    rim = np.clip(1 - np.abs(d - 0.19) / 0.04, 0, 1)   # pressed rim around it
    streak = filtered_noise(n, 120, 0.8)
    base = (0.55 + 0.05 * streak) * (1 - hole) + 0.02 * hole
    save("drum_perforated_basecolor", base)
    save("drum_perforated_roughness", 0.25 + 0.1 * streak + 0.5 * hole, non_color=True)
    save("drum_perforated_normal", height_to_normal(-hole * 1.0 + rim * 0.5 + 0.05 * streak, 6.0), non_color=True)


def matte_plastic(n=512):
    grain = filtered_noise(n, 1.2, 1.2)
    blotch = filtered_noise(n, 40, 40)
    save("plastic_matte_roughness", 0.48 + 0.12 * grain + 0.08 * blotch, non_color=True)
    save("plastic_matte_normal", height_to_normal(grain, 1.2), non_color=True)


def rubber(n=512):
    grain = filtered_noise(n, 1.5, 1.5)
    save("rubber_roughness", 0.72 + 0.15 * grain, non_color=True)
    save("rubber_normal", height_to_normal(grain, 1.5), non_color=True)


def build_all():
    brushed_steel()
    perforated_drum()
    matte_plastic()
    rubber()
    return sorted(os.listdir(TEX_DIR))


if __name__ == "__main__":
    build_all()
