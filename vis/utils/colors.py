from PIL import Image

__all__ = ('get_dominant_colors', 'is_dark_color')


# Thanks to https://gist.github.com/zollinger/1722663
def get_dominant_colors(image: Image.Image, numcolors=10, resize=150):
    image = image.copy()

    # Resize image to speed up processing
    image.thumbnail((resize, resize))

    # Reduce to palette
    paletted = image.convert('P', palette=Image.ADAPTIVE, colors=numcolors)

    # Find dominant colors
    palette = paletted.getpalette()
    color_counts = sorted(paletted.getcolors(), reverse=True)

    colors = []
    for i in range(min(len(color_counts), numcolors)):
        palette_index = color_counts[i][1]
        dominant_color = palette[palette_index*3:palette_index*3+3]
        colors.append(tuple(dominant_color))

    while len(colors) < numcolors:
        colors.append(colors[0])

    return colors


# https://stackoverflow.com/questions/12043187/how-to-check-if-hex-color-is-too-black
def is_dark_color(color):
    r, g, b = color
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) < 70
