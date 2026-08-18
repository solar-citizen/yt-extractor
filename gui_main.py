from gui.app import App
from utils.system_utils import SystemUtils

def main():
    SystemUtils.configure_utf8_console()
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
