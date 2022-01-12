import keyboard
import vis

from PIL import Image
from pystray import Icon, Menu, MenuItem


def close():
    icon.stop()
    controller.close_all()
    vis.quit()
    exit()


controller = vis.WindowControllerThreadSafe()
keyboard.add_hotkey("win+shift+a", lambda: controller.enter_selection_window())

icon = Icon('Vis', Image.open("resources/icon.png"), menu=Menu(
    MenuItem("Select", controller.enter_selection_window, default=True),
    MenuItem('Close', close)))
icon.run_detached()

vis.behave_as_daemon()
vis.run()
