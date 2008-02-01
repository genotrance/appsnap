import config
import ConfigParser
import glob
import os
import os.path
import process
import re
import string
import StringIO
import strings
import sys
import version

# Return codes
SUCCESS = 0
CHANGED = 1
UNCHANGED = 2
NEW_BUILD = 3

READ_ERROR = -1
WRITE_ERROR = -2
DOWNLOAD_FAILURE = -3

# Keys
CHANGED = 'changed'
DATA = 'data'
ETAG = 'etag'
LOCAL = 'local'
REMOTE = 'remote'
URL = 'url'

# Directories
APPSNAPLIB_DIR = 'appsnaplib'
LOCALE_DIR = 'locale'

# Files
VERSION_DAT = 'version.dat'

# Update AppSnap and database
class update:
    # Constructor
    def __init__(self, configuration, curl_instance, check_only=False, database_only=False):
        # Initialize
        self.configuration = configuration
        self.curl_instance = curl_instance
        self.check_only = check_only
        self.database_only = database_only

        self.versions = self.load_versions()
        self.newversions = []

    # Download remote DBs and concatenate
    def download_database(self):
        db_ini = ''
        db_urls = self.configuration.database[config.LOCATION].split(',')
        for i in range(len(db_urls)):
            db_urls[i] = re.sub(process.VERSION, version.APPVERSION, db_urls[i])
            db_data = self.curl_instance.get_web_data(db_urls[i])
            if db_data != None:
                db_ini += db_data
                if i < len(db_urls)-1:
                    db_ini += '\n\n'
        
        # Test downloaded content
        if db_ini != '':
            try:
                test_db = ConfigParser.SafeConfigParser()
                test_db.readfp(StringIO.StringIO(db_ini))
            except:
                db_ini = ''
        
        return db_ini
    
    # Download, compare and update DB as needed
    def update_database(self):
        # Get local db data
        if os.path.exists(config.DB_INI):
            try:
                local_db = open(config.DB_INI, 'rb')
                local_db_data = local_db.read()
                local_db.close()
            except IOError:
                return READ_ERROR
        else:
            local_db_data = ''
        
        # Get remote db data
        remote_db_data = self.download_database()
        
        # Fail if empty DB
        if remote_db_data == '':
            return DOWNLOAD_FAILURE
        
        if local_db_data != remote_db_data:
            if self.check_only == True:
                return CHANGED

            # Update the DB file
            try:
                local_db = open(config.DB_INI, 'wb')
                local_db.write(remote_db_data)
                local_db.close()
                self.configuration.copy_database_to_cache(True)
                return SUCCESS
            except IOError:
                return WRITE_ERROR
        else:
            return UNCHANGED

    # Convert \r\n to \n
    def remove_cr(self, data):
        return re.sub('\r\n', '\n', data)

    # Check if module data is valid
    def check_module(self, data):
        data = self.remove_cr(data)
        try:
            compile(data, '<string>', 'exec')
        except:
            return DOWNLOAD_FAILURE
        
        return SUCCESS

    # Update specified files
    def update_files(self, version_url, path, files):
        list = {}
        for file in files:
            list[file] = {}
            list[file][CHANGED] = False

            # URLs
            list[file][LOCAL+URL] = os.path.join(path, file)
            list[file][REMOTE+URL] = string.join([version_url, path, file], '/')

            # Check ETag
            list[file][ETAG] = self.curl_instance.get_web_etag(list[file][REMOTE+URL])
            if list[file][ETAG] != None: self.newversions.append(list[file][ETAG] + '\r\n')
            if self.search_version(list[file][ETAG]) == False:
                # ETag missing or changed, download content
                list[file][REMOTE+DATA] = self.curl_instance.get_web_data(list[file][REMOTE+URL])
                if list[file][REMOTE+DATA] == None or (file[-3] == '.py' and self.check_module(list[file][REMOTE+DATA]) != SUCCESS):
                    # Unable to download or not Python module
                    return DOWNLOAD_FAILURE

                if list[file][ETAG] != None and self.search_version(file) == True:
                    # ETag changed so file has changed
                    list[file][CHANGED] = True
                else:
                    # Check if data has changed, no cached ETag
                    if os.path.exists(list[file][LOCAL+URL]):
                        # Get local data
                        try:
                            fp = open(list[file][LOCAL+URL], 'rb')
                            data = fp.read()
                            fp.close()
                        except IOError:
                            return READ_ERROR
                        
                        if list[file][REMOTE+DATA] != data:
                            # Different from remote data
                            list[file][CHANGED] = True
                    else:
                        # File does not exist yet
                        list[file][CHANGED] = True

                if list[file][CHANGED] == True and self.check_only == True:
                    # Return CHANGED since check_only
                    return CHANGED

        # Check if anything has changed
        changed = False
        for file in files:
            if list[file][CHANGED] == True:
                changed = True
                break
        
        # Update files since something changed
        if changed == True:
            for file in files:
                # Update contents if changed
                if list[file][CHANGED] == True:
                    # Create directory if missing
                    dir = os.path.dirname(list[file][LOCAL+URL])
                    if not os.path.exists(dir):
                        try:
                            os.makedirs(dir)
                        except:
                            pass

                    # Put remote data
                    try:
                        fp = open(list[file][LOCAL+URL], 'wb')
                        fp.write(list[file][REMOTE+DATA])
                        fp.close()
                    except IOError:
                        return WRITE_ERROR

        # Delete any obsolete modules
