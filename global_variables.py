import platform

os = platform.system()
print(f'Operating system: {os}')

if os == 'Windows':
    render_image = True
else:
    render_image = False

run = True
recording = False