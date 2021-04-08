from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from os import listdir
from pathlib import Path
from fnmatch import fnmatch
import json
from PIL import Image

SEQUENCE_PATH = Path('./')
WIDTH = 1024
HEIGHT = 100

def lerp_component(low, high, percent):
    return (high - low) * percent + low

def clamp_component(component):
    if component > 1.0:
        return 1.0
    elif component < 0.0:
        return 0.0
    else:
        return component

class Color:
    def __init__(self, r, g, b, w):
        self.r = r
        self.g = g
        self.b = b
        self.w = w

    def clamped(self):
        return Color(
                clamp_component(self.r),
                clamp_component(self.g),
                clamp_component(self.b),
                clamp_component(self.w),
        )

    @staticmethod
    def from_dict(d):
        return Color(
                d['r'],
                d['g'],
                d['b'],
                d['w'],
        )

    def lerp(self, other, percent):
        self_rgb = sRGBColor(self.r, self.g, self.b)
        other_rgb = sRGBColor(other.r, other.g, other.b)
        self_lab = convert_color(self_rgb, LabColor)
        other_lab = convert_color(other_rgb, LabColor)

        result_lab = LabColor(
                lerp_component(self_lab.lab_l, other_lab.lab_l, percent),
                lerp_component(self_lab.lab_a, other_lab.lab_a, percent),
                lerp_component(self_lab.lab_b, other_lab.lab_b, percent),
        )

        result_rgb = convert_color(result_lab, sRGBColor)

        return Color(
                clamp_component(result_rgb.rgb_r),
                clamp_component(result_rgb.rgb_g),
                clamp_component(result_rgb.rgb_b),
                lerp_component(self.w, other.w, percent),
        )

    def __str__(self):
        return '{{r: {}, g: {}, b: {}, w: {}}}' \
            .format(self.r, self.g, self.b, self.w)

    def __bytes__(self):
        return bytes([int(self.r * 255), int(self.g * 255), int(self.b * 255), int(self.w * 255)])

    def rgb(self):
        return (int(self.r * 255), int(self.g * 255), int(self.b * 255))

    def white(self):
        return (int(self.w * 255), int(self.w * 255), int(self.w * 255))


def generate_png(src_json):
    colors = []
    with open(src_json) as fin:
        j = json.load(fin)
        color_points = j['color_points']
        percent_points = j['percent_points']

        color_index = 0
        for sample_index in range(WIDTH):
            overall_percent = sample_index / WIDTH
            lerp_percent = 1.0 \
                - ((percent_points[color_index + 1] \
                    - overall_percent) \
                    / (percent_points[color_index + 1] \
                        - percent_points[color_index]))

            left_color = Color.from_dict(color_points[color_index])
            right_color = Color.from_dict(color_points[color_index + 1])

            colors.append(left_color.lerp(right_color, lerp_percent))

            if overall_percent >= percent_points[color_index + 1]:
                color_index += 1

    img = Image.new('RGB', (WIDTH, HEIGHT))

    color_tuples = list(map(lambda c: c.rgb(), colors))
    white_tuples = list(map(lambda c: c.white(), colors))

    data = color_tuples*(HEIGHT // 2) + white_tuples*(HEIGHT // 2)
    img.putdata(data)

    return img

def main():
    for sequence in listdir(SEQUENCE_PATH):
        if fnmatch(sequence, '*.json'):
            img = generate_png(SEQUENCE_PATH.joinpath(sequence))
            img.save(SEQUENCE_PATH.joinpath(sequence.replace('json', 'png')))

if __name__ == '__main__':
    main()
