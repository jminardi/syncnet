import os

import enaml
from enaml.qt.qt_application import QtApplication
from PyQt4.QtCore import QFileSystemWatcher, QUrl
from atom.api import Atom, Unicode, observe, Typed, Property

from btsync import BTSync

# Directory where all synced sites will be stored. Each site will be synced to
# a directory whose name is the secret.
STORAGE_PATH = u'/Users/jack/Desktop/synced_secrets'


class SyncNet(Atom):

    # The text currently entered in the secret field.
    entered_secret = Unicode()

    # A list of all locally synced secrets.
    known_secrets = Property()

    # Instance of the BTSync API wrapper.
    btsync = Typed(BTSync, ())

    # The QUrl object referencing the currently displayed resource. It must be
    # replaced wholesale for the UI to react.
    # FIXME remove this QT dependency.
    html_path = Typed(QUrl, ())

    # Root path where all synced site directoryies are added.
    storage_path = Unicode(STORAGE_PATH)

    # The filesystem watcher that monitors all currently synced site
    # directories.
    _watcher = Typed(QFileSystemWatcher)

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
        if not self.is_valid_secret(secret):
            msg = 'Attempted to load invalid secret: {}'.format(secret)
            raise RuntimeError(msg)

        if secret not in self.known_secrets:
            self.init_secret(secret)

        path = os.path.join(self.storage_path, secret)
        path = os.path.join(path, 'index.html')
        self.html_path = QUrl(path)

    def is_valid_secret(self, secret):
        """ True if the given `secret` is a valid btsync secret string.
        """
        return 'error' not in self.btsync.get_secrets(secret)

    ### Observers  ############################################################

    @observe('entered_secret')
    def _secret_changed(self, change):
        """ Load the entered secret into the HTML View if it is valid.
        """
        secret = self.entered_secret.upper()
        if self.is_valid_secret(secret):
            self.load_secret(secret)

    def on_directory_changed(self, dirname):
        """ Slot connected to the `QFileSystemWatcher.directoryChanged` Signal.
        """
        # If the directory containing the currently loaded secret changes, it
        # is reloaded.
        _, secret = os.path.split(os.path.normpath(dirname))
        if secret == self.entered_secret:
            self.load_secret(secret)

    def on_link_clicked(self, link):
        """ Slot connected to the `QWebView.linkClicked` Signal.
        """
        print link.toString()
        if link.scheme() == 'sync':
            secret = link.host().upper()
            if self.is_valid_secret(secret):
                self.load_secret(secret)
            else:
                print 'failed to load: {}'.format(link.toString())
        else:
            self.html_path = link

    ### Default methods  ######################################################

    def _default__watcher(self):
        _watcher = QFileSystemWatcher()
        _watcher.directoryChanged.connect(self.on_directory_changed)
        return _watcher

    ### Property getters  #####################################################

    def _get_known_secrets(self):
        """ List of all locally synced secrets. Getter for known_secrets.
        """
        return os.listdir(self.storage_path)


if __name__ == '__main__':
    with enaml.imports():
        from sync_net_view import SyncNetView
    syncnet = SyncNet()
    app = QtApplication()
    view = SyncNetView(model=syncnet)
    view.show()
    app.start()
