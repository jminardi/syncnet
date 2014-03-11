SyncNet
=======

SyncNet is a decentralized browser built on top of BitTorrent Sync and (soon) Colored Coins.

You can find more detail on my [website](http://jack.minardi.org/software/syncnet-a-decentralized-web-browser/).

SyncNet is experimental, no security auditing has been done. Only use it if you know what you are doing.

Requirements
------------
* [enaml](https://github.com/nucleic/enaml) - enaml is used as the UI framework
  + You can find installation instructions [here](http://nucleic.github.io/enaml/docs/get_started/installation.html).
    If you have a working C++ compilier it is as simple as `pip install enaml`, if not you will have to install the
    various requirements from their project pages. Qt is the recommended backend. OS X users can install `PyQt4` with
    homebrew. Windows users can find binaries on the pyqt project page. Linux users know how to install things.

* [atom](https://github.com/nucleic/atom) - atom is used as the eventing framework
  + This is a dependency of `enaml`, so if you successfully installed `enaml` you should be good to go.

* [python-btsync](https://github.com/jminardi/python-btsync) - a lightweight wrapper around the BTSync API
  + `python-btsync` is a light weight wrapper I wrote around the btsync API. To use it you will have to apply
     for and receive an API key from BitTorrent. Once you have that key you will need to enter it into the
     config.json file and point btsync to that file when starting up. You can find more details on the linked
     github project page.

Future Work
-----------
* Build a DNS system using colored coins.
* Selectivly sync only the content requested.
* Convert any regular HTTP site into a syncnet site.

Logo from wikipedia: http://commons.wikimedia.org/wiki/File:Social_Network_Analysis_Visualization.png
