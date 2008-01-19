# Import required libraries
import ConfigParser
import defines
import filecmp
import os.path
import process
import re
import shutil
import strings
import sys
import threading
import time
import version
import _winreg

# Configuration file
DB_INI        = 'db.ini'
USERDB_INI    = 'userdb.ini'
CONFIG_INI    = 'config.ini'
INSTALLED_INI = 'installed.ini'
LATEST_INI    = 'latest.ini'

# Paths
SYSTEM_PATH   = '%ALLUSERSPROFILE%\Application Data\AppSnap'

# Config.ini entries
USER           = 'user'
INSTALL_DIR    = 'install_dir'
PROXY_USER     = 'proxy_user'
PROXY_PASSWORD = 'proxy_password'
SILENT_INSTALL = 'silent_install'
CACHE          = 'cache'
CACHE_LOCATION = 'cache_location'
CACHE_TIMEOUT  = 'cache_timeout'
DATABASE       = 'database'
LOCATION       = 'location'
STARTUP_CHECK  = 'startup_check'
UPDATE         = 'update'
NETWORK        = 'network'
DOWNLOAD       = 'download'

# Latest.ini entries
TIMESTAMP      = 'timestamp'

# Built-in categories
ALL            = strings.ALL
INSTALLED      = strings.INSTALLED
NOT_INSTALLED  = strings.NOT_INSTALLED
PROCESSING     = strings.PROCESSING
UPGRADEABLE    = strings.UPGRADEABLE
REMOVABLE      = strings.REMOVABLE

# Add/Remove program section identifier
ARP_ID         = '@ARP@'

