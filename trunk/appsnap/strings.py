###
# Setup localization
###

import wx
app = wx.App(False)
locale = wx.Locale(wx.LANGUAGE_DEFAULT)
locale.AddCatalogLookupPathPrefix("locale")
locale.AddCatalog("appsnap")
_ = wx.GetTranslation

###
# AppSnap strings
###

ALL = _('All')
APPLICATION = _('Application')
APPLICATION_NAME_DESCRIPTION = _('Application names, comma separated or * to filter')
APPLICATION_SPECIFIC_FUNCTIONS = _('Application specific functions')
AVAILABLE_CATEGORIES = _('Available Categories')

##

CATEGORY = _('Category')
COMPARING = _('Comparing')

##

DEFAULT = _('Default')
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
FAILED_TO_CONNECT = _('Failed to connect')
FILTER = _('Filter')
FILTER_APP_BY_CATEGORY = _('Filter applications by category')
FILTER_APP_BY_STRING = _('Filter applications by string')
FILTER_LIST_BY_CATEGORY = _('Filter list by category')
FILTER_LIST_BY_STRING = _('Filter list by string')

##

GET_LATEST_VERSION = _('Get latest version')
GLOBAL_FUNCTIONS = _('Global functions')

##

INSTALL = _('Install')
INSTALLED = _('Installed')
INSTALLED_APPLICATIONS = _('Installed Applications')
INSTALLED_INI_UPDATE_FAILED = _('Failed to update installed.ini. Is it writable?')
INSTALLED_VERSION = _('Installed Version')
INSTALLING = _('Installing')
INSTALL_DESCRIPTION = _('Download and install selected applications')
INSTALL_FAILED = _('Install failed')
INSTALL_IMPLICATION = _('implies -d')
INSTALL_SUCCEEDED = _('Install succeeded')

##

KEY = _('Key')

##

LATEST_INI_UPDATE_FAILED = _('Failed to update latest.ini. Is it writable?')
LATEST_VERSION = _('Latest Version')
LIST_ALL_APPLICATION_CATEGORIES = _('List all application categories')
LIST_SUPPORTED_APPLICATIONS = _('List supported applications')
LOADING = _('Loading')

##

MISSING_SCRAPE_AND_DOWNLOAD = _("Neither 'scrape' nor 'download' specified")
MISSING_SECTION_KEY = _('Missing section key in db.ini')
MISSING_VERSION_WHEN_SCRAPE = _("Missing key 'version' when 'scrape' specified")

##

NAME = _('Name')
NO_CHANGES_FOUND = _('No changes found')
NO_SUCH_APPLICATION = _('No such application')
NOT_AVAILABLE = _('Not available')

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
STRING = _('String')
SUPPORTED_APPLICATIONS = _('Supported Applications')

##

TEST_DOWNLOAD_ONLY = _('Test download only')
TESTING = _('Testing')
THIS_HELP_SCREEN = _('This help screen')

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
UPDATE_IMPLICATION = _('implies -i, -x if not upgradeable')
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

BUILD_EXECUTABLE_USING_PY2EXE = _('Build executable using Py2Exe')
BUILD_FAILED = _('Build failed.')

##

COMPRESS_USING_UPX = _('Compress executables using UPX')
CREATE_NSIS_PACKAGE = _('Create NSIS package')
CREATE_ZIP_PACKAGE = _('Create ZIP package')

##

NSIS_NOT_AVAILABLE = _('NSIS not available')

##

OPTIONS = _('OPTIONS')

##

REZIP_USING_SEVENZIP = _('Rezip shared library using 7-Zip')

##

SEVENZIP_NOT_AVAILABLE = _('7-Zip not available')

##

UPX_NOT_AVAILABLE = _('UPX not available')
USAGE = _('Usage')