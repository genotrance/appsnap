# Import required libraries
import codecs
import config
import curl
import defines
import getopt
import process
import re
import strings
import sys
import threading
import update
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
   -t\t\t\t%s

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
       strings.UPDATE_APPSNAP_DESCRIPTION,
       strings.CHECK_ONLY,
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
       strings.UPGRADE_IMPLICATION,
       strings.UNINSTALL_DESCRIPTION
       )

# Perform an action on the specified application
def do_action(configuration, curl_instance, lock, name, getversion, download, install, upgrade, uninstall, test):
    items = configuration.get_section_items(name)
    if items == None: items = configuration.get_arp_section_items(name + config.ARP_ID)
    if items != None:
        p = process.process(configuration, curl_instance, name, items)
        
        if getversion == True:
            output = '\n'
            output += strings.APPLICATION + ' : ' + name + '\n'
            if items[process.APP_DESCRIBE] != '':
                output += strings.DESCRIPTION + ' : ' + items[process.APP_DESCRIBE] + '\n'
            if items[process.APP_WEBSITE] != '':
                output += strings.WEBSITE + ' : ' + items[process.APP_WEBSITE] + '\n'
            if items[process.APP_CATEGORY] != config.REMOVABLE:
                latest_version = p.get_latest_version()
                if latest_version == None:
                    latest_version = strings.FAILED_TO_CONNECT
                output += strings.LATEST_VERSION + ' : ' + latest_version + '\n'
            installed = p.get_installed_version()
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

# Run the CLI
def appsnap_start():
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'cdf:ghiln:s:tuUvwx')
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
    updateall = False
    wikidump = False
    csvdump = False
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
        if o == '-n': names = [item.strip() for item in a.split(',')]
        if o == '-s': stringfilter = a
        if o == '-t': test = True
        if o == '-u': upgrade = True
        if o == '-U': updateall = True
        if o == '-v': csvdump = True
        if o == '-w': wikidump = True
        if o == '-x': uninstall = True

    # If no application specified, exit
    if names == None and list == False and categories == False and updateall == False and wikidump == False and csvdump == False:
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
        if categoryfilter == config.INSTALLED or categoryfilter == config.NOT_INSTALLED:
            names = configuration.get_sections()
            children = []
            for name in names:
                curl_instance.limit_threads(children)
                items = configuration.get_section_items(name)
                child = threading.Thread(target=process.process, args=[configuration, curl_instance, name, items])
                children.append(child)
                child.start()
        
            # Clear out threads
            curl_instance.clear_threads(children)                

        configuration.display_available_sections(categoryfilter, stringfilter)
        sys.exit(defines.ERROR_SUCCESS)

    # Update AppSnap if requested
    if updateall == True:
        check_only = test
        if check_only == False: print '-> ' + strings.UPDATING_APPSNAP
        else: print '-> ' + strings.CHECKING_FOR_UPDATES
        update_obj = update.update(configuration, curl_instance, check_only)
        returned = update_obj.update_appsnap()
        
        if returned == update.SUCCESS:
            print '-> ' + strings.UPDATE_APPSNAP_SUCCEEDED
        elif returned == update.CHANGED:
            print '-> ' + strings.UPDATES_AVAILABLE
        elif returned == update.UNCHANGED:
            print '-> ' + strings.NO_CHANGES_FOUND
        elif returned == update.NEW_BUILD:
            print '-> ' + strings.NEW_BUILD_REQUIRED
        elif returned == update.READ_ERROR:
            print '-> ' + strings.UPDATE_APPSNAP_FAILED + ' - ' + strings.UNABLE_TO_READ_APPSNAP
        elif returned == update.WRITE_ERROR:
            print '-> ' + strings.UPDATE_APPSNAP_FAILED + ' - ' + strings.UNABLE_TO_WRITE_APPSNAP
        elif returned == update.DOWNLOAD_FAILURE:
            print '-> ' + strings.UPDATE_APPSNAP_FAILED + ' - ' + strings.DOWNLOAD_FAILED
            
        sys.exit(defines.ERROR_SUCCESS)
        
    # Dump application database in wiki format if requested
    if wikidump == True:
        categories = configuration.get_categories()
        num_sections = 0
        for category in categories:
            sections = configuration.get_sections_by_category(category)
            num_sections += len(sections)
            print "!!!" + category + " (" + len(sections).__str__() + ")"
            
            for section in sections:
                items = configuration.get_section_items(section)
                
                print "* [[" + section + "|" + items[process.APP_WEBSITE] + "]] - \"\"\"" + items[process.APP_DESCRIBE] + "\"\"\""
                
        print "!!!Total: " + num_sections.__str__() + " applications in " + len(categories).__str__() + " categories" 
        sys.exit(defines.ERROR_SUCCESS)

    # Dump database in CSV format if requested
    if csvdump == True:
        def quote(str):
            if str == 'true': str = 'Yes'
            elif str == 'false': str = 'No'
            
            if str.find(',') != -1: return '"' + str + '"'
            else: return str
        
        field_names = [
                       'Category', 'Description', 'Website',
                       'Scrape URL', 'Version Regex', 'Download URL',
                       'Download Filename', 'Rename Filename', 'Referer URL',
                       'Installer Filename', 'Install Parameters', 'Installed Version Detection',
                       'Auto Upgrades', 'Change Installdir Parameters', 'Uninstall Entry',
                       'Uninstall Parameters', 'Pre Install Command', 'Post Install Command',
                       'Pre Uninstall Command', 'Post Uninstall Command'
                       ]
        fields = [
                  process.APP_CATEGORY, process.APP_DESCRIBE, process.APP_WEBSITE,
                  process.APP_SCRAPE, process.APP_VERSION, process.APP_DOWNLOAD,
                  process.APP_FILENAME, process.APP_RENAME, process.APP_REFERER,
                  process.APP_INSTALLER, process.APP_INSTPARAM, process.APP_INSTVERSION,
                  process.APP_UPGRADES, process.APP_CHINSTDIR, process.APP_UNINSTALL,
                  process.APP_UNINSTPARAM, process.APP_PREINSTALL, process.APP_POSTINSTALL,
                  process.APP_PREUNINSTALL, process.APP_POSTUNINSTALL          
        ]

        # Add field names header
        output = 'Name'
        for field_name in field_names:
            output += ',' + field_name
        output += ',State\n'
        
        # Add sections
        sections = configuration.get_sections()
        for section in sections:
            output += quote(section)
            items = configuration.get_section_items(section)
            for field in fields:
                try: output += ',' + quote(items[field])
                except KeyError: output += ','
            output += ',Published\n'
        
        print output
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
        
    # Clear out threads
    curl_instance.clear_threads(children)
