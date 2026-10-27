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
    # Real brushing is very fine: keep streak contrast low, mostly 1-2 px wide.
    fine = filtered_noise(n, 220, 0.45)
    coarse = filtered_noise(n, 500, 3)
    smudge = filtered_noise(n, 60, 60)
    h = 0.9 * fine + 0.1 * coarse
    base = 0.63 + 0.025 * (h - 0.5) - 0.025 * smudge
    rough = 0.24 + 0.07 * h + 0.08 * smudge ** 3
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


def stainless_satin(n=2048):
    """Realistic satin-brushed stainless: hairline grain, faint longer scratches,
    soft hand-smudges and a few oily fingerprints. One tile = 0.5 m, grain along U."""
    hair = filtered_noise(n, 600, 0.35)            # ~1 px hairlines, very long
    scratch = filtered_noise(n, 1500, 1.2)
    scratch = np.clip((scratch - 0.62) / 0.2, 0, 1) ** 2
    smudge = filtered_noise(n, 140, 140)
    blotch = filtered_noise(n, 40, 40)
    # Fingerprints: a few oval patches of fine concentric ridges.
    yy, xx = np.mgrid[0:n, 0:n] / n
    prints = np.zeros((n, n))
    for _ in range(7):
        cx, cy = RNG.random(2)
        ax, ay = 0.018 + 0.01 * RNG.random(), 0.024 + 0.012 * RNG.random()
        dx = (xx - cx + 0.5) % 1 - 0.5
        dy = (yy - cy + 0.5) % 1 - 0.5
        r = np.sqrt((dx / ax) ** 2 + (dy / ay) ** 2)
        ridges = 0.5 + 0.5 * np.sin(r * 55)
        prints = np.maximum(prints, np.clip(1 - r, 0, 1) ** 0.6 * ridges)
    h = 0.8 * hair + 0.2 * scratch
    base = 0.6 + 0.03 * (hair - 0.5) - 0.02 * blotch - 0.015 * prints
    rough = 0.2 + 0.07 * hair + 0.1 * smudge ** 2 + 0.05 * scratch - 0.08 * prints + 0.04 * blotch
    tint = np.stack([base * 0.985, base * 0.995, base], axis=-1)
    save("stainless_satin_basecolor", tint)
    save("stainless_satin_roughness", np.clip(rough, 0.08, 0.6), non_color=True)
    save("stainless_satin_normal", height_to_normal(h, 1.4), non_color=True)


def painted_metal(n=1024):
    """Powder-coated sheet metal: soft orange-peel bumps, faint mottling."""
    peel = filtered_noise(n, 3.0, 3.0)
    mottle = filtered_noise(n, 90, 90)
    save("paint_powder_roughness", 0.36 + 0.08 * peel + 0.08 * mottle, non_color=True)
    save("paint_powder_normal", height_to_normal(peel, 1.6), non_color=True)


def ceiling_tile(n=1024):
    """2 x 2 drop-ceiling tiles (0.6 m each) with fissured acoustic surface and
    the white T-bar grid baked in. One texture tile = 1.2 m."""
    y, x = np.mgrid[0:n, 0:n] / n * 2.0            # tile units, 2 tiles per texture
    fx, fy = x % 1.0, y % 1.0
    bar = 0.04                                       # 24 mm T-bar on a 600 mm tile
    edge = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy))
    is_bar = edge < bar / 2
    bevel = np.clip((edge - bar / 2) / 0.012, 0, 1)  # tile edge rolls down into the grid
    pores = filtered_noise(n, 0.8, 0.8)
    fissure = filtered_noise(n, 6, 1.2) * filtered_noise(n, 1.2, 6)
    fiss = np.clip((0.12 - np.abs(fissure - 0.3)) / 0.12, 0, 1) ** 2
    pit = (pores < 0.18).astype(float)
    tile_h = 0.6 * bevel - 0.25 * pit - 0.35 * fiss
    h = np.where(is_bar, 0.2, tile_h)
    base_tile = 0.80 - 0.06 * pit - 0.08 * fiss + 0.02 * (pores - 0.5)
    base = np.where(is_bar, 0.86, base_tile)
    rgb = np.stack([base, base * 0.985, base * 0.955], axis=-1)
    save("ceiling_tile_basecolor", rgb)
    save("ceiling_tile_roughness", np.where(is_bar, 0.35, 0.9), non_color=True)
    save("ceiling_tile_normal", height_to_normal(h, 3.0), non_color=True)


def towel(n=512):
    """Terry cloth: dense loop pile plus a flat woven dobby band. One tile = 0.25 m."""
    loops = filtered_noise(n, 0.7, 0.7)
    clumps = filtered_noise(n, 3.0, 3.0)
    y = np.mgrid[0:n, 0:n][0] / n
    band = ((y % 0.5) > 0.42).astype(float)          # woven border band every half tile
    h = (0.6 * loops + 0.4 * clumps) * (1 - 0.8 * band) + 0.15 * band
    base = 0.86 - 0.08 * (1 - h) - 0.02 * band
    save("towel_basecolor", np.stack([base, base * 0.99, base * 0.96], axis=-1))
    save("towel_roughness", 0.92 - 0.1 * band, non_color=True)
    save("towel_normal", height_to_normal(h, 4.0), non_color=True)


def build_all():
    towel()
    ceiling_tile()
    painted_metal()
    brushed_steel()
    perforated_drum()
    matte_plastic()
    rubber()
    return sorted(os.listdir(TEX_DIR))


if __name__ == "__main__":
    build_all()
