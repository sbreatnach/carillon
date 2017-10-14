import signal
import os.path
import logging.config
import functools
import time
import sys
import argparse
import subprocess

from daemonize import Daemonize
import yaml
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

ETC_ROOT = os.path.join('/', 'etc', 'simplekeys')
CONFIG_ROOT = os.path.join(ETC_ROOT, 'conf.d')
USER_CONFIG = os.path.join('~', '.config', 'simplekeys')
SRC_ROOT = os.path.dirname(__file__)
WORKING_ROOT = os.getcwd()
ICON_DIR = os.path.join(SRC_ROOT, 'icons')

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/simplekeys.log',
            'maxBytes': 1024000,
            'backupCount': 3
        },
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO'
        }
    }
})


class Application(object):
    """
    Catch-all class for running the keyboards application
    """

    def __init__(self):
        super(Application, self).__init__()
        self.is_running = True
        self.menu = Gtk.Menu()
        self.icon = Gtk.StatusIcon()
        self.icon.set_has_tooltip(True)
        self.icon.connect('popup-menu', self.on_popup_menu)
        self.icon.connect('query-tooltip', self.set_tooltip)
        self._all_keyboards = []
        self.keyboard = None

    def load(self, config_filename):
        """
        Loads the application state from the given configuration file name

        :param config_filename:
        """
        config_file_path = self.get_file_path(config_filename)
        with open(config_file_path) as handle:
            config_data = yaml.load(handle)
        keyboards = config_data['keyboards']
        selected = config_data.get('selected', next(iter(keyboards.keys())))
        selected_keyboard = keyboards[selected]

        self.all_keyboards = keyboards
        self.set_keyboard(selected_keyboard)

    def on_popup_menu(self, icon, button, time):
        """
        Opens the popup menu for the given Gtk icon

        :param icon:
        :param button:
        :param time:
        :return:
        """
        def pos(menu, x, y, user_data):
            return Gtk.StatusIcon.position_menu(menu, x, y, user_data)
        self.menu.popup(None, None, pos, icon, button, time)

    def set_tooltip(self, widget, x, y, keyboard_mode, tooltip):
        """
        Sets the tooltip for a Gtk tooltip
        :param widget:
        :param x:
        :param y:
        :param keyboard_mode:
        :param tooltip:
        :return:
        """
        tooltip.set_text(self.keyboard['name'])
        return True

    def get_file_path(self, filename):
        """
        Finds the given filename in one of the supported directories.
        These are:

        * current working directory
        * XDG config directory e.g. ~/.config/simplekeys
        * /etc/simplekeys/conf.d
        * /etc/simplekeys
        * directory of package install

        :param filename:
        :return: absolute file path to first matching filename, or None if
        no matching filename found
        """
        file_path = None
        for path in [WORKING_ROOT,
                     USER_CONFIG,
                     CONFIG_ROOT,
                     ETC_ROOT,
                     SRC_ROOT]:
            search_path = os.path.join(path, filename)
            if os.path.exists(search_path):
                file_path = search_path
                break
        return file_path

    @property
    def all_keyboards(self):
        """
        Returns the list of configured keyboards
        :return:
        """
        return self._all_keyboards

    @all_keyboards.setter
    def all_keyboards(self, value):
        """
        Sets the list of keyboards for the application, loading the icon menu
        based on the list.

        :param value:
        """
        if value != self._all_keyboards:
            self._all_keyboards = value
            for keyboard in sorted(self._all_keyboards.values(),
                                   key=lambda val: val['name']):
                menu_item = Gtk.MenuItem()
                menu_item.set_label(keyboard['name'])
                menu_item.connect(
                    'activate',
                    functools.partial(self.set_keyboard, keyboard)
                )
                self.menu.append(menu_item)
            self.menu.show_all()

    def set_keyboard(self, new_keyboard, *args):
        """
        Sets the selected keyboard layout, updating UI and changing OS settings
        :param new_keyboard:
        :param args:
        """
        if self.keyboard != new_keyboard:
            logging.info('Selecting keyboard %s', new_keyboard['name'])
            self.keyboard = new_keyboard
            self.icon.set_from_file(
                os.path.join(ICON_DIR, new_keyboard['icon']))
            self.load_keyboard(new_keyboard)

    def load_keyboard(self, keyboard):
        """
        Loads the keyboard layout using OS system calls
        :param keyboard:
        """
        # uses setxkbmap which is as reliable as it gets for
        # setting keyboard layout in an X client environment
        set_args = ['setxkbmap',
                    '-model', keyboard['model'],
                    '-layout', keyboard['layout']]
        variant = keyboard.get('variant')
        if variant:
            set_args += ['-variant', variant]
        subprocess.check_call(set_args)

    def run(self):
        """
        Runs the application, managing the main loop
        """
        Gtk.init(sys.argv)
        while self.is_running:
            time.sleep(0.01)
            Gtk.main_iteration()


def on_shutdown(program, *args):
    """
    Shuts down the application
    :param program:
    :param args:
    """
    logging.info('Shutting down')
    program.is_running = False


def main():
    logging.info('Starting up')
    parser = argparse.ArgumentParser(
        description='Application to manage keyboard layouts')
    parser.add_argument('-d', '--daemonize', action='store_true')
    parser.add_argument('-c', '--config-file', default='default.yml')
    parser.add_argument('-p', '--pid-file', default='simplekeys.pid')
    args = parser.parse_args()

    program = Application()
    shutdown_handler = functools.partial(on_shutdown, program)
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    program.load(args.config_file)
    if args.daemonize:
        # FIXME: this doesn't work but fails silently! Gtk issues?
        # if using file logging, pass in keep_fds option
        daemon = Daemonize(app='simplekeys', pid=args.pid_file, action=program.run)
        daemon.start()
    else:
        program.run()


if __name__ == '__main__':
    main()
