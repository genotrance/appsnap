# Import required libraries
import config
import defines
import glob
import os
import os.path
import re
import string
import strings
import StringIO
import sys
import time
import types
import zipfile

# Windows only
try:
    import _winreg
except ImportError:
    pass

# Shortcut to convert versions with letters in them
ALPHABET = 'a b c d e f g h i j k l m n o p q r s t u v w x y z'.split(' ')

# Regular expressions
DELIMITERS                 = '[._-]'
VERSION                    = '#VERSION#'
VERSION_SEARCH             = '#VERSION\[([0-9]*[:]?[0-9]*)\]#'
VERSION_REPLACE            = '#VERSION[%s]#'
REPLACE_SEARCH             = '#REPLACE\((.+?),(.*?),(.+?)\)#'
REPLACE_REPLACE            = '#REPLACE(%s,%s,%s)#'
MAJOR_VERSION              = '#MAJOR_VERSION#'
MINOR_VERSION              = '#MINOR_VERSION#'
SUB_VERSION                = '#SUB_VERSION#'
MAJORMINOR_VERSION         = '#MAJORMINOR_VERSION#'
MAJORMINORSUB_VERSION      = '#MAJORMINORSUB_VERSION#'
DOTLESS_VERSION            = '#DOTLESS_VERSION#'
DASHTODOT_VERSION          = '#DASHTODOT_VERSION#'
DOTTOUNDERSCORE_VERSION    = '#DOTTOUNDERSCORE_VERSION#'
DOTTODASH_VERSION          = '#DOTTODASH_VERSION#'
INSTALL_DIR                = '#INSTALL_DIR#'

# DB.ini entries
APP_CATEGORY      = 'category'
APP_DESCRIBE      = 'describe'
APP_WEBSITE       = 'website'
APP_SCRAPE        = 'scrape'
APP_VERSION       = 'version'
APP_DOWNLOAD      = 'download'
APP_FILENAME      = 'filename'
APP_RENAME        = 'rename'
APP_REFERER       = 'referer'
APP_INSTALLER     = 'installer'
APP_INSTPARAM     = 'instparam'
APP_UPGRADES      = 'upgrades'
APP_CHINSTDIR     = 'chinstdir'
APP_UNINSTALL     = 'uninstall'
APP_UNINSTPARAM   = 'uninstparam'
APP_PREINSTALL    = 'preinstall'
APP_POSTINSTALL   = 'postinstall'
APP_PREUNINSTALL  = 'preuninstall'
APP_POSTUNINSTALL = 'postuninstall'
APP_INSTVERSION   = 'instversion'
APP_INSTDIR       = 'instdir'

# Actions
ACT_DOWNLOAD      = 'download'
ACT_INSTALL       = 'install'
ACT_UNINSTALL     = 'uninstall'
ACT_UPGRADE       = 'upgrade'

# Meta commands
REGISTRY_SEARCH   = 'REGISTRY_SEARCH'
USE_UNINSTALL     = 'USE_UNINSTALL'

# Version cache
cached_versions = {}

