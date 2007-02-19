# Import required libraries
import glob
import os
import os.path
import re
import string
import StringIO
import time
import _winreg
import zipfile

# Shortcut to convert versions with letters in them
ALPHABET = 'a b c d e f g h i j k l m n o p q r s t u v w x y z'.split(' ')

# Regular expressions
DELIMITERS                 = '[._-]'
VERSION                    = '#VERSION#'
MAJOR_VERSION              = '#MAJOR_VERSION#'
MAJORMINOR_VERSION         = '#MAJORMINOR_VERSION#'
MAJORMINORSUB_VERSION      = '#MAJORMINORSUB_VERSION#'
DOTLESS_VERSION            = '#DOTLESS_VERSION#'
DASHTODOT_VERSION          = '#DASHTODOT_VERSION#'
DOTTOUNDERSCORE_VERSION    = '#DOTTOUNDERSCORE_VERSION#'
INSTALL_DIR                = '#INSTALL_DIR#'

# Version not available
NOT_AVAILABLE      = 'Not Available'

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

        # Get version only if scrape specified
        if 'scrape' in self.app_config and 'version' in self.app_config:
            self.latestversion = None
            self.versions = self.get_versions()
            self.splitversions = self.get_split_versions()
            self.width = self.get_width()
        else:
            self.latestversion = NOT_AVAILABLE
            self.versions = None
            self.splitversions = None
            self.width = 0

    # ***
    # External functions

    # Get the latest version
    def get_latest_version(self):
        # No versioning available
        if self.latestversion == NOT_AVAILABLE: return self.latestversion

        # Filter latest
        if self.filter_latest_version() == False: return None

        version = ''
        for i in range(self.width):
            version += self.splitversions[0][i]
            if i < self.width-1: version += DELIMITERS

        for i in range(len(self.versions)):
            if re.match(version, self.versions[i]):
                self.latestversion = self.versions[i]
                return self.versions[i]

        return None

    # Download the latest version of the application's installer
    def download_latest_version(self, progress_callback=None):
        # Get latest version if not already done
        if self.latestversion == None: self.get_latest_version()

        # If still not available, return false
        if self.latestversion == None: return False

        # Get download URL, default to scrape
        try: download = self.replace_version(self.app_config['download'])
        except KeyError: download = self.app_config['scrape']

        # Get filename
        filename = self.replace_version(self.app_config['filename'])

        # Get referer
        try: referer = self.replace_version(self.app_config['referer'])
        except KeyError:
            try: referer = self.app_config['scrape']
            except KeyError: referer = self.app_config['download']

        # Get cached location to save file to
        cached_filename = self.curl_instance.get_cached_name(filename)
        
        # Download if new version not already downloaded or if filename does not
        # contain version information and more than a day old (we have no way to
        # know if the file has changed)
        if not os.path.exists(cached_filename) or (
                                                   filename == self.app_config['filename'] and
                                                   os.path.exists(cached_filename) and
                                                   (time.time() - os.stat(cached_filename).st_ctime > 86400)
                                                   ):
            # Delete any older cached versions
            self.delete_older_versions()

            # Return false if download fails
            if self.curl_instance.download_web_data(download, filename, referer, progress_callback) != True: return False

        return cached_filename

    # Delete older application installers
    def delete_older_versions(self):
        # Create pattern for filename
        filename = self.app_config['filename']
        filename = re.sub(VERSION, '*', filename)
        filename = re.sub(MAJOR_VERSION, '*', filename)
        filename = re.sub(MAJORMINOR_VERSION, '*', filename)
        filename = re.sub(MAJORMINORSUB_VERSION, '*', filename)
        filename = re.sub(DOTLESS_VERSION, '*', filename)
        filename = re.sub(DASHTODOT_VERSION, '*', filename)
        filename = self.curl_instance.get_cached_name(filename)

        # Find all older versions
        older_files = glob.glob(filename)
        for older_file in older_files:
            os.remove(older_file)
            if older_file[-3:] == 'zip':
                self.delete_tree(older_file[:-4])

    # Install the latest version of the application
    def install_latest_version(self):
        # Download the latest version if required
        cached_filename = self.download_latest_version()
        if cached_filename == False: return False

        # Create the command to execute
        if cached_filename[-3:] == 'msi':
            command = 'msiexec /i "' + cached_filename + '"'
        elif cached_filename[-3:] == 'zip':
            self.unzip_file(cached_filename)
            try: command = '"' + os.path.join(cached_filename[:-4], self.replace_version(self.app_config['installer'])) + '"'
            except KeyError: return False
        else:
            command = '"' + cached_filename + '"'

        # Add instparam flags if available
        if self.app_config['instparam'] != '':
            command += ' ' + self.replace_install_dir(self.app_config['instparam'])

        # Add the install directory if available
        if self.app_config['chinstdir'] != '':
            command += ' ' + self.replace_install_dir(self.app_config['chinstdir'])

        # Run the installer, check return value
        retval = os.popen('"' + command + '"').close()
        if  retval != None:
            # MSI returns non-zero as success too
            if cached_filename[-3:] == 'msi' and (retval == 1641 or retval == 3010): pass
            else: return False

        # Save installed version
        self.global_config.save_installed_version(self.app, self.latestversion)

        # Return
        return True

    # Uninstall the currently installed version of the application
    def uninstall_version(self):
        # Get installed version
        installed_version = self.global_config.get_installed_version(self.app)
        if installed_version == '':
            if self.latestversion == None: self.get_latest_version()
            installed_version = self.latestversion

        try:
            # Get uninstall string from registry
            uninstall = self.replace_version(self.app_config['uninstall'], installed_version)
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + uninstall)
            uninstall_string, temp = _winreg.QueryValueEx(key, 'UninstallString')
            _winreg.CloseKey(key)

            # Run uninstaller, check return value
            if uninstall_string[0] != '"': uninstall_string = '"' + re.sub('.exe', '.exe"', uninstall_string)
            retval = os.popen('"' + uninstall_string + ' ' + self.replace_install_dir(self.app_config['uninstparam']) + '"').close()
            if  retval != None:
                # MSI returns non-zero as success too
                if (retval == 1641 or retval == 3010): pass
                else: return False

            # Delete installed version
            self.global_config.delete_installed_version(self.app)
        except WindowsError:
            return False

        return True

    # Upgrade to latest version
    def upgrade_version(self):
        cont = True
        if self.app_config['upgrades'] == 'false':
            cont = self.uninstall_version()
        if cont == True:
            cont = self.install_latest_version()

        return cont

    # ***
    # Internal functions for versioning

    # Replace version strings with version value specified or latest version
    def replace_version(self, string, version=None):
        if version == None:
            if self.latestversion == None or self.latestversion == NOT_AVAILABLE: return string
            version = self.latestversion
        elif version == '': return string

        # Create the versions
        try: major_version = re.findall('^([0-9]+)', version)[0]
        except IndexError: major_version = version
        try: majorminor_version = re.findall('^([0-9]+[._-][0-9]+).*', version)[0]
        except IndexError: majorminor_version = version
        try: majorminorsub_version = re.findall('^([0-9]+[._-][0-9]+[._-][0-9]+).*', version)[0]
        except IndexError: majorminorsub_version = version
        dotless_version = re.sub(DELIMITERS, '', version)
        dashtodot_version = re.sub('-', '.', version)
        dottounderscore_version = re.sub('\.', '_', version)

        # Replace in the specified string
        string = re.sub(VERSION, version, string)
        string = re.sub(MAJOR_VERSION, major_version, string)
        string = re.sub(MAJORMINOR_VERSION, majorminor_version, string)
        string = re.sub(MAJORMINORSUB_VERSION, majorminorsub_version, string)
        string = re.sub(DOTLESS_VERSION, dotless_version, string)
        string = re.sub(DASHTODOT_VERSION, dashtodot_version, string)
        string = re.sub(DOTTOUNDERSCORE_VERSION, dottounderscore_version, string)

        return string

    # Replace install dir string with appropriate value
    def replace_install_dir(self, string):
        # Create install directory string
        install_dir = self.global_config.user['install_dir'] + '\\' + self.app

        # Replace install directory
        string = re.sub(INSTALL_DIR, install_dir, string)

        return string

    # Get all the versions from the scrape page
    def get_versions(self):
        # Call pyurl to get the scrape page
        web_data = self.curl_instance.get_web_data(self.app_config['scrape'])
        if web_data == None: return None

        # Return a list of potential versions
        return re.findall(self.app_config['version'], web_data)

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
        nversion = string.atoi(re.sub('[a-z]', '', version))

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
        
        # Create directory to extract to
        directory = file[:-4]
        if os.path.isdir(directory):
            self.delete_tree(directory)
        os.mkdir(directory)
        
        zip = zipfile.ZipFile(file, 'r')
        for cfile in zip.namelist():
            if cfile[-1] == '/':
                os.mkdir(os.path.join(directory, cfile[:-1]))
            else:
                ufile = open(os.path.join(directory, cfile), 'wb')
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
                os.remove(file)
        os.rmdir(directory)