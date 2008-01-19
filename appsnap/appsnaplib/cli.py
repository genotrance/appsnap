# Import required libraries
import codecs
import config
import curl
import defines
import getopt
import process
import re
import string
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
      -v\t\t%s
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
       strings.VERBOSE_DOWNLOAD,
       strings.TEST_DOWNLOAD_ONLY,
       strings.GET_LATEST_VERSION,
       strings.DEFAULT,
       strings.INSTALL_DESCRIPTION,
       strings.INSTALL_IMPLICATION,
       strings.UPGRADE_DESCRIPTION,
       strings.UPGRADE_IMPLICATION,
       strings.UNINSTALL_DESCRIPTION
       )

# Blank line
BL = '\r%40s\r' % (' ')

# Display download status
def display_download_status(dl_total, dl_current, ul_total, ul_current, status={}):
    name = threading.currentThread().getName()
    status[name] = [dl_total, dl_current]

    total = 0
    current = 0
    for app_name in status:
        total += status[app_name][0]
        current += status[app_name][1]

    # Create current string
    if current < 1024 * 1024:
        current_string = '%.2f KB' % (current / 1024)
    else:
        current_string = '%.2f MB' % (current / 1024 / 1024)

    # Create total string
    if total < 1024 * 1024:
        total_string = '%.2f KB' % (total / 1024)
    else:
        total_string = '%.2f MB' % (total / 1024 / 1024)
        
    # Percentage string
    if total != 0:
        percentage_string = '[%d%%]' % (current / total * 100)
    else:
        percentage_string = ''

    print '%s%s %s / %s %s\r' % (BL, strings.DOWNLOADED, current_string, total_string, percentage_string),
    sys.stdout.flush()

# Perform an action on the specified application
def do_action(configuration, curl_instance, lock, name, getversion, download, install, upgrade, uninstall, test, verbose):
    # Set the thread name
    thread = threading.currentThread()
    thread.setName(name)

    items = configuration.get_section_items(name)
    if items == None: items = configuration.get_arp_section_items(name + config.ARP_ID)
    if items != None:
        p = process.process(configuration, curl_instance, name, items)
        
        # Display download status if verbose
        if verbose: progress_callback = display_download_status
        else: progress_callback = None

        if getversion == True:
            output = '%s\n%s : %s\n' % (BL, strings.APPLICATION, name)
            if items[process.APP_DESCRIBE] != '':
                output += '%s : %s\n' % (strings.DESCRIPTION, items[process.APP_DESCRIBE])
            if items[process.APP_WEBSITE] != '':
                output += '%s : %s\n' % (strings.WEBSITE, items[process.APP_WEBSITE])
            if items[process.APP_CATEGORY] != config.REMOVABLE:
                latest_version = p.get_latest_version()
                if latest_version == None:
                    latest_version = strings.FAILED_TO_CONNECT
                output += '%s : %s\n' % (strings.LATEST_VERSION, latest_version)
            installed = p.get_installed_version()
            if installed != '':
                output += '%s : %s\n' % (strings.INSTALLED_VERSION, installed)
            print output
        if download == True:
            output = '%s-> %s %s' % (BL, strings.DOWNLOADING, name)
            if test: output += ' (%s)' % strings.TESTING
            print output
            if p.download_latest_version(progress_callback, test) == False:
                print '%s-> %s : %s' % (BL, strings.DOWNLOAD_FAILED, name)
                return
            else:
                print '%s-> %s : %s' % (BL, strings.DOWNLOAD_SUCCEEDED, name)
        if install == True:
            print '%s-> %s %s' % (BL, strings.INSTALLING, name)
            lock.acquire()
            if p.install_latest_version(progress_callback) == False: 
                print '%s-> %s : %s' % (BL, strings.INSTALL_FAILED, name)
                lock.release()
                return
            else:
                print '%s-> %s : %s' % (BL, strings.INSTALL_SUCCEEDED, name)
            lock.release()
        if upgrade == True:
            print '%s-> %s %s' % (BL, strings.UPGRADING, name)
            lock.acquire()
            if p.upgrade_version(progress_callback) == False: 
                print '%s-> %s : %s' % (BL, strings.UPGRADE_FAILED, name)
                lock.release()
                return
            else:
                print '%s-> %s : %s' % (BL, strings.UPGRADE_SUCCEEDED, name)
            lock.release()
        if uninstall == True:
            print '%s-> %s %s' % (BL, strings.UNINSTALLING, name)
            lock.acquire()
            if p.uninstall_version() == False: 
                print '%s-> %s : %s' % (BL, strings.UNINSTALL_FAILED, name)
                lock.release()
                return
            else:
                print '%s-> %s : %s' % (BL, strings.UNINSTALL_SUCCEEDED, name)
            lock.release()
    else:
        print '%s%s : %s' % (BL, strings.NO_SUCH_APPLICATION, name)

