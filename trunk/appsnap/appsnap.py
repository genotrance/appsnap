# Import required libraries
import config
import curl
import getopt
import process
import strings
import sys
import threading
import version

header = version.APPNAME + ' ' + version.APPVERSION + '\n'

help = header + strings.COMMANDLINE_HELP

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
        sys.exit(2)

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
            sys.exit()
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
        sys.exit()

    # Print application header
    print header

    # Load the configuration
    configuration = config.config()

    # Create a pycurl instance
    curl_instance = curl.curl(configuration)

    # List applications if requested
    if categories == True:
        configuration.display_categories()
        sys.exit()
    elif list == True:
        configuration.display_available_sections(categoryfilter, stringfilter)
        sys.exit()

    # Update database if requested
    if updatedb == True:
        print '-> ' + strings.UPDATING_DATABASE
        remote = curl_instance.get_web_data(configuration.database[config.LOCATION])
        local = open(config.DB, 'rb').read()
        if local != remote:
            # Update the DB file
            try:
                db = open(config.DB, 'wb')
                db.write(remote)
                db.close()
                configuration.copy_database_to_cache(True)
                print '-> ' + strings.UPDATE_DATABASE_SUCCEEDED
            except IOError:
                print '-> ' + strings.UPDATE_DATABASE_FAILED + '. ' + strings.UNABLE_TO_WRITE_DB_INI
        else:
            print '-> ' + strings.NO_CHANGES_FOUND
        sys.exit()

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