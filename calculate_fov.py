# FOV 기반 Focal Length 계산

import math

# PyBullet 카메라 설정
WIDTH = 600
HEIGHT = 480
FOV = 60  # degrees

# FOV에서 focal length 계산
# fov_horizontal = 2 * atan(width / (2 * fx))
# fx = width / (2 * tan(fov/2))

fov_rad = math.radians(FOV)
fx = WIDTH / (2 * math.tan(fov_rad / 2))
fy = HEIGHT / (2 * math.tan(fov_rad / 2))

print(f"FOV {FOV}도에 대한 올바른 파라미터:")
print(f"WIDTH={WIDTH}, HEIGHT={HEIGHT}")
print(f"fx = {fx:.2f}")
print(f"fy = {fy:.2f}")
print(f"cx = {WIDTH/2:.2f}")
print(f"cy = {HEIGHT/2:.2f}")

print(f"\n현재 사용 중:")
print(f"fx = 525 (❌ 틀림!)")
print(f"fy = 525 (❌ 틀림!)")

print(f"\n비율:")
print(f"현재/올바름 = {525/fx:.3f}")
