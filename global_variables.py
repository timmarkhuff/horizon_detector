import platform

os = platform.system()

if os == 'Windows':
    render_image = True
else:
    render_image = False

run = True
recording = False