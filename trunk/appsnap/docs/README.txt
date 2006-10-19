What is AppSnap
---------------

AppSnap is an application that simplifies installation of software. It
automatically figures out the latest version, downloads the installer and
then installs the software in one seamless step.

AppSnap is primarily designed for Windows which does not have any decent
package manager such as APT and RPM as in the Linux world.

AppSnap is written in Python and uses wxPython, PyCurl and PyYAML. It is
packaged using Py2Exe and installed using NSIS.

Installation
------------

The installer copies the executable files, source code and the README to a
directory of your choice. It then creates a shortcut in the Start Menu.

Configuration
-------------

AppSnap has a few configurable options that are stored in config.ini in the
installation directory and can be modified as needed. The options are:-

- Default directory to install applications (if possible)
- Login for the proxy user
- Password for the proxy user
- Location where downloaded installation files should be cached

Proxy Support
-------------

AppSnap will automatically use the proxy settings configured for Internet
Explorer. If you are behind a proxy, configure the proxy user and password in
the AppSnap configuration file.

Usage
-----

AppSnap has a simple GUI which simplifies the install process. It can also
be used on the command line and in scripts.

The command line usage is as follows:-

Global functions
-h             This help screen
-c             List all application categories
-l             List supported applications
   -f <cat>    Filter list by category

Application specific functions
-n <name>      One or more application names, comma separated
   -d          Download application
   -g          Get latest version       (DEFAULT)
   -i          Install latest version   (implies -d)
   -u          Upgrade current version  (implies -i, -x if not upgradeable)
   -x          Uninstall current version

Uninstallation
--------------

AppSnap can be uninstalled from "Add or Remove Programs" in the Control Panel.

License
-------

AppSnap is being released under the GPL. The source code is included in the
installer.

Contact
-------

Contact genosha@genotrance.com for any questions regarding this program.

Links
-----

AppSnap website
http://www.genotrance.com/applications/appsnap

Python
http://www.python.org

wxPython
http://www.wxpython.org

PyCurl
http://pycurl.sourceforge.net/

PyYAML
http://pyyaml.org/

Py2Exe
http://www.py2exe.org

NSIS
http://nsis.sf.net