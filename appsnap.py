# Import required libraries
import codecs
import config
import curl
import defines
import getopt
import process
import strings
import sys
import threading
import version
import wx

# Detect the locale and set the output encoding appropriately
locale = wx.Locale(wx.LANGUAGE_DEFAULT).GetName()
if locale[:2] == 'da':
    encoding = 'cp850'
elif locale[:2] == 'bg':
    encoding = 'cp1251'
else:
    encoding = ''

if encoding:
    sys.stdout = codecs.getwriter(encoding)(sys.stdout, 'replace')

header = version.APPNAME + ' ' + version.APPVERSION + '\n'

help = header + """
%s
-h\t\t\t%s
-c\t\t\t%s
-l\t\t\t%s
   -f <%s>\t%s
   -s <%s>\t\t%s
-U\t\t\t%s

%s
-n <%s>\t\t%s
   -f <%s>\t%s
   -s <%s>\t\t%s

   -d\t\t\t%s
      -t\t\t%s
   -g\t\t\t%s (%s)
   -i\t\t\t%s (%s)
   -u\t\t\t%s (%s)
   -x\t\t\t%s
""" % (
       strings.GLOBAL_FUNCTIONS,
       strings.THIS_HELP_SCREEN,
       strings.LIST_ALL_APPLICATION_CATEGORIES,
       strings.LIST_SUPPORTED_APPLICATIONS,
       strings.CATEGORY,
       strings.FILTER_LIST_BY_CATEGORY,
       strings.STRING,
       strings.FILTER_LIST_BY_STRING,
       strings.UPDATE_DB_DESCRIPTION,
       strings.APPLICATION_SPECIFIC_FUNCTIONS,
       strings.NAME,
       strings.APPLICATION_NAME_DESCRIPTION,
       strings.CATEGORY,
       strings.FILTER_APP_BY_CATEGORY,
       strings.STRING,
       strings.FILTER_APP_BY_STRING,
       strings.DOWNLOAD_DESCRIPTION,
       strings.TEST_DOWNLOAD_ONLY,
       strings.GET_LATEST_VERSION,
       strings.DEFAULT,
       strings.INSTALL_DESCRIPTION,
       strings.INSTALL_IMPLICATION,
       strings.UPGRADE_DESCRIPTION,
       strings.UPDATE_IMPLICATION,
       strings.UNINSTALL_DESCRIPTION
       )

# Perform an action on the specified application
def do_action(configuration, curl_instance, lock, name, getversion, download, install, upgrade, uninstall, test):
    items = configuration.get_section_items(name)
    if items != None:
        p = process.process(configuration, curl_instance, name, items)
        
        if getversion == True:
            output = '\n'
            output += strings.APPLICATION + ' : ' + name + '\n'
            output += strings.DESCRIPTION + ' : ' + items[process.APP_DESCRIBE] + '\n'
            output += strings.WEBSITE + ' : ' + items[process.APP_WEBSITE] + '\n'
            latest_version = p.get_latest_version()
            if latest_version == None:
                latest_version = strings.FAILED_TO_CONNECT
            output += strings.LATEST_VERSION + ' : ' + latest_version + '\n'
            installed = configuration.get_installed_version(name)
            if installed != '':
                output += strings.INSTALLED_VERSION + ' : ' + installed + '\n'
            print output
        if download == True:
            print '-> ' + strings.DOWNLOADING + ' ' + name,
            if test: print ' (' + strings.TESTING + ')'
            else: print
            if p.download_latest_version(None, test) == False:
                print '-> ' + strings.DOWNLOAD_FAILED + ' : ' + name
                return
            else:
                print '-> ' + strings.DOWNLOAD_SUCCEEDED + ' : ' + name
        if install == True:
            print '-> ' + strings.INSTALLING + ' ' + name
            lock.acquire()
            if p.install_latest_version() == False: 
                print '-> ' + strings.INSTALL_FAILED + ' : ' + name
                lock.release()
                return
            else:
                print '-> ' + strings.INSTALL_SUCCEEDED + ' : ' + name
            lock.release()
        if upgrade == True:
            print '-> ' + strings.UPGRADING + ' : ' + name
            lock.acquire()
            if p.upgrade_version() == False: 
                print '-> ' + strings.UPGRADE_FAILED + ' : ' + name
                lock.release()
                return
            else:
                print '-> ' + strings.UPGRADE_SUCCEEDED + ' : ' + name
            lock.release()
        if uninstall == True:
            print '-> ' + strings.UNINSTALLING + ' : ' + name
            lock.acquire()
            if p.uninstall_version() == False: 
                print '-> ' + strings.UNINSTALL_FAILED + ' : ' + name
                lock.release()
                return
            else:
                print '-> ' + strings.UNINSTALL_SUCCEEDED + ' : ' + name
            lock.release()
    else:
        print strings.NO_SUCH_APPLICATION + ' : ' + name

