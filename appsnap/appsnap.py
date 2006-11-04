# Import required libraries
import process
import config
import sys
import curl
import getopt
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
            print 'Updated!'
            db = open(config.DB, 'wb')
            db.write(remote)
            db.close()
        else:
            print 'No changes.'
        sys.exit()

    # Perform actions for each application specified
    for name in names:
        items = configuration.get_section_items(name)
        if items != None:
            p = process.process(configuration, curl_instance, name, items)

            if getversion == True:
                print 'Application    : ' + name
                print 'Description    : ' + items['describe']
                print 'Website        : ' + items['website']
                print 'Latest Version : ' + p.get_latest_version()
                print ''
            if download == True:
                print 'Downloading...'
                if p.download_latest_version() == False: print "  Download failed"
            if install == True:
                print 'Installing...'
                if p.install_latest_version() == False: print "  Install failed"
            if upgrade == True:
                print 'Upgrading...'
                if p.upgrade_version() == False: print "  Upgrade failed"
            if uninstall == True:
                print 'Uninstalling...'
                if p.uninstall_version() == False: print "  Uninstall failed"
        else:
            print 'No such application: ' + name