# Configuration loading class
class config:
    # Constructor - creates a config parser object
    def __init__(self):
        # Lock to serialize INI writing
        self.lock = threading.Lock()
        
        # Load the database information
        try:
            self.db = ConfigParser.SafeConfigParser()
            self.db.read(DB_INI)
        except ConfigParser.MissingSectionHeaderError:
            print strings.APPSNAP_DATABASE_CORRUPT + '\n'
            pass

        # Load the user database information
        try:
            self.userdb = ConfigParser.SafeConfigParser()
            self.userdb.read(USERDB_INI)
            self.merge_user_db()
        except ConfigParser.MissingSectionHeaderError:
            print strings.USER_DATABASE_CORRUPT + '\n'
            pass

        # Load the user configuration
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(CONFIG_INI))
        # User variables
        self.user = self.convert_to_hash(self.config.items(USER))
        self.cache = self.convert_to_hash(self.config.items(CACHE))
        self.database = self.convert_to_hash(self.config.items(DATABASE))
        self.update = self.convert_to_hash(self.config.items(UPDATE))
        self.network = self.convert_to_hash(self.config.items(NETWORK))
        
        # Remove file: from cache location if specified
        if self.cache[CACHE_LOCATION][:5].lower() == 'file:':
            self.cache[CACHE_LOCATION] = self.cache[CACHE_LOCATION][5:]
        
        # Expand environment variables in cache location if any
        self.cache[CACHE_LOCATION] = self.expand_env(self.cache[CACHE_LOCATION])
            
        # Copy database to cache location if not already done
        self.copy_database_to_cache()

        # Ensure system path exists
        self.system_path = self.expand_env(SYSTEM_PATH)
        if not os.path.exists(self.system_path):
            os.makedirs(self.system_path)

        # Load the installed applications
        self.installed_ini = os.path.join(self.system_path, INSTALLED_INI)
        self.installed = ConfigParser.SafeConfigParser()
        self.installed.read(self.installed_ini)
        
        # Filter out sections that aren't in main db
        for section in self.installed.sections():
            if not self.db.has_section(section):
                self.installed.remove_section(section)
                
        # Add AppSnap to installed applications list
        self.add_installed_version(version.APPNAME, version.APPVERSION)
        
        # Load the version cache
        self.latest_ini = os.path.join(self.cache[CACHE_LOCATION], LATEST_INI)
        self.latest = ConfigParser.SafeConfigParser()
        self.latest.read(self.latest_ini)
        
        # Load Add/Remove programs list
        self.arp_list = self.load_arp()

    #####
    # Get
    #####

    # Get sections
    def get_sections(self):
        sections = self.db.sections()
        sections.sort(lambda a,b: cmp(a.upper(), b.upper()))
        return sections

    # Gets all the items for a section
    def get_section_items(self, section):
        if self.db.has_section(section):
            items = self.convert_to_hash(self.db.items(section))
            self.check_section_items(section, items)
        else: items = None

        return items

    # Get categories
    def get_categories(self):
        # Get the sections
        sections = self.get_sections()

        categories = []
        for section in sections:
            items = self.get_section_items(section)
            if items[process.APP_CATEGORY] not in categories: categories.append(items[process.APP_CATEGORY])

        categories.sort(lambda a,b: cmp(a.upper(), b.upper()))
        return categories

    # Get sections by category
    def get_sections_by_category(self, category):
        sections = self.get_sections()

        cat_sections = []
        for section in sections:
            items = self.get_section_items(section)
            if (category == items[process.APP_CATEGORY]):
                cat_sections.append(section)

        return cat_sections

    # Get sections by string
    def filter_sections_by_string(self, sections, string):
        string_sections = []
        for section in sections:
            if section.lower().find(string.lower()) != -1:
                string_sections.append(section)

        return string_sections

    #####
    # Display
    #####

    # Display categories
    def display_categories(self):
        # Get the categories
        categories = [INSTALLED, NOT_INSTALLED, REMOVABLE]
        categories.extend(self.get_categories())

        print strings.AVAILABLE_CATEGORIES + '\n'
        for category in categories:
            print '  ' + category

    # Display available sections
    def display_available_sections(self, category='', string=''):
        # Get the sections
        if category == INSTALLED:
            sections = self.installed.sections()
            category = ''
            print strings.INSTALLED_APPLICATIONS + '\n'
        elif category == NOT_INSTALLED:
            sections = [item for item in self.get_sections() if item not in self.installed.sections()]
            category = ''
            print strings.NOT_INSTALLED_APPLICATIONS + '\n'
        elif category == REMOVABLE:
            sections = self.get_arp_sections()
        else:
            sections = self.get_sections()
            print strings.SUPPORTED_APPLICATIONS + '\n'

        if category != '': print strings.CATEGORY + ' : ' + category
        if string != '': print strings.FILTER + ' : ' + string + '\n'
        else:
            print
        for section in sections:
            if string == '' or (string != '' and section.lower().find(string.lower()) != -1):
                items = self.get_section_items(section)
                if items == None: items = self.get_arp_section_items(section)
                if items == None: continue
                if category == '' or (category == items[process.APP_CATEGORY]):
                    print strings.APPLICATION + ' : ' + re.sub(ARP_ID, '', section)
                    if items[process.APP_DESCRIBE] != '':
                        print strings.DESCRIPTION + ' : ' + items[process.APP_DESCRIBE]
                    if items[process.APP_WEBSITE] != '':
                        print strings.WEBSITE + ' : ' + items[process.APP_WEBSITE]
                    print

    #####
    # Installed Version
    #####

    def add_installed_version(self, appname, appversion):
        if not self.installed.has_section(appname):
            self.installed.add_section(appname)
        self.installed.set(appname, process.APP_VERSION, appversion)

    # Get installed version
    def get_installed_version(self, section):
        if self.installed.has_section(section) == True:
            try: version = self.installed.get(section, process.APP_VERSION)
            except ConfigParser.NoOptionError: version = ''
            if version == 'Not available': version = strings.NOT_AVAILABLE
            return version
        return ''

    # Save installed version to file
    def save_installed_version(self, section, version):
        self.lock.acquire()
        
        if self.installed.has_section(section) == False:
            self.installed.add_section(section)
        if version == strings.NOT_AVAILABLE: version = 'Not available'
        self.installed.set(section, process.APP_VERSION, version)
        try:
            inifile = open(self.installed_ini, 'w')
            self.installed.write(inifile)
            inifile.close()
        except IOError:
            print strings.INSTALLED_INI_UPDATE_FAILED
            
        self.lock.release()

    # Delete installed version from file
    def delete_installed_version(self, section):
        self.lock.acquire()
        
        if self.installed.has_section(section) == True:
            self.installed.remove_section(section)
            try:
                inifile = open(self.installed_ini, 'w')
                self.installed.write(inifile)
                inifile.close()
            except:
                print strings.INSTALLED_INI_UPDATE_FAILED
                
        self.lock.release()

    #####
    # Cached Latest Version
    #####

    # Get cached latest version
    def get_cached_latest_version(self, section):
        if self.latest.has_section(section) == True:
            if time.time() - float(self.latest.get(section, TIMESTAMP)) < int(self.cache[CACHE_TIMEOUT]) * defines.NUM_SECONDS_IN_DAY:
                return self.latest.get(section, process.APP_VERSION)
        return None

    # Save cached latest version to file
    def save_cached_latest_version(self, section, version):
        self.lock.acquire()
        
        if self.latest.has_section(section) == False:
            self.latest.add_section(section)
        self.latest.set(section, process.APP_VERSION, version)
        self.latest.set(section, TIMESTAMP, time.time().__str__())

        # Create cache directory
        self.create_cache_directory()
    
        # Save version
        try:
            inifile = open(self.latest_ini, 'w')
            self.latest.write(inifile)
            inifile.close()
        except IOError:
            print strings.LATEST_INI_UPDATE_FAILED
    
        self.lock.release()

    #####
    # Helper functions
    #####
    
    # Create cache directory
    def create_cache_directory(self):
        if not os.path.exists(self.cache[CACHE_LOCATION]):
            try:
                os.makedirs(self.cache[CACHE_LOCATION])
            except IOError:
                print strings.FAILED_CREATE_CACHE_DIR + ' : ' + self.cache[CACHE_LOCATION]
                
    # Copy database to cache directory
    def copy_database_to_cache(self, overwrite=False):
        if os.path.exists(DB_INI):
            cached_db = os.path.join(self.cache[CACHE_LOCATION], DB_INI)
            self.create_cache_directory()
            if not os.path.exists(cached_db) or overwrite == True or filecmp.cmp(DB_INI, cached_db) == False:
                shutil.copy(DB_INI, cached_db)

    # Check if a section has all the expected fields
    def check_section_items(self, section, items):
        keys = [
                process.APP_CATEGORY,
                process.APP_FILENAME,
                process.APP_UPGRADES
        ]
        for key in keys:
            if not key in items:
                print strings.MISSING_SECTION_KEY + '. ' + strings.SECTION + ' = ' + section + ', ' + strings.KEY + ' = ' + key
                sys.exit(defines.ERROR_MISSING_SECTION_KEY)
        if process.APP_SCRAPE in items and not process.APP_VERSION in items:
            print strings.MISSING_VERSION_WHEN_SCRAPE + '. ' + strings.SECTION + ' = ' + section
            sys.exit(defines.ERROR_MISSING_VERSION_WHEN_SCRAPE)
        if not process.APP_SCRAPE in items and not process.APP_DOWNLOAD in items:
            print strings.MISSING_SCRAPE_AND_DOWNLOAD + '. ' + strings.SECTION + ' = ' + section
            sys.exit(defines.MISSING_SCRAPE_AND_DOWNLOAD)

    # Convert a config list into a hash
    def convert_to_hash(self, list):
        items = {}
        for i in list: items[i[0]] = i[1]
        return items

    # Merge the userdb with the main db
    def merge_user_db(self):
        # Get user sections
        user_sections = self.userdb.sections()
        for user_section in user_sections:
            # Remove the db version
            if self.db.has_section(user_section):
                self.db.remove_section(user_section)

            # Add the section
            self.db.add_section(user_section)

            # Add each option
            options = self.userdb.options(user_section)
            for option in options:
                self.db.set(user_section, option, self.userdb.get(user_section, option))
    
    # Expand string containing environment variable
    def expand_env(self, string):
        if string == '': return string
        
        pipe = os.popen("cmd /c echo " + string)
        exp_string = pipe.read()
        pipe.close()

        return exp_string[:-1]
    
    #####
    # Add/Remove Programs
    #####
    
    # Create Add/Remove program list
    def load_arp(self):
        arp_list = {}
        named = self.registry_search_arp('DisplayName')
        uninstallable = self.registry_search_arp('UninstallString')
        for un in uninstallable:
            if not re.match('KB[0-9]+[.*]*', un) and named.get(un) != None and named.get(un).groups()[0] != '':
                arp_list[named.get(un).groups()[0] + ARP_ID] = {
                                           process.APP_CATEGORY: REMOVABLE,
                                           process.APP_DESCRIBE: '',
                                           process.APP_WEBSITE: '',
                                           process.APP_UNINSTALL: un,
                                           process.APP_INSTVERSION: 'REGISTRY_SEARCH:DisplayVersion=(.*)'
                                           }

        return arp_list
    
    # Get ARP sections
    def get_arp_sections(self):
        sections = self.arp_list.keys()
        sections.sort(lambda a,b: cmp(a.upper(), b.upper()))
        return sections
    
    # Get ARP items
    def get_arp_section_items(self, section):
        if self.arp_list.has_key(section):
            return self.arp_list[section]
        else:
            return None
        
    #####
    # Registry Searching
    #####
    
    # Search for uninstall entry based on name and value provided
    def registry_search_uninstall_entry(self, name, value):
        uninstall_key = ''
        matchobj = None
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall')
            uninstall_keys = self.registry_search(key, name, value, True)
            _winreg.CloseKey(key)
        except WindowsError:
            pass
        
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall')
            uninstall_keys.update(self.registry_search(key, name, value, True))
            _winreg.CloseKey(key)
        except WindowsError:
            pass

        # Return only latest version or last found
        for u_key in uninstall_keys.keys():
            if matchobj == None or (len(matchobj.groups()) and len(uninstall_keys[u_key].groups()) and matchobj.groups()[0] < uninstall_keys[u_key].groups()[0]):
                uninstall_key = u_key
                matchobj = uninstall_keys[u_key]

        return uninstall_key, matchobj
        
    # Search for name value provided under uninstall location in registry with specified key
    def registry_search_uninstall_location(self, uninstall_key, name, value):
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + uninstall_key)
            subvalue, temp = _winreg.QueryValueEx(key, name)
            _winreg.CloseKey(key)
        except WindowsError:
            subvalue = ''
        
        if subvalue == '':
            try:
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\' + uninstall_key)
                subvalue, temp = _winreg.QueryValueEx(key, name)
                _winreg.CloseKey(key)
            except WindowsError:
                subvalue = ''
                
        if subvalue != '':
            matchobj = re.match(value, subvalue)
            if matchobj != None and len(matchobj.groups()) and matchobj.groups()[0] != None:
                return matchobj
            
        return ''
    
    # Find all Add/Remove applications in the registry
    def registry_search_arp(self, subkey):
        uninstallable = {}
        try:
            key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall')
            uninstallable = self.registry_search(key, subkey, '(.*)', True)
            _winreg.CloseKey(key)
        except WindowsError:
            pass
        
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall')
            uninstallable.update(self.registry_search(key, subkey, '(.*)', True))
            _winreg.CloseKey(key)
        except WindowsError:
            pass

        return uninstallable
    
    # Search for registry key
    def registry_search(self, key, name, value, all=False):
        i = 0
        matching = {}
        try:
            while 1:
                subkey_name = _winreg.EnumKey(key, i)
                i += 1
                try:
                    subkey = _winreg.OpenKey(key, subkey_name)
                    subvalue, temp = _winreg.QueryValueEx(subkey, name)
                    _winreg.CloseKey(subkey)
                except WindowsError:
                    continue
                except TypeError:
                    continue
                matchobj = re.match(value, subvalue)
                if matchobj != None:
                    if all == False: return subkey_name, matchobj
                    else: matching[subkey_name] = matchobj
        except EnvironmentError: pass
        
        if all == False: return '', None
        else: return matching
