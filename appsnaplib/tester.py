import os
import random
import re
import shutil
import string
import sys
import threading
import time
import types
import unittest

import cli, config, curl, process, update, version


class configTest(unittest.TestCase):
    def setUp(self):
        self.config = config.config()

    def test_config(self):
        cfg = config.config()
        assert cfg != None

    def test_get_sections(self):
        sections = self.config.get_sections()
        assert type(sections) == types.ListType and len(sections) > 0

    def test_get_section_items(self):
        sections = self.config.get_sections()
        for section in sections:
            items = self.config.get_section_items(section)
            assert items != None, section

    def test_get_categories(self):
        categories = self.config.get_categories()
        assert type(categories) == types.ListType and len(categories) > 0

    def test_get_sections_by_category(self):
        categories = self.config.get_categories()
        for category in categories:
            sections = self.config.get_sections_by_category(category)
            assert type(sections) == types.ListType and len(sections) > 0

    def test_filter_sections_by_string(self):
        sections = self.config.get_sections()
        fsections = self.config.filter_sections_by_string(sections, 'Fire')
        assert type(fsections) == types.ListType and len(fsections) > 0

        fsections = self.config.filter_sections_by_string(sections, '1YxYsdas1034')
        assert type(fsections) == types.ListType and len(fsections) == 0

    def test_display(self):
        self.config.display_categories()
        self.config.display_available_sections()
        self.config.display_available_sections(category='Development')
        self.config.display_available_sections(category='Development', string='Py')
        self.config.display_available_sections(string='Fire')
        self.config.display_available_sections(category='Nonexistant')
        self.config.display_available_sections(string='12847312487c12341cjh')

    def test_installed_version(self):
        section = 'Doggy'
        version = '12345'
        assert self.config.get_installed_version(section) == ''
        self.config.add_installed_version(section, version)
        self.config.save_installed_version(section, version)
        assert self.config.get_installed_version(section) == version
        self.config.delete_installed_version(section)

    def test_cached_latest_version(self):
        section = 'Doggy'
        version = '12345'
        assert self.config.get_cached_latest_version(section) == None
        self.config.save_cached_latest_version(section, version)
        assert self.config.get_cached_latest_version(section) == version

        self.config.lock.acquire()
        self.config.latest.remove_section(section)
        inifile = open(self.config.latest_ini, 'w')
        self.config.latest.write(inifile)
        inifile.close()
        self.config.lock.release()

    def test_load_arp(self):
        arp = self.config.load_arp()
        assert type(arp) == types.DictType and len(arp) > 0

    def test_get_arp_sections(self):
        arp = self.config.get_arp_sections()
        assert type(arp) == types.ListType and len(arp) > 0

    def test_get_arp_section_items(self):
        arp = self.config.load_arp()
        for a in arp:
            assert self.config.get_arp_section_items(a) != None

    def tearDown(self):
        self.config = None

class curlTest(unittest.TestCase):
    def setUp(self):
        self.curlInstance = curl.curl(config.config())

    def test_get_web_headers(self):
        assert len(self.curlInstance.get_web_header('http://appsnap.googlecode.com/svn/trunk/appsnap/build.py')) > 0

    def test_get_web_etag(self):
        assert self.curlInstance.get_web_etag('http://appsnap.googlecode.com/svn/trunk/appsnap/build.py') != None
        assert self.curlInstance.get_web_etag('http://www.google.com') == None

    def test_get_web_timestamp(self):
        assert type(self.curlInstance.get_web_timestamp('http://appsnap.googlecode.com/svn/trunk/appsnap/build.py')) == types.FloatType
        assert self.curlInstance.get_web_timestamp('http://www.google.com') == None

    def test_get_web_data(self):
        assert self.curlInstance.get_web_data('http://appsnap.googlecode.com/svn/trunk/appsnap/build.py') != None
        assert self.curlInstance.get_web_data('http://www.google.com') != None
        assert self.curlInstance.get_web_data('http://127.0.0.1:5511') == None

    def test_download_web_data(self):
        assert self.curlInstance.download_web_data('http://www.google.com', 'index.html', 'http://images.google.com', lambda a,b,c,d: 0, False) == True
        assert self.curlInstance.download_web_data('http://www.google.com', 'index.html', '', lambda a,b,c,d: 0, False) == True
        assert self.curlInstance.download_web_data('http://www.google.com', 'index.html', '', None, False) == True
        os.remove('index.html')
        assert self.curlInstance.download_web_data('http://www.google.com', 'index.html', 'http://images.google.com', lambda a,b,c,d: 0, True) == True
        assert self.curlInstance.download_web_data('http://www.google.com', 'index.html', '', lambda a,b,c,d: 0, True) == True
        assert self.curlInstance.download_web_data('http://www.google.com', 'index.html', '', None, True) == True

    def tearDown(self):
        self.curlInstance = None

