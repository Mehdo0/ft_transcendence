#   converting hexadecimal colors (#FF0000) to rgb colors (e.g., 255, 0, 0)
#   for an easier understanding from the ai
def hex_to_rgb(value):
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

