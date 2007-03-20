###
# Setup localization
###

import wx
_ = wx.GetTranslation

###
# AppSnap strings
###

ALL = _('All')
APPLICATION = _('Application')
AVAILABLE_CATEGORIES = _('Available Categories')

##

CATEGORY = _('Category')
COMMANDLINE_HELP = _("""
Global functions
-h             This help screen
-c             List all application categories
-l             List supported applications
   -f <cat>    Filter list by category
   -s <string> Filter list by string
-U             Update database

Application specific functions
-n <name>      One or more application names, comma separated or * to specify filter
   -f <cat>    Filter applications by category
   -s <string> Filter applications by string

   -d          Download application
      -t       Test download only
   -g          Get latest version       (DEFAULT)
   -i          Install latest version   (implies -d)
   -u          Upgrade current version  (implies -i, -x if not upgradeable)
   -x          Uninstall current version
""")
COMPARING = _('Comparing')

##

DESCRIPTION = _('Description')
DONE = _('Done')
DOWNLOAD = _('Download')
DOWNLOADED = _('Downloaded')
DOWNLOADING = _('Downloading')
DOWNLOAD_DESCRIPTION = _('Download selected applications')
DOWNLOAD_FAILED = _('Download failed')
DOWNLOAD_SUCCEEDED = _('Download succeeded')

##

ERROR = _('Error')

##

FAILED_CREATE_CACHE_DIR = _('Failed to create cache location')
FAILED_TO_CONNECT = _('failed to connect')
FILTER = _('Filter')

##

INSTALL = _('Install')
INSTALLED = _('Installed')
INSTALLED_APPLICATIONS = _('Installed Applications')
INSTALLED_INI_UPDATE_FAILED = _('Failed to update installed.ini. Is it writable?')
INSTALLED_VERSION = _('Installed Version')
INSTALLING = _('Installing')
INSTALL_DESCRIPTION = _('Download and install selected applications')
INSTALL_FAILED = _('Install failed')
INSTALL_SUCCEEDED = _('Install succeeded')

##

KEY = _('Key')

##

LATEST_INI_UPDATE_FAILED = _('Failed to update latest.ini. Is it writable?')
LATEST_VERSION = _('Latest Version')
LOADING = _('Loading')

##

MISSING_SCRAPE_AND_DOWNLOAD = _("Neither 'scrape' nor 'download' specified")
MISSING_SECTION_KEY = _('Missing section key in db.ini')
MISSING_VERSION_WHEN_SCRAPE = _("Missing key 'version' when 'scrape' specified")

##

NO_CHANGES_FOUND = _('No changes found.')
NO_SUCH_APPLICATION = _('No such application')

##

PROXY_AUTHENTICATION_FAILED = _('Proxy authentication failed. Check config.ini')

##

RELOAD = _('Reload')
RELOADING_DATABASE = _('Reloading database')
RELOAD_DESCRIPTION = _('Reload configuration')
REPORT_BUG = _('Report Bug')
REPORT_BUG_DESCRIPTION = _('Report a bug')

##

SECTION = _('Section')
STARTING = _('Starting')
STATUS = _('Status')
SUPPORTED_APPLICATIONS = _('Supported Applications')

##

TESTING = _('Testing')

##

UNABLE_TO_WRITE_DB_INI = _('Unable to write to db.ini')
UNINSTALL = _('Uninstall')
UNINSTALLING = _('Uninstalling')
UNINSTALL_DESCRIPTION = _('Uninstall selected applications')
UNINSTALL_FAILED = _('Uninstall failed')
UNINSTALL_SUCCEEDED = _('Uninstall succeeded')
UPDATE_DATABASE_FAILED = _('Update database failed')
UPDATE_DATABASE_SUCCEEDED = _('Update database succeeded')
UPDATE_DB = _('Update DB')
UPDATE_DB_DESCRIPTION = _('Update application database')
UPDATING_DATABASE = _('Updating database')
UPDATING_LOCAL_DATABASE = _('Updating local database')
UPGRADE = _('Upgrade')
UPGRADEABLE = _('Upgradeable')
UPGRADE_DESCRIPTION = _('Upgrade selected applications')
UPGRADE_FAILED = _('Upgrade failed')
UPGRADE_SUCCEEDED = _('Upgrade succeeded')
UPGRADING = _('Upgrading')

##

WAITING = _('Waiting')
WEBSITE = _('Website')

###
# Build strings
###

BUILD_COMMANDLINE_HELP = _("""
Usage:
  build.py [OPTIONS]
  -p    Build executable using Py2Exe
  -r    Rezip shared library using 7-Zip
  -u    Compress executables using UPX
  -z    Create ZIP package
  -n    Create NSIS package""")
BUILD_FAILED = _('Build failed.')

##

NSIS_NOT_AVAILABLE = _('NSIS not available')

##

SEVENZIP_NOT_AVAILABLE = _('7-Zip not available')

##

UPX_NOT_AVAILABLE = _('UPX not available')