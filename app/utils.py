from PIL import Image
import io

def tile_image_for_3ds(img: Image.Image) -> bytes:
    """
    Converts a PIL image into a 3DS-compatible 8x8 tiled RGBA8888 format.
    Assumes image is already resized to a multiple of 8 (e.g., 64x64 or 128x128).
    """
    width, height = img.size
    img_rgba = img.convert("RGBA")
    pixels = img_rgba.load()
    
    tiled_data = bytearray(width * height * 4)
    
    # 3DS PICA200 GPU uses 8x8 tiling
    for y in range(height):
        for x in range(width):
            # Calculate the 3DS tiled offset
            # This follows the 8x8 block ordering used by the 3DS GPU
            # Block offset + Pixel offset within block
            out_offset = (((y >> 3) * (width >> 3) + (x >> 3)) << 6) +                          ((x & 1) | ((y & 1) << 1) | ((x & 2) << 1) |                           ((y & 2) << 2) | ((x & 4) << 2) | ((y & 4) << 3))
            
            r, g, b, a = pixels[x, y]
            
            # RGBA8888 on 3DS is usually A B G R in memory (Little Endian)
            # But Citro2D/C3D often expects RGBA depending on the format chosen.
            # For GPU_RGBA8, it's 32-bit.
            base = out_offset * 4
            tiled_data[base] = a
            tiled_data[base + 1] = b
            tiled_data[base + 2] = g
            tiled_data[base + 3] = r
            
    return bytes(tiled_data)
