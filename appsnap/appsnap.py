# Import required libraries
import config
import curl
import getopt
import process
import sys
import threading
import version

header = version.APPNAME + ' ' + version.APPVERSION + '\n'

help = header + """
Global functions
-h             This help screen
-c             List all application categories
-l             List supported applications
   -f <cat>    Filter list by category
-U             Update database

Application specific functions
-n <name>      One or more application names, comma separated
   -d          Download application
   -g          Get latest version       (DEFAULT)
   -i          Install latest version   (implies -d)
   -u          Upgrade current version  (implies -i, -x if not upgradeable)
   -x          Uninstall current version
"""

def do_action(configuration, curl_instance, lock, name, getversion, download, install, upgrade, uninstall):
    items = configuration.get_section_items(name)
    if items != None:
        p = process.process(configuration, curl_instance, name, items)
        
        if getversion == True:
            output = '\n'
            output += 'Application       : ' + name + '\n'
            output += 'Description       : ' + items['describe'] + '\n'
            output += 'Website           : ' + items['website'] + '\n'
            output += 'Latest Version    : ' + p.get_latest_version() + '\n'
            installed = configuration.get_installed_version(name)
            if installed != '':
                output += 'Installed Version : ' + installed + '\n'
            print output
        if download == True:
            print '-> Downloading ' + name
            if p.download_latest_version() == False:
                print "-> Download failed for " + name
                return
            else:
                print "-> Download succeeded for " + name
        if install == True:
            print '-> Installing ' + name
            lock.acquire()
            if p.install_latest_version() == False: 
                print "-> Install failed for " + name
                lock.release()
                return
            else:
                print "-> Install succeeded for " + name
            lock.release()
        if upgrade == True:
            print '-> Upgrading ' + name
            lock.acquire()
            if p.upgrade_version() == False: 
                print "-> Upgrade failed for " + name
                lock.release()
                return
            else:
                print "-> Upgrade succeeded for " + name
            lock.release()
        if uninstall == True:
            print '-> Uninstalling ' + name
            lock.acquire()
            if p.uninstall_version() == False: 
                print "-> Uninstall failed for " + name
                lock.release()
                return
            else:
                print "-> Uninstall succeeded for " + name
            lock.release()
    else:
        print 'No such application: ' + name
        
if __name__ == '__main__':
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'cdf:ghiln:uUx')
    except getopt.GetoptError:
        print help
        sys.exit(2)

    # Set defaults
    names = None
    filter = ''
    categories = False
    download = False
    getversion = True
    install = False
    list = False
    upgrade = False
    uninstall = False
    updatedb = False

    for o, a in opts:
        if o == '-c': categories = True
        if o == '-d': download = True
        if o == '-f': filter = a
        if o == '-g': getversion = True
        if o == '-h':
            print help
            sys.exit()
        if o == '-i': install = True
        if o == '-l': list = True
        if o == '-n': names = a.split(',')
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
        configuration.display_available_sections(filter)
        sys.exit()

    # Update database if requested
    if updatedb == True:
        print 'Updating database...'
        remote = curl_instance.get_web_data(configuration.database['location'])
        local = open(config.DB, 'rb').read()
        if local != remote:
            # Update the DB file
            try:
                db = open(config.DB, 'wb')
                db.write(remote)
                db.close()
                print 'Updated!'
            except IOError:
                print 'Update Failed. Unable to write to db.ini'
        else:
            print 'No changes.'
        sys.exit()

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
                                                         uninstall])
        children.append(child)
        child.start()