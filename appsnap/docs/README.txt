What is AppSnap
---------------

AppSnap is an application that simplifies installation of software. It
automatically figures out the latest version, downloads the installer and
then installs the software in one seamless step.

AppSnap is primarily designed for Windows which does not have any decent
package manager such as APT and RPM as in the Linux world.

AppSnap is written in Python and uses wxPython, PyCurl and PyYAML. It is 
packaged using Py2Exe, compressed with UPX and installed using NSIS.

Features
--------

- Detect latest version of supported applications
- Download, install, upgrade and uninstall
- Fully functional GUI and CLI supporting localization
- Manage installed and upgradeable applications
- Manage AppSnap updates from within itself
- Update growing application database from central repository
- Create single application repository to be used by AppSnap on an intranet
- Support proxy configurations
- Parallel downloads with progress information
- Filter applications by category and keywords
- Free and Open Source

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
- Location to download latest DB from

Proxy Support
-------------

AppSnap will automatically use the proxy settings configured for Internet
Explorer. If you are behind a proxy, configure the proxy user and password in
the AppSnap configuration file.

Protocol Support
----------------

AppSnap uses libcurl to perform the actual downloads. As a result, it inherits
libcurl's long list of supported protocols:

  FTP, FTPS, HTTP, HTTPS, SCP, SFTP, TFTP, TELNET, DICT, FILE and LDAP

AppSnap has been tested with the FTP, HTTP and FILE protocols. These protocols
can be used anywhere in the database as well as in the configuration file.

Examples:

  FTP:  ftp://ftp.example.com/path/to/file
  HTTP: http://www.example.com/path/to/file
  FILE: file:\\localhost\d$\path\to\file, file:\\servername\sharename\path\to\file

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
-U             Update database

Application specific functions
-n <name>      One or more application names, comma separated
   -d          Download application
   -g          Get latest version       (DEFAULT)
   -i          Install latest version   (implies -d)
   -u          Upgrade current version  (implies -i, -x if not upgradeable)
   -x          Uninstall current version

Database
--------

The AppSnap application database is a simple INI file that contains all the
information that AppSnap needs in order to download, install and uninstall
the applications that are supported.

More details about adding new entries to the database can be found in DB.txt.

Uninstallation
--------------

AppSnap can be uninstalled from "Add or Remove Programs" in the Control Panel.

Source Package
--------------

AppSnap is also available in a source only package which can be executed
directly using an existing installation of Python. The following extra Python
packages will need to be installed prior to running AppSnap:

- wxPython
- PyCurl
- PyYAML

Just download the source ZIP file, extract to a directory of your choice and run
appsnap.py for the command line or appsnapgui.py for the GUI.

Source from SVN
---------------

The AppSnap source can be downloaded directly from SVN using an SVN client. The
latest code can be obtained from the following URL:-

  http://appsnap.googlecode.com/svn/trunk/appsnap

Source of previously released versions of AppSnap are also tagged and can be
downloaded from the following URL:-

  http://appsnap.googlecode.com/svn/tags/
  
For example, version 1.2.1 can be downloaded from:-

  http://appsnap.googlecode.com/svn/tags/appsnap-1.2.1/

For more information, refer to http://code.google.com/p/appsnap/source.

Building AppSnap
----------------

The AppSnap executable and installer can be built from the source package using
build.py. The build script requires the following applications and Python modules
installed prior to execution:

- Python
  - wxPython
  - PyCurl
  - PyYAML
  - Py2Exe
- 7-Zip
- NSIS
- UPX (upx.exe present in the Windows directory)

License
-------

AppSnap is being released under the GPL. The source code is included in the
installer.

Contact
-------

Contact ganeshjgd AT gmail DOT com for any questions regarding this program.

Links
-----

AppSnap website
http://blog.genotrance.com/applications/appsnap

Discussion Forum
http://groups.google.com/group/appsnap

Issue Tracker
http://code.google.com/p/appsnap/issues/list

SVN Repository
http://code.google.com/p/appsnap/source

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

7-Zip
http://www.7-zip.org/

UPX
http://upx.sourceforge.net/