class processTest(unittest.TestCase):
    def setUp(self):
        self.config = config.config()
        self.curlInstance = curl.curl(self.config)

        self.failed = []

    def test_process_constructor(self):
        apps = self.config.get_sections()
        for app in apps:
            p = process.process(self.config, self.curlInstance, app, self.config.get_section_items(app))
            assert p != None

    def test_check_version_and_download(self):
        apps = self.config.get_sections()
        self.process_loop(apps, self.check_version_and_download)
        assert len(self.failed) == 0, self.printable_failed()

    def check_version_and_download(self, p):
        installed = p.get_installed_version()
        instdir = p.get_install_dir()

        if p.get_latest_version(True) == None \
        or p.download_latest_version(cli.display_download_status, True) == False:
            self.failed.append(p.app)

    def test_check_install_uninstall(self):
        apps = self.config.get_sections()
        random.shuffle(apps)
        apps = apps[:3]
        self.process_loop(apps, self.check_install_uninstall)
        assert len(self.failed) == 0, self.printable_failed()

    def check_install_uninstall(self, p):
        if p.download_latest_version(cli.display_download_status) == False:
            self.failed.append('Download failed: %s' % p.app)
        elif p.install_latest_version() == False:
            self.failed.append('Install failed: %s' % p.app)
        elif p.app_config.has_key(process.APP_INSTVERSION) and p.get_installed_version() == '':
            self.failed.append('Instversion failed: %s' % p.app)
        elif p.app_config.has_key(process.APP_INSTDIR) and p.get_install_dir() == '':
            self.failed.append('Instdir failed: %s' % p.app)
        elif p.app_config.has_key(process.APP_UNINSTALL) and p.parse_uninstall_entry()[0] == '':
            self.failed.append('Uninstall key failed: %s' % p.app)
        elif p.app_config.has_key(process.APP_UNINSTALL) and p.get_uninstall_string(p.parse_uninstall_entry()[0], p.get_installed_version()) == '':
            self.failed.append('Uninstall string failed: %s' % p.app)
        elif p.uninstall_version() == False:
            self.failed.append('Uninstall failed: %s' % p.app)

    def process_loop(self, apps, helper):
        children = []
        for app in apps:
            self.curlInstance.limit_threads(children)

            p = process.process(self.config, self.curlInstance, app, self.config.get_section_items(app))
            child = threading.Thread(target=helper, args=[p]) 
            children.append(child)
            child.start()

        self.curlInstance.clear_threads(children)

    def printable_failed(self):
        out = ['\nFailed applications']
        for f in self.failed:
            out.append('  ' + f)
        return string.join(out, '\n')

    def tearDown(self):
        self.config = None
        self.curlInstance = None

