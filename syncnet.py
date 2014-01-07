import os
import threading
import SimpleHTTPServer
import SocketServer

import enaml
from enaml.qt.qt_application import QtApplication
from PyQt4.QtCore import QFileSystemWatcher
from atom.api import Atom, Unicode, observe, Typed, Property, Int

from btsync import BTSync

# Directory where all synced sites will be stored. Each site will be synced to
# a directory whose name is the secret.
STORAGE_PATH = u'/Users/jack/Desktop/synced_secrets'


class SyncNet(Atom):

    # The text currently entered in the secret field.
    address = Unicode()

    # The currently loaded secret.
    current_secret = Unicode()

    # A list of all locally synced secrets.
    known_secrets = Property()

    # Instance of the BTSync API wrapper.
    btsync = Typed(BTSync, ())

    # The QUrl object referencing the currently displayed resource. It must be
    # replaced wholesale for the UI to react.
    html_path = Unicode()

    # Root path where all synced site directoryies are added.
    storage_path = Unicode(STORAGE_PATH)

    # The filesystem watcher that monitors all currently synced site
    # directories.
    _watcher = Typed(QFileSystemWatcher)

    # This thread runs the simple http server.
    _server_thread = Typed(threading.Thread)

    # The simple http server's port
    http_port = Int()

    ### Public Interface  #####################################################

    def init_secret(self, secret):
        """ Creates a new directry at `self.storage_path` and adds it to the
        BTSync object to be synced with the given `secret`. The secret is
        assumed valid.

        Parameters
        ----------
        secret : str
            BTSync secret string referencing a directory of html files. This
            secret is assumed to already exist on the network.

        Notes
        -----
        The newly created folder's name will be the given `secret`.

        """
        path = os.path.join(self.storage_path, secret)
        os.mkdir(path)
        self._watcher.addPath(path)
        self.btsync.add_folder(path, secret)

    def load_secret(self, secret):
        """ Display the HTML files referenced by the given secret in the View.
        If the secret is not synced locally, it will be initialized and synced.

        Parameters
        ----------
        secret : str
            BTSync secret string

        Raises
        ------
        RuntimeError if `secret` is invalid

        """
        secret = secret.upper()
        if not self.is_valid_secret(secret):
            msg = 'Attempted to load invalid secret: {}'.format(secret)
            raise RuntimeError(msg)

        if secret not in self.known_secrets:
            self.init_secret(secret)

        self.current_secret = secret

        print '>>', self._server_thread
        url = 'http://localhost:{}/{}'.format(self.http_port, secret)
        print 'inside load_secret, url is:', url
        #self.html_path = QUrl('')
        self.html_path = url

    def is_valid_secret(self, secret):
        """ True if the given `secret` is a valid btsync secret string.
        """
        if '/' in secret:
            return False
        return 'error' not in self.btsync.get_secrets(secret)

    ### Observers  ############################################################

    @observe('address')
    def _secret_changed(self, change):
        """ Load the entered secret into the HTML View if it is valid.
        """
        secret = self.address
        if self.is_valid_secret(secret):
            self.load_secret(secret)

    def on_directory_changed(self, dirname):
        """ Slot connected to the `QFileSystemWatcher.directoryChanged` Signal.
        """
        # If the directory containing the currently loaded secret changes, it
        # is reloaded.
        _, secret = os.path.split(os.path.normpath(dirname))
        if secret == self.current_secret:
            self.load_secret(secret)

    def on_link_clicked(self, link):
        """ Slot connected to the `QWebView.linkClicked` Signal.
        """
        print 'inside on_link_clicked:', link.toString()
        if link.host() == 'localhost':
            self.address = link.path()[1:]
        elif link.scheme == 'sync':
            self.address = link.host().upper()
        else:
            self.address = link.toString()

        if link.scheme() == 'sync':
            secret = link.host().upper()
            if self.is_valid_secret(secret):
                self.load_secret(secret)
            else:
                print 'failed to load: {}'.format(link.toString())
        else:
            self.html_path = link.toString()

    ### Default methods  ######################################################

    def _default__watcher(self):
        _watcher = QFileSystemWatcher()
        _watcher.directoryChanged.connect(self.on_directory_changed)
        return _watcher

    def _default__server_thread(self):
        os.chdir(self.storage_path)
        handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(('localhost', 0), handler)
        _, port = httpd.server_address
        self.http_port = port

        t = threading.Thread(target=httpd.serve_forever)
        t.setDaemon(True)  # don't hang on exit
        t.start()
        return t

    ### Property getters  #####################################################

    def _get_known_secrets(self):
        """ List of all locally synced secrets. Getter for known_secrets.
        """
        return os.listdir(self.storage_path)


if __name__ == '__main__':
    with enaml.imports():
        from syncnet_view import SyncNetView
    syncnet = SyncNet()
    app = QtApplication()
    view = SyncNetView(model=syncnet)
    view.show()
    app.start()
