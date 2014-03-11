import os
import threading
import SimpleHTTPServer
import SocketServer

import enaml
from enaml.qt.qt_application import QtApplication
from PyQt4.QtCore import QFileSystemWatcher
from atom.api import Atom, Unicode, observe, Typed, Property, Int

from btsync import BTSync

import logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# Directory where all synced sites will be stored. Each site will be synced to
# a directory whose name is the secret.
STORAGE_PATH = os.path.expanduser(u'~/Documents/SyncNet/synced_secrets')


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
    url = Unicode()

    # Root path where all synced site directoryies are added.
    storage_path = Unicode()

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
        logger.debug('Directory added to BTSync: {}'.format(path))

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

        # Store the currently loaded secret so its directory can be monitored.
        self.current_secret = secret

        # Ensure the HTTP server is running before the url is set.
        if self._server_thread is None:
            logger.debug('Creating server thread')
            self._server_thread = self._create_server_thread()

        url = 'http://localhost:{}/{}'.format(self.http_port, secret)
        self.url = ''  # FIXME hack to get the webview to reload
        self.url = url
        logger.debug('URL set to: {}'.format(url))

    def is_valid_secret(self, secret):
        """ True if the given `secret` is a valid btsync secret string. A
        valid secret is a 160 bit base32 encoded string with an 'A' or 'B'
        prepended.

        """
        if not (secret.startswith('A') or secret.startswith('B')):
            return False
        if len(secret) != 33:
            return False
        if not secret.isupper():
            return False
        # ensure only legal chars as defined by RFC 4648
        for char in ('1', '8', '9', '='):
            if char in secret:
                return False
        return True

    ### Observers  ############################################################

    @observe('address')
    def _address_changed(self, change):
        """ Check the text entered into the address field to see if it contains
        a valid secret. If so, attempt to load that secret.

        """
        address = self.address.upper()
        if self.is_valid_secret(address):
            self.load_secret(address)

    def on_directory_changed(self, dirname):
        """ Slot connected to the `QFileSystemWatcher.directoryChanged` Signal.
        """
        # If the directory containing the currently loaded secret changes, it
        # is reloaded.
        _, secret = os.path.split(os.path.normpath(dirname))
        if secret == self.current_secret:
            self.load_secret(secret)

    def on_link_clicked(self, url):
        """ Slot connected to the `QWebView.linkClicked` Signal.
        """
        self._update_address_bar(url)

        if url.scheme() == 'sync':
            secret = url.host().upper()
            if self.is_valid_secret(secret):
                self.load_secret(secret)
            else:
                msg = 'Attempted to load invalid secret: {}'
                logger.debug(msg.format(url.toString()))
        else:
            self.url = url.toString()

    def on_url_changed(self, url):
        """ Slot connected to the `QWebView.urlChanged` Signal.
        """
        self._update_address_bar(url)

    ### Default methods  ######################################################

    def _default__watcher(self):
        _watcher = QFileSystemWatcher()
        _watcher.directoryChanged.connect(self.on_directory_changed)
        return _watcher

    def _default_storage_path(self):
        storage_path = STORAGE_PATH
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
            logger.debug('Creating storage path: {}'.format(storage_path))
        return storage_path

    ### Property getters  #####################################################

    def _get_known_secrets(self):
        """ List of all locally synced secrets. Getter for known_secrets.
        """
        return os.listdir(self.storage_path)

    ### Private Interface  ####################################################

    def _create_server_thread(self):
        os.chdir(self.storage_path)
        handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = SocketServer.TCPServer(('localhost', 0), handler)
        _, port = httpd.server_address
        self.http_port = port
        logger.debug('Serving on port #{}'.format(port))

        t = threading.Thread(target=httpd.serve_forever)
        t.daemon = True  # don't hang on exit
        t.start()
        return t

    def _update_address_bar(self, url):
        """
        Parameters
        ----------
        url : QUrl
            The currently displayed url

        """
        if url.host() == 'localhost':
            self.address = url.path()[1:]
        elif url.scheme() == 'sync':
            self.address = url.host().upper()
        else:
            self.address = url.toString()


if __name__ == '__main__':
    with enaml.imports():
        from syncnet_view import SyncNetView
    syncnet = SyncNet()
    syncnet.btsync.start()
    app = QtApplication()
    view = SyncNetView(model=syncnet)
    view.show()
    app.start()
