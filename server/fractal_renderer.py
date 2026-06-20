"""FCSTN Fractal Renderer - High-quality fractal image generation for the live server.
Produces beautiful Mandelbrot, Julia, 3D terrain, and orbit trap visualizations
with multiple color palettes. Outputs PNG images via API endpoints.
"""
import io, math, time, colorsys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

PALETTES = {
    "cyberpunk": [(0,0,20),(10,0,40),(60,0,80),(120,0,120),(200,0,100),(255,50,50),(255,200,0),(255,255,100)],
    "oceanic": [(0,10,30),(0,30,80),(0,60,140),(0,120,200),(60,180,240),(120,220,255),(200,240,255)],
    "fire": [(20,0,0),(60,0,0),(120,20,0),(200,60,0),(255,120,0),(255,180,50),(255,220,100),(255,255,200)],
    "aurora": [(0,20,10),(0,60,30),(0,120,80),(40,200,120),(120,255,100),(200,255,60),(255,200,80)],
    "neon": [(0,0,0),(20,0,40),(0,60,120),(0,200,200),(200,255,0),(255,0,200),(255,255,255)],
    "earth": [(0,40,10),(40,80,20),(80,120,40),(120,160,60),(160,180,80),(200,200,120),(240,220,180)],
    "magnetic": [(10,0,10),(40,0,60),(60,0,120),(80,60,200),(100,120,255),(140,200,255),(200,240,255)],
    "toxic": [(0,20,0),(20,60,0),(40,120,0),(100,200,0),(180,255,0),(255,255,0),(255,200,100)],
}

def build_palette_lut(colors, size=256):
    """Build a color lookup table from a list of RGB tuples."""
    lut = np.zeros((size, 3), dtype=np.uint8)
    n = len(colors)
    for i in range(size):
        t = (i / (size - 1)) * (n - 1)
        idx = int(t)
        frac = t - idx
        if idx >= n - 1:
            lut[i] = colors[-1]
        else:
            c0, c1 = colors[idx], colors[idx + 1]
            lut[i] = tuple(int(a + (b - a) * frac) for a, b in zip(c0, c1))
    return lut

def smooth_color(iterations, max_iter, z_value, palette, palette_offset=0.0):
    """Smooth coloring with palette mapping."""
    if iterations >= max_iter:
        return (0, 0, 0)
    mu = iterations + 1 - math.log2(math.log2(abs(z_value))) if z_value != 0 else iterations
    t = (mu / max_iter + palette_offset) % 1.0
    idx = int(t * (len(palette) - 1))
    frac = (t * (len(palette) - 1)) - idx
    if idx >= len(palette) - 1:
        return palette[-1]
    c0, c1 = palette[idx], palette[idx + 1]
    return tuple(int(a + (b - a) * frac) for a, b in zip(c0, c1))

def render_mandelbrot(width, height, palette_name="cyberpunk", max_iter=256,
                      center_x=-0.5, center_y=0.0, zoom=1.0, rotation=0.0,
                      palette_offset=0.0, julia=False, julia_cx=0.285, julia_cy=0.01):
    """Render a high-quality Mandelbrot or Julia set."""
    palette = PALETTES.get(palette_name, PALETTES["cyberpunk"])
    lut = build_palette_lut(palette)
    img = Image.new("RGB", (width, height))
    pixels = img.load()

    aspect = width / height
    half_w = 3.0 / zoom * aspect
    half_h = 3.0 / zoom
    cos_r, sin_r = math.cos(rotation), math.sin(rotation)

    for py in range(height):
        for px in range(width):
            nx = (px / width - 0.5) * 2.0
            ny = (py / height - 0.5) * 2.0
            rx = nx * cos_r - ny * sin_r
            ry = nx * sin_r + ny * cos_r
            cx = center_x + rx * half_w
            cy = center_y + ry * half_h

            if julia:
                zx, zy = cx, cy
                cx, cy = julia_cx, julia_cy
            else:
                zx, zy = 0.0, 0.0

            n = 0
            while n < max_iter:
                x2 = zx * zx - zy * zy + cx
                y2 = 2.0 * zx * zy + cy
                zx, zy = x2, y2
                if zx * zx + zy * zy > 4.0:
                    break
                n += 1

            if n >= max_iter:
                pixels[px, py] = (0, 0, 0)
            else:
                mu = n + 1 - math.log2(math.log2(math.sqrt(zx*zx + zy*zy))) if (zx*zx + zy*zy) > 0 else n
                t = ((mu / max_iter) + palette_offset) % 1.0
                idx = int(t * 255)
                pixels[px, py] = tuple(int(v) for v in lut[min(idx, 255)])

    return img

