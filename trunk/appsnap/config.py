# Import required libraries
import ConfigParser
import os.path
import shutil
import sys
import time
import version

# Configuration file
DB        = 'db.ini'
USERDB    = 'userdb.ini'
CONFIG    = 'config.ini'
INSTALLED = 'installed.ini'
LATEST    = 'latest.ini'

# Configuration loading class
class config:
    # Constructor - creates a config parser object
    def __init__(self):
        # Load the database information
        self.db = ConfigParser.SafeConfigParser()
        self.db.readfp(open(DB))

        # Load the user database information
        self.userdb = ConfigParser.SafeConfigParser()
        self.userdb.read(USERDB)
        self.merge_user_db()

        # Load the user configuration
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(CONFIG))
        # User variables
        self.user = self.convert_to_hash(self.config.items('user'))
        self.cache = self.convert_to_hash(self.config.items('cache'))
        self.database = self.convert_to_hash(self.config.items('database'))
        self.network = self.convert_to_hash(self.config.items('network'))
        
        # Remove file: from cache location if specified
        if self.cache['cache_location'][:5].lower() == 'file:':
            self.cache['cache_location'] = self.cache['cache_location'][5:]
            
        # Copy database to cache location if not already done
        self.copy_database_to_cache()

        # Load the installed applications
        self.installed = ConfigParser.SafeConfigParser()
        self.installed.read(INSTALLED)
        
        # Filter out sections that aren't in main db
        for section in self.installed.sections():
            if not self.db.has_section(section):
                self.installed.remove_section(section)
                
        # Add AppSnap to installed applications list
        if not self.installed.has_section(version.APPNAME):
            self.installed.add_section(version.APPNAME)
        self.installed.set(version.APPNAME, 'version', version.APPVERSION)
        
        # Load the version cache
        self.latest_ini = os.path.join(self.cache['cache_location'], LATEST)
        self.latest = ConfigParser.SafeConfigParser()
        self.latest.read(self.latest_ini)

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
            if items['category'] not in categories: categories.append(items['category'])

        categories.sort(lambda a,b: cmp(a.upper(), b.upper()))
        return categories

    # Get sections by category
    def get_sections_by_category(self, category):
        sections = self.get_sections()

        cat_sections = []
        for section in sections:
            items = self.get_section_items(section)
            if (category == items['category']):
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
        categories = self.get_categories()

        print 'Available Categories\n'
        for category in categories:
            print '  ' + category

    # Display available sections
    def display_available_sections(self, category='', string=''):
        # Get the sections
        if category == 'Installed':
            sections = self.installed.sections()
            category = ''
            print 'Installed Applications\n'
        else:
            sections = self.get_sections()
            print 'Supported Applications\n'

        if category != '': print 'Category    : ' + category
        if string != '': print 'Filter      : ' + string + '\n'
        else:
            print
        for section in sections:
            if string == '' or (string != '' and section.lower().find(string.lower()) != -1):
                items = self.get_section_items(section)
                if category == '' or (category == items['category']):
                    print 'Application : ' + section
                    print 'Description : ' + items['describe']
                    print 'Website     : ' + items['website']
                    print

    #####
    # Installed Version
    #####

    # Get installed version
    def get_installed_version(self, section):
        if self.installed.has_section(section) == True:
            return self.installed.get(section, 'version')
        return ''

    # Save installed version to file
    def save_installed_version(self, section, version):
        if self.installed.has_section(section) == False:
            self.installed.add_section(section)
        self.installed.set(section, 'version', version)
        try:
            self.installed.write(open(INSTALLED, 'w'))
        except IOError:
            print 'Failed to update installed.ini. Is it writable?'

    # Delete installed version from file
    def delete_installed_version(self, section):
        if self.installed.has_section(section) == True:
            self.installed.remove_section(section)
            try:
                self.installed.write(open(INSTALLED, 'w'))
            except:
                print 'Failed to update installed.ini. Is it writable?'

    #####
    # Cached Latest Version
    #####

    # Get cached latest version
    def get_cached_latest_version(self, section):
        if self.latest.has_section(section) == True:
            if time.time() - float(self.latest.get(section, 'timestamp')) < int(self.cache['cache_timeout']) * 24 * 60 * 60:
                return self.latest.get(section, 'version')
        return None

    # Save cached latest version to file
    def save_cached_latest_version(self, section, version):
        if self.latest.has_section(section) == False:
            self.latest.add_section(section)
        self.latest.set(section, 'version', version)
        self.latest.set(section, 'timestamp', time.time().__str__())

        # Create cache directory
        self.create_cache_directory()
    
        # Save version
        try:
            self.latest.write(open(self.latest_ini, 'w'))
        except IOError:
            print 'Failed to update latest.ini. Is it writable?'

    #####
    # Helper functions
    #####
    
    # Create cache directory
    def create_cache_directory(self):
        if not os.path.exists(self.cache['cache_location']):
            try:
                os.mkdir(self.cache['cache_location'])
            except IOError:
                print 'Failed to create cache location'
                
    # Copy database to cache directory
    def copy_database_to_cache(self, overwrite=False):
        cached_db = os.path.join(self.cache['cache_location'], DB)
        self.create_cache_directory()
        if not os.path.exists(cached_db) or overwrite == True:
            shutil.copy(DB, cached_db)

    # Check if a section has all the expected fields
    def check_section_items(self, section, items):
        keys = (
            'category filename instparam upgrades chinstdir uninstall uninstparam'
        ).split(' ')
        for key in keys:
            if not key in items:
                print "Missing key '" + key + "' in section '" + section + "'"
                sys.exit()
        if 'scrape' in items and not 'version' in items:
            print "Missing key 'version' when 'scrape' specified in section '" + section + "'"
            sys.exit()
        if not 'scrape' in items and not 'download' in items:
            print "Neither 'scrape' nor 'download' specified in section '" + section + "'"
            sys.exit()

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