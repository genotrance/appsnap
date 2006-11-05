# Import required libraries
import sys
import ConfigParser

# Configuration file
DB = 'db.ini'
CONFIG = 'config.ini'
INSTALLED = 'installed.ini'

# Configuration loading class
class config:
    # Constructor - creates a config parser object
    def __init__(self):
        # Load the database information
        self.db = ConfigParser.SafeConfigParser()
        self.db.readfp(open(DB))

        # Load the user configuration
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(CONFIG))
        # User variables
        self.user = self.convert_to_hash(self.config.items('user'))
        self.cache = self.convert_to_hash(self.config.items('cache'))
        self.database = self.convert_to_hash(self.config.items('database'))

        # Load the installed applications
        self.installed = ConfigParser.SafeConfigParser()
        self.installed.read(INSTALLED)

    #####
    # Get
    #####

    # Get sections
    def get_sections(self):
        return self.db.sections()

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
    def display_available_sections(self, category=''):
        # Get the sections
        if category == 'Installed':
            sections = self.installed.sections()
            category = ''
            print 'Installed Applications\n'
        else:
            sections = self.get_sections()
            print 'Supported Applications\n'
        sections.sort()

        if category != '': print '  Category    : ' + category + '\n'
        for section in sections:
            items = self.get_section_items(section)
            if category == '' or (category == items['category']):
                print '  Application : ' + section
                print '  Description : ' + items['describe']
                print '  Website     : ' + items['website']
                print ''

    #####
    # Version
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
        self.installed.write(open(INSTALLED, 'w'))

    # Delete installed version from file
    def delete_installed_version(self, section):
        if self.installed.has_section(section) == True:
            self.installed.remove_section(section)
            self.installed.write(open(INSTALLED, 'w'))

    #####
    # Helper functions
    #####

    # Check if a section has all the expected fields
    def check_section_items(self, section, items):
        keys = (
            'category scrape version filename ' +
            'instparam upgrades chinstdir uninstall uninstparam'
        ).split(' ')
        for key in keys:
            if not key in items:
                print "Missing key '" + key + "' in section '" + section + "'"
                sys.exit()

    # Convert a config list into a hash
    def convert_to_hash(self, list):
        items = {}
        for i in list: items[i[0]] = i[1]
        return items