# Class to do all the backend work
class process:
    # Constructor
    def __init__(self, global_config, curl_instance, app, app_config):
        # Store the application's configuration
        self.global_config = global_config
        self.curl_instance = curl_instance
        self.app = app
        self.app_config = app_config
        self.init = False
        self.latestversion = None
        self.installedversion = ''
        self.installdir = ''
        self.uninstall_key = ''
        self.uninstall_matchobj = None
        self.versions = None
        self.splitversions = None
        self.width = 0

        self.get_installed_version()

    # ***
    # External functions

    # Get the latest version
    def get_latest_version(self, force=False):
        if self.init == False or force==True:
            self.init = True
            # Get version only if scrape specified
            if APP_SCRAPE in self.app_config and APP_VERSION in self.app_config:
                self.latestversion = self.global_config.get_cached_latest_version(self.app)
                if self.latestversion == None or force==True:
                    for i in range(defines.NUM_MAX_DOWNLOAD_RETRIES):
                        self.versions = self.get_versions()
                        if self.versions != None or i == defines.NUM_MAX_DOWNLOAD_RETRIES-1: break
                        time.sleep(defines.SLEEP_BACKEND_DOWNLOAD_RETRY)

                    self.splitversions = self.get_split_versions()
                    self.width = self.get_width()
            else:
                self.latestversion = strings.NOT_AVAILABLE

        # No versioning or cached version available
        if self.latestversion != None: return self.latestversion

        # Filter latest
        if self.filter_latest_version() == False: return None

        version = ''
        for i in range(self.width):
            version += self.splitversions[0][i]
            if i < self.width-1: version += DELIMITERS

        for i in range(len(self.versions)):
            if re.match(version, self.versions[i]):
                self.latestversion = self.versions[i]
                self.global_config.save_cached_latest_version(self.app, self.latestversion)
                return self.versions[i]

        return None

    # Get the installed version of the application
    def get_installed_version(self):
        if self.installedversion != '': return self.installedversion

        if self.app_config.has_key(APP_INSTVERSION):
            if self.app_config[APP_INSTVERSION] == USE_UNINSTALL:
                uninstall_key, matchobj = self.parse_uninstall_entry()
                if uninstall_key != '' and matchobj != None and len(matchobj.groups()) and matchobj.groups()[0] != None:
                    self.installedversion = self.handle_multipart_versions([matchobj.groups()], APP_UNINSTALL)[0]
            else:
                command = self.app_config[APP_INSTVERSION].split(':')
                if len(command) == 2 and command[0] == REGISTRY_SEARCH:
                    uninstall_key, matchobj = self.parse_uninstall_entry()
                    if uninstall_key != '':
                        value = command[1].split('=')
                        if len(value) == 2:
                            matchobj = self.global_config.registry_search_uninstall_location(uninstall_key, value[0], value[1])
                        else:
                            matchobj = self.global_config.registry_search_uninstall_location(uninstall_key, value[0], '')
                        if matchobj != '':
                            self.installedversion = self.handle_multipart_versions([matchobj.groups()], APP_INSTVERSION)[0]
                        else:
                            self.installedversion = ''
        else:
            # Get installed version from file
            installed_version = self.global_config.get_installed_version(self.app)

            # Check if app is still installed
            if self.app_config.has_key(APP_UNINSTALL):
                app_uninstall, matchobj = self.parse_uninstall_entry()
                uninstall_string = self.get_uninstall_string(app_uninstall, installed_version)
                if uninstall_string == None:
                    self.installedversion = ''
                else:
                    if installed_version == '':
                        self.installedversion = strings.NOT_AVAILABLE
                    else:
                        self.installedversion = installed_version
            else:
                filename = self.get_filename_or_rename()
                if filename[-3:] == 'zip':
                    try:
                        # ZIP file with installer
                        test = self.app_config[APP_INSTALLER]
                    except KeyError:
                        # ZIP file without installer
                        self.installedversion = installed_version

        if self.app_config[APP_CATEGORY] != config.REMOVABLE:
            if self.installedversion != '': self.global_config.add_installed_version(self.app, self.installedversion)
            else: self.global_config.delete_installed_version(self.app)

        return self.installedversion

    # Get the install directory of the application
    def get_install_dir(self):
        if self.installdir != '': return self.installdir

        if self.app_config.has_key(APP_INSTDIR):
            command = self.app_config[APP_INSTDIR].split(':')
            if len(command) == 2 and command[0] == REGISTRY_SEARCH:
                uninstall_key, matchobj = self.parse_uninstall_entry()
                if uninstall_key != '':
                    value = command[1].split('=')
                    if len(value) == 2:
                        matchobj = self.global_config.registry_search_uninstall_location(uninstall_key, value[0], value[1])
                    else:
                        matchobj = self.global_config.registry_search_uninstall_location(uninstall_key, value[0], '')
                    if matchobj != '':
                        self.installdir = matchobj.groups()[0]
                    else:
                        self.installdir = ''

        return self.installdir

    # Download the latest version of the application's installer
    def download_latest_version(self, progress_callback=None, test=False):
        # Get latest version if not already done
        if self.latestversion == None: self.get_latest_version()

        # If still not available, return false
        if self.latestversion == None: return False

        # Get download URL, default to scrape
        try: download = self.replace_version(self.app_config[APP_DOWNLOAD])
        except KeyError:
            try: download = self.app_config[APP_SCRAPE]
            except KeyError:
                return False

        # Get filename
        filename = self.replace_version(self.app_config[APP_FILENAME])
        try: rename_orig = self.app_config[APP_RENAME]
        except KeyError: rename_orig = ''
        rename = self.replace_version(rename_orig)

        # Get referer
        try: referer = self.replace_version(self.app_config[APP_REFERER])
        except KeyError:
            try: referer = self.app_config[APP_SCRAPE]
            except KeyError: referer = self.app_config[APP_DOWNLOAD]

        # Get cached location to save file to
        cached_filename = self.curl_instance.get_cached_name(filename, rename)

        # Download file depending on conditions below
        cache_timeout = int(self.global_config.cache['cache_timeout']) * defines.NUM_SECONDS_IN_DAY
        perform_download = False
        if not os.path.exists(cached_filename) or test == True:
            # File not downloaded yet or test mode
            perform_download = True
        else:
            # File already exists
            if time.time() - os.stat(cached_filename).st_ctime > cache_timeout:
                # Timeout expired
                if rename == '':
                    # No renaming specified, check filename
                    if filename == self.app_config[APP_FILENAME]:
                        # No version information in filename
                        perform_download = True
                else:
                    # Renaming specified, check rename instead
                    if rename == rename_orig:
                        # No version information in rename
                        perform_download = True

        if perform_download == True:
            # Delete any older cached versions
            if test == False: self.delete_older_versions()

            # Return false if download fails
            for i in range(defines.NUM_MAX_DOWNLOAD_RETRIES):
                if self.curl_instance.download_web_data(download + filename, cached_filename, referer, progress_callback, test) == True: break
                if i == defines.NUM_MAX_DOWNLOAD_RETRIES-1: return False
                time.sleep(defines.SLEEP_BACKEND_DOWNLOAD_RETRY)

        return cached_filename

    # Delete older application installers
    def delete_older_versions(self):
        filename = self.replace_version_with_mask(self.app_config[APP_FILENAME])
        try: rename = self.replace_version_with_mask(self.app_config[APP_RENAME])
        except KeyError: rename = ''
        filename = self.curl_instance.get_cached_name(filename, rename)

        # Find all older versions
        older_files = glob.glob(filename)
        for older_file in older_files:
            try: os.remove(older_file)
            except WindowsError: pass
            if older_file[-3:] == 'zip':
                self.delete_tree(older_file[:-4])

    # Install the latest version of the application
    def install_latest_version(self, progress_callback=None):
        # Download the latest version if required
        cached_filename = self.download_latest_version(progress_callback)
        if cached_filename == False: return False

        # Execute pre-install command if any
        if self.execute_script(APP_PREINSTALL) != True:
            return False

        # Create the command to execute
        installer = True
        if cached_filename[-3:] == 'msi':
            command = 'msiexec /i "' + cached_filename + '"'
        elif cached_filename[-3:] == 'zip':
            self.unzip_file(cached_filename)
            try: command = '"' + os.path.join(cached_filename[:-4], self.replace_version(self.app_config[APP_INSTALLER])) + '"'
            except KeyError:
                # ZIP file with no embedded installer
                installer = False
        elif cached_filename[-3:] == 'xpi':
            # Identify the app
            if self.app_config[APP_CATEGORY][:len(strings.FIREFOX)] == strings.FIREFOX:
                name = 'Firefox'
            elif self.app_config[APP_CATEGORY][:len(strings.THUNDERBIRD)] == strings.THUNDERBIRD:
                name = 'Thunderbird'
            else:
                return False

            # Create a process for that app
            items = self.global_config.get_section_items(name)
            app = process(self.global_config, self.curl_instance, name, items)

            # Check if app is installed
            version = app.get_installed_version()
            app_dir = app.get_install_dir()
            if version == '' or app_dir == '':
                return False

            command = string.join(['"' + os.path.join(app_dir, name + '.exe') + '"', '-install-global-extension', '"' + cached_filename + '"'])
        else:
            command = '"' + cached_filename + '"'

        # If installer command to be executed
        if installer == True:
            # Add instparam flags if available and if silent install requested
            if self.global_config.user[config.SILENT_INSTALL] == 'True':
                try:
                    command += ' ' + self.replace_install_dir(self.app_config[APP_INSTPARAM])
                except KeyError:
                    pass

            # Add the install directory if available
            try:
                if self.app_config[APP_CHINSTDIR] != '':
                    command += ' ' + self.replace_install_dir(self.app_config[APP_CHINSTDIR])
            except KeyError:
                pass

            # Run the installer, check return value
            try: retval = os.popen('"' + command + '"').close()
            except IOError: retval = 2
            if  retval != None:
                # MSI returns non-zero as success too
                if cached_filename[-3:] == 'msi' and (retval == 1641 or retval == 3010): pass
                # Firefox returns 1
                elif cached_filename[-3:] == 'xpi' and retval == 1: pass
                else: return False
        else:
            directory = self.replace_install_dir(INSTALL_DIR)
            command = 'explorer "' + directory + '"'
            os.popen('"' + command + '"').close()

        # Save installed version
        self.global_config.save_installed_version(self.app, self.latestversion)
        self.installedversion = ''

        # Execute post-install command if any
        if self.execute_script(APP_POSTINSTALL) != True:
            return False

        # If cache_timeout = 0, delete installer
        try: cache_timeout = int(self.global_config.cache[config.CACHE_TIMEOUT])
        except: cache_timeout = defines.NUM_DEFAULT_CACHE_TIMEOUT
        if cache_timeout == 0:
            self.delete_older_versions()

        # Return
        return True

    # Uninstall the currently installed version of the application
    def uninstall_version(self):
        # Get installed version
        installed_version = self.get_installed_version()
        if installed_version == '':
            if self.latestversion == None: self.get_latest_version()
            installed_version = self.latestversion

        # Execute pre-uninstall command if any
        if self.execute_script(APP_PREUNINSTALL) != True:
            return False

        # Process uninstall string if required
        app_uninstall, matchobj = self.parse_uninstall_entry()

        try:
            # Get uninstall string from registry
            uninstall_string = self.get_uninstall_string(app_uninstall, installed_version)
            if uninstall_string == None: raise WindowsError

            # Delete NSIS uninstaller if necessary
            nsis_cleanup = False
            nsis_uninstaller = uninstall_string

            # Add uninstparam flags if available and if silent install requested
            uninstparam = ''
            if self.global_config.user[config.SILENT_INSTALL] == 'True':
                # Ensure MSIExec is executed with /x to automatically uninstall
                uninstall_string = re.sub(re.compile('msiexec.exe /i', re.IGNORECASE), 'msiexec.exe /x', uninstall_string)

                try:
                    uninstparam = ' ' + self.replace_install_dir(self.app_config[APP_UNINSTPARAM])

                    # Check if NSIS
                    if '_?=#INSTALL_DIR#' in self.app_config[APP_UNINSTPARAM]:
                        nsis_cleanup = True
                except KeyError:
                    pass

            # Fix uninstall string quotes
            if uninstall_string[0] != '"': uninstall_string = '"' + re.sub(re.compile('\.exe', re.IGNORECASE), '.exe"', uninstall_string)

            # Run uninstaller, check return value
            retval = os.popen('"' + uninstall_string + uninstparam + '"').close()
            if  retval != None:
                # MSI returns non-zero as success too
                if (retval == 1641 or retval == 3010): pass
                else: return False

            # Delete NSIS uninstaller
            if nsis_cleanup == True:
                try:
                    # Delete uninstaller and directory if not empty
                    nsis_uninstaller = nsis_uninstaller.replace('"', '')
                    os.remove(nsis_uninstaller)
                    os.rmdir(os.path.dirname(nsis_uninstaller))
                except: pass

            # Delete installed version
            self.global_config.delete_installed_version(self.app)
            self.installedversion = ''
        except (WindowsError, KeyError):
            filename = self.get_filename_or_rename()
            if filename[-3:] == 'zip':
                try:
                    # Installer didn't provide uninstall method
                    test = self.app_config[APP_INSTALLER]
                    return False
                except KeyError:
                    # ZIP file with no embedded installer
                    directory = self.replace_install_dir(INSTALL_DIR)
                    self.delete_tree(directory)

                    # Delete installed version
                    self.global_config.delete_installed_version(self.app)
                    self.installedversion = ''
            else:
                # No uninstall method available
                return False

        # Execute post-uninstall command if any
        if self.execute_script(APP_POSTUNINSTALL) != True:
            return False

        return True

    # Locate the uninstall entry for the application in the registry
    def parse_uninstall_entry(self):
        if self.uninstall_key != '':
            return self.uninstall_key, self.uninstall_matchobj

        if not self.app_config.has_key(APP_UNINSTALL):
            self.uninstall_key = ''
            self.uninstall_matchobj = None
        else:
            command = self.app_config[APP_UNINSTALL].split(':')
            if len(command) == 2 and command[0] == REGISTRY_SEARCH:
                value = command[1].split('=')
                if len(value) == 2:
                    self.uninstall_key, self.uninstall_matchobj = self.global_config.registry_search_uninstall_entry(value[0], value[1])
                else:
                    self.uninstall_key, self.uninstall_matchobj = self.global_config.registry_search_uninstall_entry(value[0], '')
            else:
                self.uninstall_key = self.app_config[APP_UNINSTALL]
                self.uninstall_matchobj = None

        return self.uninstall_key, self.uninstall_matchobj

    def get_uninstall_string(self, app_uninstall, installed_version):
        uninstall_string = None

        if sys.platform == 'win32':
            try:
                # Get uninstall string from registry - LOCAL_MACHINE
                uninstall = self.replace_version(app_uninstall, installed_version)
                key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + uninstall)
                uninstall_string, temp = _winreg.QueryValueEx(key, 'UninstallString')
                _winreg.CloseKey(key)
            except WindowsError:
                try:
                    # Get uninstall string from registry - CURRENT_USER
                    uninstall = self.replace_version(app_uninstall, installed_version)
                    key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + uninstall)
                    uninstall_string, temp = _winreg.QueryValueEx(key, 'UninstallString')
                    _winreg.CloseKey(key)
                except WindowsError:
                    uninstall_string = None

        return uninstall_string

    # Upgrade to latest version
    def upgrade_version(self, progress_callback=None):
        cont = True
        try:
            # Download first
            cont = self.download_latest_version(progress_callback)
            if cont != False: cont = True

            # Uninstall existing version
            if cont == True and self.app_config[APP_UPGRADES] == 'false':
                cont = self.uninstall_version()

            # Install new version
            if cont == True:
                cont = self.install_latest_version(progress_callback)
        except KeyError:
            return False

        return cont

    # Execute commands for pre/post install/uninstall
    def execute_script(self, type):
        try: commands = self.app_config[type].split(',')
        except KeyError:
            return True

        # Latest version for installation
        if type == APP_PREINSTALL or type == APP_POSTINSTALL:
            version = None
        # Installed version for uninstallation
        elif type == APP_PREUNINSTALL or type == APP_POSTUNINSTALL:
            version = self.get_installed_version()
            if version == '':
                version = None

        # Execute the commands
        for command in commands:
            command = self.replace_version(command, version)
            command = self.replace_install_dir(command)
            retval = os.popen('"' + command + '"').close()
            if retval != None:
                return False

        return True

    # ***
    # Internal functions for versioning

    # Replace version strings with version value specified or latest version
    def replace_version(self, string, version=None):
        if version == None:
            if self.latestversion == None or self.latestversion == strings.NOT_AVAILABLE: return string
            version = self.latestversion
        elif version == '': return string

        # Deprecated version replacements to use VERSION[x] replacement
        string = re.sub(MAJOR_VERSION, VERSION_REPLACE % '0', string)
        string = re.sub(MINOR_VERSION, VERSION_REPLACE % '1', string)
        string = re.sub(SUB_VERSION, VERSION_REPLACE % '2', string)
        string = re.sub(MAJORMINOR_VERSION, VERSION_REPLACE % ':2', string)
        string = re.sub(MAJORMINORSUB_VERSION, VERSION_REPLACE % ':3', string)

        # Deprecated version replacements to use REPLACE(x,y,z) replacement
        string = re.sub(DOTLESS_VERSION, REPLACE_REPLACE % (DELIMITERS, '', VERSION), string)
        string = re.sub(DASHTODOT_VERSION, REPLACE_REPLACE % ('-', '.', VERSION), string)
        string = re.sub(DOTTOUNDERSCORE_VERSION, REPLACE_REPLACE % ('[.]', '_', VERSION), string)
        string = re.sub(DOTTODASH_VERSION, REPLACE_REPLACE % ('[.]', '-', VERSION), string)

        # Replace version in the specified string
        string = re.sub(VERSION, version, string)

        # VERSION[x] replacement
        matches = re.findall(VERSION_SEARCH, string)
        splitversion = re.split(DELIMITERS, version)
        delimiters = re.sub('[0-9a-z]', '', version)
        for match in matches:
            if match != '':
                try: replace = eval('splitversion[%s]' % match)
                except IndexError: replace = ''

                if type(replace) != types.StringType:
                    try: dl = eval('delimiters[%s]' % match)
                    except IndexError: dl = ''
                    replace = self.combine_multipart_version_with_delimiters([replace], dl)[0]
                    if replace[-1] in DELIMITERS:
                        replace = replace[:-1]
            else:
                replace = ''

            string = string.replace(VERSION_REPLACE % match, replace)

        # REPLACE(x,y,z) replacement
        matches = re.findall(REPLACE_SEARCH, string)
        for match in matches:
            if len(match):
                [srch, repl, str] = match
                if srch != '' and str != '':
                    replace = re.sub(srch, repl, str)
                    string = string.replace(REPLACE_REPLACE % (srch, repl, str), replace)

        return string

    # Replace version strings with *
    def replace_version_with_mask(self, string):
        string = re.sub(VERSION, '*', string)
        string = re.sub(VERSION_SEARCH, '*', string)
        string = re.sub(REPLACE_SEARCH, '*', string)
        string = re.sub(MAJOR_VERSION, '*', string)
        string = re.sub(MINOR_VERSION, '*', string)
        string = re.sub(SUB_VERSION, '*', string)
        string = re.sub(MAJORMINOR_VERSION, '*', string)
        string = re.sub(MAJORMINORSUB_VERSION, '*', string)
        string = re.sub(DOTLESS_VERSION, '*', string)
        string = re.sub(DASHTODOT_VERSION, '*', string)
        string = re.sub(DOTTOUNDERSCORE_VERSION, '*', string)
        string = re.sub(DOTTODASH_VERSION, '*', string)
        return string

    # Replace install dir string with appropriate value
    def replace_install_dir(self, string):
        # Search for install directory
        install_dir = self.get_install_dir()

        # Create install directory string if no install directory found
        if install_dir == '':
            install_dir = os.path.join(self.global_config.user['install_dir'], self.app)

        # Replace install directory
        string = string.replace(INSTALL_DIR, install_dir)

        return self.global_config.expand_env(string)

    # Get all the versions from the scrape page
    def get_versions(self):
        # Call pyurl to get the scrape page
        web_data = self.curl_instance.get_web_data(self.app_config[APP_SCRAPE])
        if web_data == None: return None

        versions = re.findall(self.app_config[APP_VERSION], web_data, re.DOTALL)
        versions = self.handle_multipart_versions(versions, APP_VERSION)

        # Return a list of potential versions
        return versions

    # Handle multipart versions
    def handle_multipart_versions(self, versions, version_key):
        if len(versions) and type(versions[0]) == types.TupleType:
            # Multipart versions, get delimiters if any
            delimiters = self.get_multipart_version_delimiters(self.app_config[version_key])

            # Combine with delimiters
            versions = self.combine_multipart_version_with_delimiters(versions, delimiters)

        return versions

    # Get multipart version delimiters from application version regex
    # (?#xxxx) becomes ['x', 'x', 'x', 'x']
    def get_multipart_version_delimiters(self, string):
        delimiter_array = []
        delimiters = re.findall('\(\?#(.*?)\)', string)
        for delimiter in delimiters:
            for s in delimiter:
                delimiter_array.append(s)
        return delimiter_array

    # Combine version parts with delimiters
    def combine_multipart_version_with_delimiters(self, versions, delimiters):
        # Combine with delimiters
        for i in range(len(versions)):
            combined_version = ''
            for j in range(len(versions[i])):
                combined_version += versions[i][j]
                if j < len(delimiters):
                    combined_version += delimiters[j]
            versions[i] = combined_version

        return versions

    # Split the versions into separate columns
    def get_split_versions(self):
        if self.versions == None: return None

        splitversions = []
        for version in self.versions:
            splitversions.append(re.split(DELIMITERS, version))
        return splitversions

    def get_width(self):
        if self.versions == None: return None

        # Get number of distinct version parts
        width = 0
        for spl in self.splitversions:
            if width < len(spl): width = len(spl)
        return width

    # Convert a letter into a numeric value
    def get_numeric_value(self, letter):
        key = 0.00
        for a in ALPHABET:
            key += 0.01
            if a == letter: return key
        return 0.0

    # Convert a version string into a numeric value
    def convert_to_number(self, version):
        # Conver to lower case
        version = version.lower()

        # Get the letters to convert
        letters = re.findall('[a-z]', version)

        # Convert version to a number without the letters
        nversion = int(re.sub('[ a-z]', '0', version))

        # Convert the letters into a numeric value
        decimal = 0.0
        for letter in letters: decimal += self.get_numeric_value(letter)

        # Return the combination of the numeric portion and converted letters
        return nversion + decimal

    # Find the maximum value in the split version list of the specified column
    def find_max(self, col):
        max = '-1'
        for row in self.splitversions:
            try:
                if self.convert_to_number(row[col]) > self.convert_to_number(max): max = row[col]
            except IndexError: pass
        return max

    # Filter split versions where value of column is as specified
    def filter(self, col, value):
        filteredlist = []
        for row in self.splitversions:
            try:
                if row[col] == value:
                    filteredlist.append(row)
            except IndexError: pass
        self.splitversions = filteredlist

    # Filter split versions until only latest version remains
    def filter_latest_version(self):
        if self.versions == None: return False

        for i in range(self.width):
            max = self.find_max(i)
            if max != '-1': self.filter(i, max)
            else: break

        # Update width to the found version
        self.width = self.get_width()

        return True

    # Unzip a ZIP file to specified directory
    def unzip_file(self, file):
        # Check if a supported zipfile
        if not zipfile.is_zipfile(file):
            return False

        # Check if ZIP file with extract only
        try:
            test = self.app_config[APP_INSTALLER]
            directory = file[:-4]
        except KeyError:
            directory = self.replace_install_dir(INSTALL_DIR)

        # Create directory to extract to
        if os.path.isdir(directory):
            self.delete_tree(directory)
        try: os.mkdir(directory)
        except WindowsError:
            pass

        zip = zipfile.ZipFile(file, 'r')
        for cfile in zip.namelist():
            if cfile[-1] == '/':
                if not os.path.exists(os.path.join(directory, cfile[:-1])):
                    os.mkdir(os.path.join(directory, cfile[:-1]))
            else:
                target = os.path.join(directory, cfile)
                if not os.path.exists(os.path.dirname(target)):
                    os.makedirs(os.path.dirname(target))
                ufile = open(target, 'wb')
                buffer = StringIO.StringIO(zip.read(cfile))
                buflen = 2 ** 20
                data = buffer.read(buflen)
                while data:
                    ufile.write(data)
                    data = buffer.read(buflen)
                ufile.close()

        return True

    # Delete a directory tree
    def delete_tree(self, directory):
        files = glob.glob(os.path.join(directory, '*'))
        for file in files:
            if os.path.isdir(file):
                self.delete_tree(file)
            else:
                try: os.remove(file)
                except WindowsError: pass
        try: os.rmdir(directory)
        except WindowsError:
            pass

    # Get filename or rename if it is present
    def get_filename_or_rename(self):
        filename = self.app_config[APP_FILENAME]
        try: rename = self.app_config[APP_RENAME]
        except KeyError: rename = ''
        if rename != '': filename = rename

        return filename

