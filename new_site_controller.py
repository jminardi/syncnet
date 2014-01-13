import base64
import hashlib
import os
import subprocess

from atom.api import Atom, Unicode, Typed, observe


class NewSiteController(Atom):

    seed = Unicode()

    secret = Unicode()

    ro_secret = Unicode()

    syncnet = Typed(object)

    def on_ok_clicked(self):
        syncnet = self.syncnet
        syncnet.load_secret(self.secret)
        new_path = os.path.join(syncnet.storage_path, syncnet.current_secret)
        subprocess.call(["open", new_path])

    @observe('seed')
    def _seed_changed(self, changed):
        seed = self.seed
        if seed:
            self.secret = 'A' + base64.b32encode(hashlib.sha1(seed).digest())
        else:
            self.secret = ''

    @observe('secret')
    def _secret_changed(self, changed):
        secret = self.secret
        if secret:
            secrets = self.syncnet.btsync.get_secrets(secret)
            if 'read_only' in secrets:
                self.ro_secret = secrets['read_only']
            else:
                self.seed = ''
                self.ro_secret = ''
        else:
            self.seed = ''
            self.ro_secret = ''