#        for file in glob.glob(APPSNAPLIB_DIR + os.path.sep + '*.py'):
#            if os.path.basename(file) not in files:
#                changed = True
#                try: os.remove(file)
#                except WindowsError: pass

        # Return code     
        if changed == True:
            return SUCCESS
        else:
            return UNCHANGED

    # Build locale file list
    def build_locale_file_list(self, locales):
        files = []
        for locale in locales:
            files.append(string.join([locale, 'LC_MESSAGES', 'appsnap.po'], '/'))
            files.append(string.join([locale, 'LC_MESSAGES', 'appsnap.mo'], '/'))
        return files

    # Download, compare and update AppSnap as needed
    def update_appsnap(self):
        # Download version.py for new version information
        version_url = self.configuration.update[config.LOCATION]
        version_data = self.curl_instance.get_web_data(version_url + '/' + APPSNAPLIB_DIR + '/version.py')
        
        if version_data == None:
            return DOWNLOAD_FAILURE
        
        # Load version.py
        try:
            exec(self.remove_cr(version_data))
        except:
            return DOWNLOAD_FAILURE
        
        # Check minimum build version
        if BLDVERSION > version.BLDVERSION:
            return NEW_BUILD
        
        # Save return values
        returned = []
        
        # Update database
        ret = self.update_database()
        if ret not in [SUCCESS, UNCHANGED]: return ret
        returned.append(ret)

        if not self.database_only:
            # Update appsnaplib
            ret = self.update_files(version_url, APPSNAPLIB_DIR, FILES)
            if ret not in [SUCCESS, UNCHANGED]: return ret
            returned.append(ret)

            # Update misc components
            ret = self.update_files(version_url, '', MISC)
            if ret not in [SUCCESS, UNCHANGED]: return ret
            returned.append(ret)
            
            # Update locales        
            ret = self.update_files(version_url, LOCALE_DIR, self.build_locale_file_list(LOCALES))
            if ret not in [SUCCESS, UNCHANGED]: return ret
            returned.append(ret)
        
        # Save versions for SUCCESS and UNCHANGED
        if self.versions != self.newversions: self.save_versions(self.newversions)

        # Return SUCCESS if anything changed
        if SUCCESS in returned:
            return SUCCESS
        else:
            return UNCHANGED

    # Load version.dat
    def load_versions(self):
        try:
            f = open(VERSION_DAT, 'rb')
            versions = f.readlines()
            versions.sort()
            f.close()
        except IOError:
            versions = []

        return versions

    # Save version.dat
    def save_versions(self, versions):
        try:
            f = open(VERSION_DAT, 'wb')
            versions.sort()
            f.writelines(versions)
            f.close()

            self.versions = versions
            self.newversions = []
        except IOError:
            pass

    # Look for string in version.dat
    def search_version(self, str):
        for version in self.versions:
            if version.find(str) != -1:
                return True
        return False
