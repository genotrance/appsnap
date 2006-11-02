# Import required libraries
import re
import string
import _winreg
import os
import os.path

# Shortcut to convert versions with letters in them
ALPHABET = 'a b c d e f g h i j k l m n o p q r s t u v w x y z'.split(' ')

# Regular expressions
DELIMITERS         = '[._-]'
VERSION            = '#VERSION#'
MAJORMINOR_VERSION = '#MAJORMINOR_VERSION#'
DOTLESS_VERSION    = '#DOTLESS_VERSION#'
INSTALL_DIR        = '#INSTALL_DIR#'

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

        # Version information
        self.latestversion = None
        self.versions = self.get_versions()
        self.splitversions = self.get_split_versions()
        self.width = self.get_width()

    # ***
    # External functions

    # Get the latest version
    def get_latest_version(self):
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
    def download_latest_version(self):
        # Get latest version if not already done
        if self.latestversion == None: self.get_latest_version()

        # If still not available, return false
        if self.latestversion == None: return False

        download = self.replace_version(self.app_config['download'])
        filename = self.replace_version(self.app_config['filename'])

        cached_filename = self.curl_instance.get_cached_name(filename)
        if not os.path.exists(cached_filename):
            # Return false if download fails
            if self.curl_instance.download_web_data(download, filename) != True: return False

        return cached_filename

    # Install the latest version of the application
    def install_latest_version(self):
        # Download the latest version if required
        cached_filename = self.download_latest_version()
        if cached_filename == False: return False

        # Create the command to execute
        args = [cached_filename]

        # Add instparam flags if available
        if self.app_config['instparam'] != '':
            args.append(self.replace_install_dir(self.app_config['instparam']))

        # Add the install directory if available
        if self.app_config['chinstdir'] != '':
            args.append(self.replace_install_dir(self.app_config['chinstdir']))

        # Run the installer
        os.spawnv(os.P_WAIT, cached_filename, args)

        # Return
        return True

    # Uninstall the currently installed version of the application
    def uninstall_version(self):
        # Get latest version if not already done
        if self.latestversion == None: self.get_latest_version()

        try:
            # Get uninstall string from registry
            uninstall = self.replace_version(self.app_config['uninstall'])
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + uninstall)
            uninstall_string, temp = _winreg.QueryValueEx(key, 'UninstallString')
            _winreg.CloseKey(key)

            # Run uninstaller
            if uninstall_string[0] != '"': uninstall_string = '"' + re.sub('.exe', '.exe"', uninstall_string)
            os.system('"' + uninstall_string + ' ' + self.replace_install_dir(self.app_config['uninstparam']) + '"')
        except WindowsError:
            print 'Failed'
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

    # Replace version strings with appropriate values
    def replace_version(self, string):
        if self.latestversion == None: return string

        # Create the versions
        version = self.latestversion
        try: majorminor_version = re.findall('^([0-9]+[._-][0-9]+).*', self.latestversion)[0]
        except IndexError: majorminor_version = version
        dotless_version = re.sub(DELIMITERS, '', self.latestversion)

        # Replace in the specified string
        string = re.sub(VERSION, version, string)
        string = re.sub(MAJORMINOR_VERSION, majorminor_version, string)
        string = re.sub(DOTLESS_VERSION, dotless_version, string)

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