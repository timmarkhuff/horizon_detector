from math import pi

FULL_ROTATION = 2 * pi
new_lines = []


def adjust_angle(angle: float, sky_is_up: bool) -> float:
    """
    Adjusts the angle within the range of 0-2*pi
    """
    angle = abs(angle % FULL_ROTATION)
    in_sky_is_up_sector = (angle >= FULL_ROTATION * .75  or (angle > 0 and angle <= FULL_ROTATION * .25))

    if sky_is_up == in_sky_is_up_sector:
        return angle
    if angle < pi:
        angle += pi
    else:
        angle -= pi
    return angle

# read labels.txt
label_filepath = r"C:\Users\Owner\Desktop\horizon_detector\training_data\1900_images\ORIGINAL labels.txt"
with open(label_filepath, encoding='utf-8-sig') as f:
    lines = f.readlines()

for line in lines:
    filename, angle, offset, sky_is_up = line.split(',')
    angle = float(angle)
    sky_is_up = bool(int(sky_is_up))
    angle = adjust_angle(angle, sky_is_up)
    new_lines.append(f'{filename},{angle},{offset}')


label_filepath = r"C:\Users\Owner\Desktop\horizon_detector\training_data\1900_images\NEW labels.txt"
with open(label_filepath, 'w') as f:
    for line in new_lines:
        f.write(line + '\n')

print("done!")