class updateTest(unittest.TestCase):
    def setUp(self):
        # Create test directory
        self.test_dir = 'test_dir'
        try: os.mkdir(self.test_dir)
        except WindowsError: pass
        os.chdir(self.test_dir)
        
        # Copy config.ini
        shutil.copyfile(os.path.join('..', config.CONFIG_INI), config.CONFIG_INI)

        # Setup
        self.config = config.config()
        self.curlInstance = curl.curl(self.config)
        self.version_url = self.config.update[config.LOCATION]
        self.update_obj = update.update(self.config, self.curlInstance, True)

        # Load remote version.py
        version_data = self.curlInstance.get_web_data(string.join([self.version_url, update.APPSNAPLIB_DIR, 'version.py'], '/'))
        assert version_data != None
        try: exec(self.update_obj.remove_cr(version_data))
        except: assert 1 == 0

        # Create subdirs
        self.dirs = [update.APPSNAPLIB_DIR]
        for locale in LOCALES:
            self.dirs.append(os.path.join(update.LOCALE_DIR, locale, 'LC_MESSAGES'))
        for dir in self.dirs:
            try: os.makedirs(dir)
            except WindowsError: pass

        # Download release
        for file in FILES:
            self.curlInstance.download_web_data(string.join([self.version_url, update.APPSNAPLIB_DIR, file], '/'), os.path.join(update.APPSNAPLIB_DIR, file), '')

        for file in MISC:
            self.curlInstance.download_web_data(string.join([self.version_url, file], '/'), file, '')

        for locale in LOCALES:
            for file in ['appsnap.po', 'appsnap.mo']:
                self.curlInstance.download_web_data(string.join([self.version_url, update.LOCALE_DIR, locale, 'LC_MESSAGES', file], '/'), \
                    os.path.join(update.LOCALE_DIR, locale, 'LC_MESSAGES', file), '')

    def test_all(self):
        # Download database
        db_ini = self.update_obj.download_database()
        assert db_ini != ''

        # Save database
        f = open(config.DB_INI, 'wb')
        f.write(db_ini)
        f.close()

        ###
        ###
        # Check only

        ###
        # Same data

        # No ETags, return UNCHANGED, create versions.dat
        try: os.remove(update.VERSION_DAT)
        except: pass

        self.reinit()
        ping = time.clock()
        assert self.update_obj.update_appsnap() == update.UNCHANGED
        noetag_time = time.clock() - ping
        assert os.path.exists(update.VERSION_DAT) == True
        assert os.stat(update.VERSION_DAT).st_size != 0
        print 'Same, No ETag time: %.2f' % noetag_time

        # With ETags, return UNCHANGED, faster
        self.reinit()
        ping = time.clock()
        assert self.update_obj.update_appsnap() == update.UNCHANGED
        etag_time = time.clock() - ping
        assert etag_time < noetag_time
        print 'Same, ETag time: %.2f' % etag_time

        # With bad ETags, return CHANGED, fastest, versions.dat unchanged
        shutil.copyfile(update.VERSION_DAT, update.VERSION_DAT + '.bak')
        versions = self.update_obj.load_versions()
        for i in range(len(versions)):
            versions[i] = '"100%s' % versions[i][4:]
        self.update_obj.save_versions(versions)

        self.reinit()
        ping = time.clock()
        assert self.update_obj.update_appsnap() == update.CHANGED
        badetag_time = time.clock() - ping
        assert badetag_time < etag_time < noetag_time
        newversions = self.update_obj.load_versions()
        assert newversions == versions
        print 'Same, Bad ETag time: %.2f' % badetag_time

        ###
        # Diff data

        # No ETags, return CHANGED, no versions.dat
        os.remove(update.VERSION_DAT)
        os.remove(update.VERSION_DAT + '.bak')
        f = open('appsnap.html', 'ab')
        f.write('<!-- Dummy Data -->')
        f.close()

        self.reinit()
        ping = time.clock()
        assert self.update_obj.update_appsnap() == update.CHANGED
        assert os.path.exists(update.VERSION_DAT) == False
        dnoetag_time = time.clock() - ping
        print 'Diff, No ETag time: %.2f' % dnoetag_time

        ###
        ###
        # Actually update
        self.update_obj.check_only = False

        # No ETags, return SUCCESS, create versions.dat 
        self.reinit()
        ping = time.clock()
        assert self.update_obj.update_appsnap() == update.SUCCESS
        cnoetag_time = time.clock() - ping
        assert os.path.exists(update.VERSION_DAT) == True
        print 'Change+Diff, No ETag time: %.2f' % cnoetag_time

        # No ETags, return UNCHANGED, create versions.dat
        os.remove(update.VERSION_DAT)
        self.reinit()
        ping = time.clock()
        assert self.update_obj.update_appsnap() == update.UNCHANGED
        cunoetag_time = time.clock() - ping
        assert os.path.exists(update.VERSION_DAT) == True
        print 'Change+Same, No ETag time: %.2f' % cunoetag_time

    def reinit(self):
        self.curlInstance.headers = {}
        self.update_obj.versions = self.update_obj.load_versions()
        self.update_obj.newversions = []

    def tearDown(self):
        # Delete test directory
        os.chdir('..')
        shutil.rmtree(self.test_dir, True)

def do_test():
    import tester
    if len(sys.argv) > 2:
        names = sys.argv[2:]
        suite = unittest.TestLoader().loadTestsFromNames(names, tester)
    else:
        suite = unittest.TestLoader().loadTestsFromModule(tester)
    unittest.TextTestRunner(verbosity=2).run(suite)
