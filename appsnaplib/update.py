import config
import ConfigParser
import glob
import os
import os.path
import process
import re
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
PODATA = 'podata'
MODATA = 'modata'
TARGET = 'target'
POTARGET = 'potarget'
MOTARGET = 'motarget'

# Directories
APPSNAPLIB_DIR = 'appsnaplib'
LOCALE_DIR = 'locale'

# Update AppSnap and database
class update:
    # Constructor
    def __init__(self, configuration, curl_instance, check_only=False, database_only=False):
        # Initialize
        self.configuration = configuration
        self.curl_instance = curl_instance
        self.check_only = check_only
        self.database_only = database_only
        
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
        
    # Download, compare and update appsnaplib
    def update_appsnaplib(self, version_url, files):
        # Download appsnaplib
        appsnaplib = {}
        for file in files:
            appsnaplib[file] = {}
            appsnaplib[file][CHANGED] = False
            appsnaplib[file][DATA] = self.curl_instance.get_web_data(version_url + '/' + APPSNAPLIB_DIR + '/' + file)
            if appsnaplib[file][DATA] == None or self.check_module(appsnaplib[file][DATA]) != SUCCESS:
                return DOWNLOAD_FAILURE
            
        # Check if any modules changed
        changed = False
        for file in files:
            appsnaplib[file][TARGET] = os.path.join(APPSNAPLIB_DIR, file)
            if os.path.exists(appsnaplib[file][TARGET]):
                # Get local data
                try:
                    fp = open(appsnaplib[file][TARGET], 'rb')
                    data = fp.read()
                    fp.close()
                except IOError:
                    return READ_ERROR
                
                # Compare with remote data
                if appsnaplib[file][DATA] != data:
                    appsnaplib[file][CHANGED] = True
                    changed = True
            else:
                appsnaplib[file][CHANGED] = True
                changed = True
        
        # Update modules since something changed
        if changed == True:
            if self.check_only == True:
                return CHANGED

            for file in files:
                # Create directory if missing
                dir = os.path.dirname(appsnaplib[file][TARGET])
                if not os.path.exists(dir):
                    try:
                        os.makedirs(dir)
                    except:
                        pass

                # Update module contents
                if appsnaplib[file][CHANGED] == True:
                    # Put remote data
                    try:
                        fp = open(appsnaplib[file][TARGET], 'wb')
                        fp.write(appsnaplib[file][DATA])
                        fp.close()
                    except IOError:
                        return WRITE_ERROR
                    
        # Delete any obsolete modules
        for file in glob.glob(APPSNAPLIB_DIR + os.path.sep + '*.py'):
            if os.path.basename(file) not in files:
                changed = True
                try: os.remove(file)
                except WindowsError: pass
        
        # Return code     
        if changed == True:
            return SUCCESS
        else:
            return UNCHANGED

    # Download, compare and update locales
    def update_locales(self, version_url, locales):
        # Download locales
        locale_data = {}
        for locale in locales:
            locale_data[locale] = {}
            locale_data[locale][CHANGED] = False
            locale_data[locale][PODATA] = self.curl_instance.get_web_data(version_url + '/' + LOCALE_DIR + '/' + locale + '/LC_MESSAGES/appsnap.po')
            locale_data[locale][MODATA] = self.curl_instance.get_web_data(version_url + '/' + LOCALE_DIR + '/' + locale + '/LC_MESSAGES/appsnap.mo')
            if locale_data[locale][PODATA] == None or locale_data[locale][MODATA] == None:
                return DOWNLOAD_FAILURE 
            
        # Check if any locales changed or added
        changed = False
        for locale in locales:
            locale_data[locale][POTARGET] = os.path.join(LOCALE_DIR, locale, 'LC_MESSAGES', 'appsnap.po')
            locale_data[locale][MOTARGET] = os.path.join(LOCALE_DIR, locale, 'LC_MESSAGES', 'appsnap.mo')
            if os.path.exists(locale_data[locale][POTARGET]) and os.path.exists(locale_data[locale][MOTARGET]):
                # Get local data
                try:
                    fp = open(locale_data[locale][POTARGET], 'rb')
                    podata = fp.read()
                    fp.close()
        
                    fp = open(locale_data[locale][MOTARGET], 'rb')
                    modata = fp.read()
                    fp.close()
                except IOError:
                    return READ_ERROR
            
                # Compare with remote data
                if locale_data[locale][PODATA] != podata or locale_data[locale][MODATA] != modata:
                    locale_data[locale][CHANGED] = True
                    changed = True
            else:
                locale_data[locale][CHANGED] = True
                changed = True
                
        # Update locales since something has changed
        if changed == True:
            if self.check_only == True:
                return CHANGED

            for locale in locales:
                # Create directory if missing
                dir = os.path.dirname(locale_data[locale][POTARGET])
                if not os.path.exists(dir):
                    try:
                        os.makedirs(dir)
                    except:
                        pass
                
                # Update locale contents
                if locale_data[locale][CHANGED] == True:
                    # Put remote data
                    try:
                        fp = open(locale_data[locale][POTARGET], 'wb')
                        fp.write(locale_data[locale][PODATA])
                        fp.close()
    
                        fp = open(locale_data[locale][MOTARGET], 'wb')
                        fp.write(locale_data[locale][MODATA])
                        fp.close()
                    except IOError:
                        return WRITE_ERROR
                    
            return SUCCESS
        
        return UNCHANGED
    
    # Download, compare and update misc components
    def update_miscs(self, version_url, miscs):
        # Download misc
        misc_data = {}
        for misc in miscs:
            misc_data[misc] = {}
            misc_data[misc][CHANGED] = False
            misc_data[misc][DATA] = self.curl_instance.get_web_data(version_url + '/' + misc)
            if misc_data[misc][DATA] == None:
                return DOWNLOAD_FAILURE 
            
        # Check if any components changed or added
        changed = False
        for misc in miscs:
            misc_data[misc][TARGET] = misc
            if os.path.exists(misc_data[misc][TARGET]):
                # Get local data
                try:
                    fp = open(misc_data[misc][TARGET], 'rb')
                    data = fp.read()
                    fp.close()
                except IOError:
                    return READ_ERROR
            
                # Compare with remote data
                if misc_data[misc][DATA] != data:
                    misc_data[misc][CHANGED] = True
                    changed = True
            else:
                misc_data[misc][CHANGED] = True
                changed = True
                
        # Update misc components since something has changed
        if changed == True:
            if self.check_only == True:
                return CHANGED

            for misc in miscs:
                # Create directory if missing
                dir = os.path.dirname(misc_data[misc][TARGET])
                if not os.path.exists(dir):
                    try:
                        os.makedirs(dir)
                    except:
                        pass
                
                # Update contents
                if misc_data[misc][CHANGED] == True:
                    # Put remote data
                    try:
                        fp = open(misc_data[misc][TARGET], 'wb')
                        fp.write(misc_data[misc][DATA])
                        fp.close()
                    except IOError:
                        return WRITE_ERROR
                    
            return SUCCESS
        
        return UNCHANGED
        
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
            ret = self.update_appsnaplib(version_url, FILES)
            if ret not in [SUCCESS, UNCHANGED]: return ret
            returned.append(ret)

            # Update misc components
            ret = self.update_miscs(version_url, MISC)
            if ret not in [SUCCESS, UNCHANGED]: return ret
            returned.append(ret)
            
            # Update locales        
            ret = self.update_locales(version_url, LOCALES)
            if ret not in [SUCCESS, UNCHANGED]: return ret
            returned.append(ret)
        
        # Return SUCCESS if anything changed
        if SUCCESS in returned:
            return SUCCESS
        else:
            return UNCHANGED