def render_terrain(width, height, palette_name="earth", center_x=-0.5, center_y=0.0, zoom=1.0,
                   elevation_scale=60.0, sun_angle=0.5):
    """Render a 3D isometric terrain map from Mandelbrot heightmap (Minecraft-like)."""
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import LightSource

    res = min(width, height) // 2
    xs = np.linspace(center_x - 2.0/zoom, center_x + 2.0/zoom, res)
    ys = np.linspace(center_y - 2.0/zoom, center_y + 2.0/zoom, res)
    X, Y = np.meshgrid(xs, ys)
    Z = np.zeros_like(X, dtype=np.float64)
    max_iter = 100

    for i in range(res):
        for j in range(res):
            cx, cy = X[i, j], Y[i, j]
            zx, zy = 0.0, 0.0
            n = 0
            while n < max_iter:
                zx, zy = zx*zx - zy*zy + cx, 2.0*zx*zy + cy
                if zx*zx + zy*zy > 4.0:
                    break
                n += 1
            Z[i, j] = n / max_iter

    Z = Z * elevation_scale

    palette_colors = PALETTES.get(palette_name, PALETTES["earth"])
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("custom",
        [(r/255, g/255, b/255) for r, g, b in palette_colors])

    fig = plt.figure(figsize=(width/100, height/100), dpi=100, facecolor='black')
    ax = fig.add_subplot(111, projection='3d', facecolor='black')
    ax.set_facecolor('black')

    ls = LightSource(azdeg=315, altdeg=sun_angle * 45)
    rgb = ls.shade(Z, cmap=cmap, vert_exag=2, blend_mode='overlay')

    ax.plot_surface(X, Y, Z, facecolors=rgb, rstride=1, cstride=1,
                    antialiased=True, shade=False, linewidth=0)
    ax.view_init(elev=30, azim=-60)
    ax.grid(False)
    ax.axis('off')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, facecolor='black', dpi=100)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)

def render_julia(width, height, palette_name="neon", max_iter=256,
                 cx=0.285, cy=0.01, zoom=1.0, palette_offset=0.0):
    """Render a Julia set with given seed point."""
    return render_mandelbrot(width, height, palette_name, max_iter,
                             center_x=0, center_y=0, zoom=zoom,
                             palette_offset=palette_offset,
                             julia=True, julia_cx=cx, julia_cy=cy)

def render_multi_fractal(width, height, palette_name="aurora", mode="layers",
                         center_x=-0.5, center_y=0.0, zoom=1.0):
    """Render composite multi-fractal with multiple layers."""
    base = render_mandelbrot(width, height, palette_name, 128, center_x, center_y, zoom)
    overlay = render_mandelbrot(width, height, "neon", 64, center_x + 0.1, center_y - 0.1, zoom * 0.5,
                                palette_offset=0.3)
    blended = Image.blend(base, overlay, 0.3)
    return blended

def render_map_tile(zoom_level, tile_x, tile_y, palette_name="earth"):
    """Render a single tile for a Minecraft-style map explorer."""
    size = 256
    span = 4.0 / (2 ** zoom_level)
    center_x = -0.5 + (tile_x - 2**(zoom_level-1)) * span
    center_y = 0.0 + (tile_y - 2**(zoom_level-1)) * span
    return render_terrain(size, size, palette_name, center_x, center_y, 2.0 / span)

def render_fractal_by_state(cognitive_state, width=960, height=540):
    """Render fractal image based on current cognitive state for dynamic visual feedback."""
    attn = cognitive_state.get('attention', 0.5)
    eng = cognitive_state.get('engagement', 0.5)
    load = cognitive_state.get('load', 0.3)
    val = cognitive_state.get('valence', 0.5)
    coherence = cognitive_state.get('coherence', 0.5)
    state_name = cognitive_state.get('state_name', 'resting')

    zoom = 1.0 + attn * 3.0 + eng * 2.0
    rotation = val * math.pi * 2 - math.pi
    offset = (1.0 - coherence) * 0.5
    cx = -0.5 + (val - 0.5) * 0.3
    cy = 0.0 + (attn - 0.5) * 0.2

    palette_switching = {
        "focused": "cyberpunk", "stressed": "fire",
        "fatigued": "oceanic", "engaged": "neon",
        "curious": "aurora", "resting": "magnetic",
    }
    palette = palette_switching.get(state_name, "cyberpunk")

    if load > 0.8:
        return render_mandelbrot(width, height, "fire", 128 + int(attn * 128),
                                 cx, cy, zoom, rotation, offset)
    elif coherence > 0.7:
        return render_julia(width, height, palette, 256, cx, cy, zoom, offset)
    else:
        return render_mandelbrot(width, height, palette, 128 + int(attn * 128),
                                 cx, cy, zoom, rotation, offset)