if __name__ == '__main__':
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'cdf:ghiln:s:tuUx')
    except getopt.GetoptError:
        print help
        sys.exit(defines.ERROR_GETOPT)

    # Set defaults
    names = None
    categoryfilter = ''
    stringfilter = ''
    categories = False
    download = False
    getversion = True
    install = False
    list = False
    upgrade = False
    uninstall = False
    updatedb = False
    test = False

    for o, a in opts:
        if o == '-c': categories = True
        if o == '-d': download = True
        if o == '-f': categoryfilter = a
        if o == '-g': getversion = True
        if o == '-h':
            print help
            sys.exit(defines.ERROR_HELP)
        if o == '-i': install = True
        if o == '-l': list = True
        if o == '-n': names = a.split(',')
        if o == '-s': stringfilter = a
        if o == '-t': test = True
        if o == '-u': upgrade = True
        if o == '-U': updatedb = True
        if o == '-x': uninstall = True

    # If no application specified, exit
    if names == None and list == False and categories == False and updatedb == False:
        print help
        sys.exit(defines.ERROR_NO_OPTIONS_SPECIFIED)

    # Print application header
    print header

    # Load the configuration
    configuration = config.config()

    # Create a pycurl instance
    curl_instance = curl.curl(configuration)

    # List applications if requested
    if categories == True:
        configuration.display_categories()
        sys.exit(defines.ERROR_SUCCESS)
    elif list == True:
        configuration.display_available_sections(categoryfilter, stringfilter)
        sys.exit(defines.ERROR_SUCCESS)

    # Update database if requested
    if updatedb == True:
        print '-> ' + strings.UPDATING_DATABASE
        remote = curl_instance.get_web_data(configuration.database[config.LOCATION] + '/?version=' + version.APPVERSION)
        local = open(config.DB_INI, 'rb').read()
        if local != remote:
            # Update the DB file
            try:
                db = open(config.DB_INI, 'wb')
                db.write(remote)
                db.close()
                configuration.copy_database_to_cache(True)
                print '-> ' + strings.UPDATE_DATABASE_SUCCEEDED
            except IOError:
                print '-> ' + strings.UPDATE_DATABASE_FAILED + '. ' + strings.UNABLE_TO_WRITE_DB_INI
        else:
            print '-> ' + strings.NO_CHANGES_FOUND
        sys.exit(defines.ERROR_SUCCESS)

    # Figure out applications selected
    if len(names) == 1 and names[0] == '*':
        if categoryfilter == '':
            names = configuration.get_sections()
        else:
            print strings.CATEGORY + ' : ' + categoryfilter
            names = configuration.get_sections_by_category(categoryfilter)

        if stringfilter != '':
            print strings.FILTER + ' : ' + stringfilter + '\n'
            names = configuration.filter_sections_by_string(names, stringfilter)
        else:
            print
            
    # Perform actions for each application specified
    children = []
    lock = threading.Lock()
    for name in names:
        curl_instance.limit_threads(children)
        
        child = threading.Thread(target=do_action, args=[configuration, 
                                                         curl_instance, 
                                                         lock, 
                                                         name, 
                                                         getversion, 
                                                         download, 
                                                         install, 
                                                         upgrade, 
                                                         uninstall,
                                                         test])
        children.append(child)
        child.start()