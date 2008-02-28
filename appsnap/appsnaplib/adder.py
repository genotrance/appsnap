import glob
import os
import re
import string
import sys

import config, process

FIELDS = [
          process.APP_CATEGORY, process.APP_DESCRIBE, process.APP_WEBSITE,
          process.APP_SCRAPE, process.APP_VERSION, process.APP_DOWNLOAD,
          process.APP_FILENAME, process.APP_RENAME, process.APP_REFERER,
          process.APP_INSTALLER, process.APP_INSTPARAM, process.APP_INSTVERSION,
          process.APP_INSTDIR,
          process.APP_UPGRADES, process.APP_CHINSTDIR, process.APP_UNINSTALL,
          process.APP_UNINSTPARAM, process.APP_PREINSTALL, process.APP_POSTINSTALL,
          process.APP_PREUNINSTALL, process.APP_POSTUNINSTALL          
]

class adder:
    # Constructor
    def __init__(self, configuration, curl_instance):
        # Initialize
        self.apps = {}
        self.configuration = configuration
        self.curl_instance = curl_instance

        # Find AppSnap executable
        if os.path.exists('appsnap.py'): self.appsnap = 'python appsnap.py'
        else: self.appsnap = 'appsnap.exe'

    # Add application wizard
    def add_application(self, app_name, addon=False):
        # Skip apps already in database
        if app_name in self.configuration.get_sections():
            print 'Application \'%s\' already in database' % app_name
            return

        # Initialize
        self.apps[app_name] = {}

        if addon == False:
            # Google search
            os.startfile('http://google.com/search?q=%s' % app_name)

            # Set fields
            fields = FIELDS[:8]    
        else:
            # Set fields
            fields = ['type', 'category', 'describe', 'appid', 'filestart', 'fileend', 'version', 'versionchunk']

        # Create config
        print '- Enter configuration for %s' % app_name
        for field in fields:
            print '> %-15s: ' % field,
            self.apps[app_name][field] = self.interpret_shortcut(field, self.getline())
        self.apps[app_name][process.APP_UPGRADES] = 'false'
        print

        # Write db.ini with app config
        self.write_db_ini(app_name)

        # Reload for addons
        if addon == True: self.reload_app_config(app_name)

        # Try version (-n)
        print 'Is version detection working?',
        self.try_appsnap(app_name)

        # Try download (-n -d -v)
        print 'Is download working?',
        self.try_appsnap(app_name, '-d -v')

        # Get downloaded filename
        filename = self.get_downloaded_filename(app_name)

        # Detect installer type
        self.set_installer_type(app_name, filename)

        # Write db.ini with app config
        self.write_db_ini(app_name)

        # Try install (-n -i)
        print 'Is install working?',
        self.try_appsnap(app_name, '-i')

        # Skip for addons
        if addon == False:
            # Add instversion and uninstall
            print '- Enter uninstall instversion and instdir'
            for field in [process.APP_UNINSTALL, process.APP_INSTVERSION, process.APP_INSTDIR]:
                print '> %-15s: ' % field,
                self.apps[app_name][field] = self.getline()
            print

            # Write db.ini with app config
            self.write_db_ini(app_name)

            # Try instversion (-n)
            print 'Is installed version being detected?',
            self.try_appsnap(app_name)

            # Try uninstall (-x)
            print 'Is uninstall working?',
            self.try_appsnap(app_name, '-x')

            # Try version (-n)
            print 'Is installed version no longer being detected?',
            self.try_appsnap(app_name)

        # Export -V
        print '- Exporting app config'
        os.system('%s -n "%s" -V | vim' % (self.appsnap, app_name))

        # Open Zoho
        print '- Opening Zoho database',
        os.startfile('http://creator.zoho.com/genotrance/appsnap-database/form/1/')
        print '-- pause --',
        self.getline()

        # Refresh DB
        print '- Refreshing remote database',
        os.startfile('http://genotrance.com/appsnap/db/?force=true')
        print '-- pause --',
        self.getline()

        # Update database (-U -D)
        print '\nIs DB getting updated?',
        self.try_appsnap('', '-U -D')

        # Try version (-n)
        print 'Is app now in the official database?',
        self.try_appsnap(app_name)

    # Get line from stdin
    def getline(self):
        line = sys.stdin.readline().strip()
        print '\r',
        return line

    # Expand shortcuts
    def interpret_shortcut(self, type, string):
        # Sourceforge scrape
        if type == process.APP_SCRAPE:
            try:
                [key, value] = string.split(':')
                if key == 'SOURCEFORGE':
                    return 'http://sourceforge.net/projects/%s/download/' % value
            except ValueError: pass

        # Sourceforge download
        elif type == process.APP_DOWNLOAD:
            try:
                [key, value] = string.split(':')
                if key == 'SOURCEFORGE':
                    return 'http://downloads.sourceforge.net/%s/' % value
            except ValueError: pass

        return string

    # Write db.ini
    def write_db_ini(self, app_name):
        print '- Writing db.ini\n'

        # Rebuild database
        db_data = []
        sections = self.configuration.get_sections()
        if app_name not in sections:
            sections.append(app_name)
            sections.sort()

        for section in sections:
            if section == app_name:
                if self.apps[app_name].has_key('type'):
                    db_data.append(self.get_addon_config(app_name, self.apps[app_name]))
                else:
                    db_data.append(self.get_app_config(app_name, self.apps[app_name]))
            else:
                items = self.configuration.get_section_items(section)
                db_data.append(self.get_app_config(section, items))

        f = open(config.DB_INI, 'wb')
        f.write(string.join(db_data, '\n'))
        f.write('\n')
        f.close()

    # Convert app dictionary to db.ini format
    def get_app_config(self, app_name, app_config):
        out = []
        out.append('[%s]\n\n' % app_name)
        for field in FIELDS:
            if app_config.has_key(field) and (field == process.APP_FILENAME or app_config[field] != ''):
                out.append('%-15s = %s\n' % (field, re.sub('%', '%%', app_config[field])))
        return string.join(out, '')

    # Convert addon dictionary to db.ini format
    def get_addon_config(self, app_name, app_config):
        out = """
[%s]

category        = %s:%s
describe        = %s
website         = https://addons.mozilla.org/en-US/%s/addon/%s
scrape          = https://addons.mozilla.org/en-US/%s/addons/versions/%s
version         = Version %s.*?file/([0-9]+)/%s(?#-)
download        = https://addons.mozilla.org/en-US/%s/downloads/file/#VERSION[%s]#/
filename        = %s#VERSION[%s]#%s.xpi
upgrades        = true
""" % (
        app_name, 
        app_config['type'].capitalize(), app_config['category'],
        app_config['describe'],
        app_config['type'], app_config['appid'],
        app_config['type'], app_config['appid'],
        app_config['version'], app_config['filestart'],
        app_config['type'], app_config['versionchunk'][-1],
        app_config['filestart'], app_config['versionchunk'], app_config['fileend']
        )

        return out

    # Try app config
    def try_appsnap(self, app_name='', command=''):
        if app_name != '':
            command = '%s -n "%s" %s' % (self.appsnap, app_name, command)
        else:
            command = '%s %s' % (self.appsnap, command)

        print "(%s)" % command.strip()
        while 1:
            print '--------'
            os.system(command)
            print '--------'
            print '> Try again? (y/N) ',
            yn = self.getline()
            if yn != 'y' and yn != 'Y': break
        print

        # Reload app config if changed
        self.reload_app_config(app_name)

    # Reload app config from db.ini
    def reload_app_config(self, app_name):
        self.configuration = config.config() 
        self.apps[app_name] = self.configuration.get_section_items(app_name)

    # Get downloaded filename
    def get_downloaded_filename(self, app_name):
        p = process.process(self.configuration, self.curl_instance, app_name, self.apps[app_name])
        filename = p.replace_version_with_mask(self.apps[app_name][process.APP_FILENAME])
        try: rename = p.replace_version_with_mask(self.apps[app_name][process.APP_RENAME])
        except KeyError: rename = ''
        filemask = self.curl_instance.get_cached_name(filename, rename)

        file = self.get_first_from_mask(filemask)
        if file == '':
            print 'File not downloaded: %s' % filemask
            sys.exit(1)
        print '- Downloaded: %s' % file
        return file

    # Return first file that matches mask
    def get_first_from_mask(self, filemask):
        files = glob.glob(filemask) 
        if len(files) == 0:
            return ''

        return files[0]

    # Set installer type
    def set_installer_type(self, app_name, filename):
        type = ''
        if filename[-3:].lower() == 'msi':
            type = 'MSI'
        elif filename[-3:].lower() == 'xpi':
            type = 'XPI'
        elif filename[-3:].lower() == 'zip':
            type = 'ZIP'

            # Extract ZIP
            print '- Extracted: %s' % filename
            self.apps[app_name][process.APP_INSTALLER] = 'dummy.exe'
            p = process.process(self.configuration, self.curl_instance, app_name, self.apps[app_name])
            p.unzip_file(filename)
            os.startfile(filename[:-4])

            # Get installer
            print '- Enter installer name'
            print '> %-15s: ' % process.APP_INSTALLER,
            self.apps[app_name][process.APP_INSTALLER] = self.getline()
            print

            # Detect installer within ZIP
            if self.apps[app_name][process.APP_INSTALLER] != '':
                instmask = p.replace_version_with_mask(os.path.join(filename[:-4], self.apps[app_name][process.APP_INSTALLER]))
                installer = self.get_first_from_mask(instmask)
                if installer == '':
                    print 'File not extracted: %s' % installer
                    sys.exit(1)
                type = self.detect_installer_type(installer)
        else:
            type = self.detect_installer_type(filename)

        if type == 'MSI':
            self.apps[app_name][process.APP_INSTPARAM] = '/passive /norestart'
            self.apps[app_name][process.APP_UPGRADES] = 'true'
            self.apps[app_name][process.APP_UNINSTPARAM] = '/passive /norestart'
        elif type == 'XPI':
            self.apps[app_name][process.APP_UPGRADES] = 'true'
        elif type == 'ZIP':
            self.apps[app_name][process.APP_UPGRADES] = 'false'
        elif type == 'Inno':
            self.apps[app_name][process.APP_INSTPARAM] = '/sp- /silent /norestart'
            self.apps[app_name][process.APP_UPGRADES] = 'true'
            self.apps[app_name][process.APP_CHINSTDIR] = '/dir="#INSTALL_DIR#"'
            self.apps[app_name][process.APP_UNINSTPARAM] = '/sp- /silent /norestart'
        elif type == 'NSIS':
            self.apps[app_name][process.APP_INSTPARAM] = '/S'
            self.apps[app_name][process.APP_UPGRADES] = 'false'
            self.apps[app_name][process.APP_CHINSTDIR] = '/D=#INSTALL_DIR#'
            self.apps[app_name][process.APP_UNINSTPARAM] = '/S _?=#INSTALL_DIR#'
        elif type == 'MSIEXE':
            self.apps[app_name][process.APP_INSTPARAM] = '/S /v/qb'
            self.apps[app_name][process.APP_UPGRADES] = 'true'
            self.apps[app_name][process.APP_UNINSTPARAM] = '/passive /norestart'
        elif type == 'BITROCK':
            self.apps[app_name][process.APP_INSTPARAM] = '--mode unattended'
            self.apps[app_name][process.APP_CHINSTDIR] = '--prefix "#INSTALL_DIR#"'
            self.apps[app_name][process.APP_UPGRADES] = 'false'
            self.apps[app_name][process.APP_UNINSTPARAM] = '--mode unattended'

        print '- Installer type: %s' % type

    # Detect the installer type
    def detect_installer_type(self, filename):
        f = open(filename, 'rb')
        data = f.read()
        f.close()

        if data.find('Inno') != -1:
            return 'Inno'
        elif data.find('NSIS') != -1:
            return 'NSIS'
        elif data.find('MSI') != -1:
            return 'MSIEXE'
        elif data.find('BitRock') != -1:
            return 'BITROCK'
        return ''