# Run the CLI
def appsnap_start():
    # Parse command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'cdDf:ghiln:s:tuUvVwx')
    except getopt.GetoptError:
        print help
        sys.exit(defines.ERROR_GETOPT)

    # Set defaults
    categories = False
    download = False
    database_only = False
    categoryfilter = ''
    getversion = True
    install = False
    list = False
    names = None
    stringfilter = ''
    test = False
    upgrade = False
    updateall = False
    verbose = False
    csvdump = False
    wikidump = False
    uninstall = False

    for o, a in opts:
        if o == '-c': categories = True
        if o == '-d': download = True
        if o == '-D': database_only = True
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
        if o == '-v': verbose = True
        if o == '-V': csvdump = True
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
        if check_only == False: print '-> %s' % strings.UPDATING_APPSNAP
        else: print '-> %s' % strings.CHECKING_FOR_UPDATES
        update_obj = update.update(configuration, curl_instance, check_only, database_only)
        returned = update_obj.update_appsnap()
        
        if returned == update.SUCCESS:
            print '-> %s' % strings.UPDATE_APPSNAP_SUCCEEDED
        elif returned == update.CHANGED:
            print '-> %s' % strings.UPDATES_AVAILABLE
        elif returned == update.UNCHANGED:
            print '-> %s' % strings.NO_CHANGES_FOUND
        elif returned == update.NEW_BUILD:
            print '-> %s' % strings.NEW_BUILD_REQUIRED
        elif returned == update.READ_ERROR:
            print '-> %s - %s' % (strings.UPDATE_APPSNAP_FAILED, strings.UNABLE_TO_READ_APPSNAP)
        elif returned == update.WRITE_ERROR:
            print '-> %s - %s' % (strings.UPDATE_APPSNAP_FAILED, strings.UNABLE_TO_WRITE_APPSNAP)
        elif returned == update.DOWNLOAD_FAILURE:
            print '-> %s - %s' % (strings.UPDATE_APPSNAP_FAILED, strings.DOWNLOAD_FAILED)
            
        sys.exit(defines.ERROR_SUCCESS)
        
    # Dump application database in wiki format if requested
    if wikidump == True:
        categories = configuration.get_categories()
        num_sections = 0
        for category in categories:
            sections = configuration.get_sections_by_category(category)
            num_sections += len(sections)
            print '!!!%s (%d)' % (category, len(sections))
            
            for section in sections:
                items = configuration.get_section_items(section)
                
                print '* [[%s|%s]] - """%s"""' % (section, items[process.APP_WEBSITE], items[process.APP_DESCRIBE])
                
        print '!!!Total: %d applications in %d categories' % (num_sections, len(categories))
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
                       'Install Directory Detection', 
                       'Auto Upgrades', 'Change Installdir Parameters', 'Uninstall Entry',
                       'Uninstall Parameters', 'Pre Install Command', 'Post Install Command',
                       'Pre Uninstall Command', 'Post Uninstall Command'
                       ]
        fields = [
                  process.APP_CATEGORY, process.APP_DESCRIBE, process.APP_WEBSITE,
                  process.APP_SCRAPE, process.APP_VERSION, process.APP_DOWNLOAD,
                  process.APP_FILENAME, process.APP_RENAME, process.APP_REFERER,
                  process.APP_INSTALLER, process.APP_INSTPARAM, process.APP_INSTVERSION,
                  process.APP_INSTDIR,
                  process.APP_UPGRADES, process.APP_CHINSTDIR, process.APP_UNINSTALL,
                  process.APP_UNINSTPARAM, process.APP_PREINSTALL, process.APP_POSTINSTALL,
                  process.APP_PREUNINSTALL, process.APP_POSTUNINSTALL          
        ]

        # Add field names header
        data = ['Name']
        data.extend(field_names)
        data.append('State\n')
        output = [string.join(data, ',')]
        
        # Add sections
        sections = configuration.get_sections()
        for section in sections:
            data = [quote(section)]
            items = configuration.get_section_items(section)
            for field in fields:
                try: data.append(quote(items[field]))
                except KeyError: data.append('')
            data.append('Published\n')
            output.append(string.join(data, ','))
        
        print string.join(output, '')
        sys.exit(defines.ERROR_SUCCESS)

    # Figure out applications selected
    if len(names) == 1 and names[0] == '*':
        if categoryfilter == '':
            names = configuration.get_sections()
        else:
            print '%s : %s' % (strings.CATEGORY, categoryfilter)
            names = configuration.get_sections_by_category(categoryfilter)

        if stringfilter != '':
            print '%s : %s\n' % (strings.FILTER, stringfilter)
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
                                                         test,
                                                         verbose])
        children.append(child)
        child.start()
        
    # Clear out threads
    curl_instance.clear_threads(children)
