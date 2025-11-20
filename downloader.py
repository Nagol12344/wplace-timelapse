import requests
import sys
import types, typing
from io import BytesIO
from PIL import Image

DOMAIN = "https://backend.wplace.live"

def main():
    args = sys.argv[1:]
    if len(args) != 8:
        print("Usage: python downloader.py <tx1> <ty1> <x1> <y1> <tx2> <ty2> <x2> <y2>")
        sys.exit(1)
    cord1 = (args[0], args[1], args[2], args[3])
    cord2 = (args[4], args[5], args[6], args[7])
    download_image(cord1, cord2)
    
def download_image(cord1, cord2, return_image=False) -> typing.Optional[Image.Image]:
    # First, determine the size of the final image
    num_tiles_x = int(cord2[0]) - int(cord1[0]) + 1
    num_tiles_y = int(cord2[1]) - int(cord1[1]) + 1
    row_widths = []
    row_heights = []

    # Precompute widths and heights for each tile
    for tx in range(int(cord1[0]), int(cord2[0]) + 1):
        widths = []
        heights = []
        for ty in range(int(cord1[1]), int(cord2[1]) + 1):
            xstart = int(cord1[2]) if tx == int(cord1[0]) else 0
            ystart = int(cord1[3]) if ty == int(cord1[1]) else 0
            xend = int(cord2[2]) if tx == int(cord2[0]) else 1000
            yend = int(cord2[3]) if ty == int(cord2[1]) else 1000
            widths.append(xend - xstart)
            heights.append(yend - ystart)
        row_widths.append(sum(widths))
        row_heights.append(max(heights))

    total_width = sum([
        int(cord2[2]) - int(cord1[2]) if tx == int(cord2[0]) and tx == int(cord1[0])
        else (1000 - int(cord1[2]) if tx == int(cord1[0])
        else (int(cord2[2]) if tx == int(cord2[0]) else 1000))
        for tx in range(int(cord1[0]), int(cord2[0]) + 1)
    ])
    total_height = sum([
        int(cord2[3]) - int(cord1[3]) if ty == int(cord2[1]) and ty == int(cord1[1])
        else (1000 - int(cord1[3]) if ty == int(cord1[1])
        else (int(cord2[3]) if ty == int(cord2[1]) else 1000))
        for ty in range(int(cord1[1]), int(cord2[1]) + 1)
    ])
    print(f"Final image size: {total_width}x{total_height}")
    # Set default color to #9ebdff (R:158, G:189, B:255, A:255)
    finalimage = Image.new("RGBA", (total_width, total_height))

    y_offset = 0
    for ty_idx, ty in enumerate(range(int(cord1[1]), int(cord2[1]) + 1)):
        x_offset = 0
        for tx_idx, tx in enumerate(range(int(cord1[0]), int(cord2[0]) + 1)):
            print(f"Downloading tile {tx}, {ty} from {cord1} to {cord2}")
            xstart = int(cord1[2]) if tx == int(cord1[0]) else 0
            ystart = int(cord1[3]) if ty == int(cord1[1]) else 0
            xend = int(cord2[2]) if tx == int(cord2[0]) else 1000
            yend = int(cord2[3]) if ty == int(cord2[1]) else 1000
            img = download_tile(tx, ty, xstart, ystart, xend, yend)
            finalimage.paste(img, (x_offset, y_offset))
            x_offset += img.width
        y_offset += img.height
    finalimage = Image.alpha_composite(Image.new("RGBA", finalimage.size, "#9ebdff"), finalimage)
    if return_image:
        return finalimage
    else:
        print(f"Saving image to {cord1}_{cord2}.png")  
    finalimage.save(f"{cord1}_{cord2}.png")
    
    
def download_tile(tilex, tiley, xstart, ystart, xend, yend) -> Image:
    url = f"{DOMAIN}/files/s0/tiles/{tilex}/{tiley}.png"
    response = requests.get(url)
    image_data = BytesIO(response.content)
    img = Image.open(image_data)

    img = img.crop((xstart, ystart, xend, yend))
    return img

if __name__ == "__main__":
    main()