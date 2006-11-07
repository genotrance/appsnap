import config
import curl
import process
import threading
import time
import wx

WIDTH = 540
HEIGHT = 400

# GUI schema in YAML format
schema = """
    objects:
    - name : icon
      type : wx.Icon
      ^name : '%s'
      ^type : wx.BITMAP_TYPE_ICO

    - name : panel
      type : wx.Panel
      parent : frame

    - name : downloadicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;18'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : downloadbmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~downloadicon

    - name : installicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;162'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : installbmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~installicon

    - name : upgradeicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;19'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : upgradebmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~upgradeicon

    - name : uninstallicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;32'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : uninstallbmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~uninstallicon

    - name : dbupdateicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;35'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : dbupdatebmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~dbupdateicon

    - name : reloadicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;69'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : reloadbmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~reloadicon

    - name : toolbar
      type : wx.ToolBar
      parent : frame
      pos : (5, 0)
      style : wx.TB_TEXT
      methods:
      - method : SetMargins
        size : (5, 0)

    - name : dropdown
      type : wx.Choice
      parent : toolbar
      size : (150, -1)
      events:
      - type : wx.EVT_CHOICE
        method : category_chosen

    - name : sectionlist
      type : wx.CheckListBox
      parent : panel
      pos : (8, 20)
      events:
      - type : wx.EVT_LISTBOX
        method : show_section_info_event
      - type : wx.EVT_CHECKLISTBOX
        method : selected_section

    - name : outline
      type : wx.StaticBox
      parent : panel
      pos : (160, 14)

    - name : appwebsite
      type : wx.StaticText
      parent : panel
      pos : (175, 40)

    - name : appwebsitelink
      type : wx.lib.hyperlink.HyperLinkCtrl
      parent : panel
      pos : (225, 40)
      methods:
      - method : SetColours
        visited : wx.Colour(0, 0, 255)

    - name : appversion
      type : wx.StaticText
      parent : panel
      pos : (175, 55)

    - name : installedversion
      type : wx.StaticText
      parent : panel
      pos : (175, 70)

    - name : actionname
      type : wx.StaticText
      parent : panel
      pos : (175, 95)

    - name : progressbar
      type : wx.Gauge
      parent : panel
      range : 1000
      pos : (175, 115)
      size : (%s, 15)
      methods:
      - method : Hide

    methods:
    - name : frame
      method : SetSizeHints
      minW : %s
      minH : %s
      maxW : %s

    - name : frame
      method : SetIcon
      icon : ~icon

    - name : frame
      method : SetToolBar
      toolbar : ~toolbar

    events:
    - name : frame
      type : wx.EVT_SIZE
      method : resize_all
""" % ('appsnap.ico', WIDTH - 200, WIDTH, HEIGHT, WIDTH)

# Event processing methods
class Events:
    # Constructor
    def __init__(self, resources):
        # Save any resources provided
        self.resources = resources

        # Save process objects
        self.process = {}

        # A lock object to serialize
        self.lock = threading.Lock()

        # Create toolbar only once
        self.toolbar = False

    # Setup the event object
    def setup(self):
        # Load the configuration
        self.configuration = config.config()

        # Create a pycurl instance
        self.curl_instance = curl.curl(self.configuration)

        # Get all categories
        categories = self.configuration.get_categories()
        categories.sort()
        categories.insert(0, 'All')
        categories.insert(1, 'Installed')
        categories.insert(2, '--')

        # Get all sections
        sections = self.configuration.get_sections()
        sections.sort()

        # Add categories to dropdown and sections to sectionlist
        schema = """
            methods:
            - name : dropdown
              method : Clear

            - name : dropdown
              method : AppendItems
              strings : %s

            - name : sectionlist
              method : Clear

            - name : sectionlist
              method : InsertItems
              items : %s
              pos : 0
        """ % (categories, sections)
        self.resources['gui'].parse_and_run(schema)
        self.resources['gui'].execute([{'name' : 'dropdown', 'method' : 'Select', 'n' : 0}])

        if self.toolbar == False:
            self.create_toolbar()

    # Create the toolbar
    def create_toolbar(self):
        schema = """
            methods:
            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddControl
              control : ~dropdown

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~downloadbmp
              label : Download
              shortHelp : Download selected applications

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~installbmp
              label : Install
              shortHelp : Download and install selected applications

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~upgradebmp
              label : Upgrade
              shortHelp : Upgrade selected applications

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~uninstallbmp
              label : Uninstall
              shortHelp : Uninstall selected applications

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~dbupdatebmp
              label : Update DB
              shortHelp : Update application database

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~reloadbmp
              label : Reload
              shortHelp : Reload configuration

            - name : toolbar
              method : Realize
        """
        (objects, methods, events) = self.resources['gui'].parse(schema)
        retval = self.resources['gui'].execute(methods)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[3].GetId(), self.do_download)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[4].GetId(), self.do_install)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[5].GetId(), self.do_upgrade)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[6].GetId(), self.do_uninstall)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[8].GetId(), self.do_db_update)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[9].GetId(), self.do_reload)

        # Create toolbar only once
        self.toolbar = True

    # Resize the GUI on drag or startup
    def resize_all(self, event):
        # Get the frame size
        frame = event.GetSize()

        schema = """
            methods:
            - name : panel
              method : SetSize
              size : %s

            - name : sectionlist
              method : SetSize
              size : (150, %s)

            - name : outline
              method : SetSize
              size : (%s, %s)
        """ % (frame, frame.y - 87, WIDTH - 170, frame.y - 80)
        self.resources['gui'].parse_and_run(schema)

    # Update the section list when category is changed
    def category_chosen(self, event):
        # Get the category selected
        category = event.GetString()

        # Get all sections for this category
        if category == 'All':
            sections = self.configuration.get_sections()
        elif category == 'Installed':
            sections = self.configuration.installed.sections()
        elif category == '--':
            return
        else:
            sections = self.configuration.get_sections_by_category(category)

        # Sort
        sections.sort()

        # Replace sections
        schema = """
            methods:
            - name : sectionlist
              method : Clear

            - name : sectionlist
              method : InsertItems
              items : %s
              pos : 0
        """ % sections
        self.resources['gui'].parse_and_run(schema)

    # Reset all section information
    def reset_section_info(self):
        # Display text
        schema = """
            methods:
            - name : outline
              method : SetLabel
              label : ''

            - name : appwebsite
              method : SetLabel
              label : ''

            - name : appwebsitelink
              method : SetURL
              URL : ''

            - name : appwebsitelink
              method : SetLabel
              label : ''

            - name : appwebsitelink
              method : SetToolTipString
              tip : ''

            - name : appversion
              method : SetLabel
              label : ''

            - name : installedversion
              method : SetLabel
              label : ''

            - name : application
              method : Yield
        """
        self.resources['gui'].parse_and_run(schema)

    # Show information for the selected section
    def show_section_info(self, section):
        # Acquire lock
        self.lock.acquire()

        # Get configuration
        items = self.configuration.get_section_items(section)

        # Trim website link if needed
        if len(items['website']) > 52:
            website = items['website'][0:52] + ' ...'
            tooltip = items['website']
        else:
            website = items['website']
            tooltip = ""

        # Get installed version
        installedversion = self.configuration.get_installed_version(section)
        if installedversion != '':
            installedversion = 'Installed Version : ' + installedversion

        # Display text
        schema = """
            methods:
            - name : outline
              method : SetLabel
              label : '%s - %s'

            - name : appwebsite
              method : SetLabel
              label : 'Website :'

            - name : appwebsitelink
              method : SetURL
              URL : '%s'

            - name : appwebsitelink
              method : SetLabel
              label : '%s'

            - name : appwebsitelink
              method : SetToolTipString
              tip : '%s'

            - name : appversion
              method : SetLabel
              label : 'Latest Version : loading...'

            - name : installedversion
              method : SetLabel
              label : '%s'

            - name : application
              method : Yield
        """ % (section, items['describe'], items['website'], website, tooltip, installedversion)
        self.resources['gui'].parse_and_run(schema)

        # Get latest version
        if not self.process.has_key(section):
            self.process[section] = process.process(self.configuration, self.curl_instance, section, items)
        latest_version = self.process[section].get_latest_version()
        if latest_version == None:
            latest_version = 'failed to connect'

        # Update version
        self.resources['gui'].objects['appversion'].SetLabel('Latest Version : ' + latest_version)

        # Release lock
        self.lock.release()

    # Show information for the selected section
    def show_section_info_event(self, event):
        # Get the section selected
        section = event.GetString()

        # Show the information
        child = threading.Thread(target=self.show_section_info, args=[section])
        child.setDaemon(True)
        child.start()

    def selected_section(self, event):
        # Get the section clicked
        id = event.GetSelection()
        section = self.resources['gui'].objects['sectionlist'].GetString(id)

        # Show the information
        child = threading.Thread(target=self.show_section_info, args=[section])
        child.setDaemon(True)
        child.start()

    def get_checked_sections(self):
        sectionlist = self.resources['gui'].objects['sectionlist']

        checked = []
        for i in range(sectionlist.GetCount()):
            if sectionlist.IsChecked(i):
                checked.append(sectionlist.GetString(i))

        return checked

    def uncheck_section(self, name):
        sectionlist = self.resources['gui'].objects['sectionlist']

        for i in range(sectionlist.GetCount()):
            if sectionlist.GetString(i) == name and sectionlist.IsChecked(i):
                sectionlist.Check(i, False)
                break

    # Update progress bar and text
    def update_progress_bar(self, count, label):
        self.resources['gui'].objects['progressbar'].SetValue(count)
        self.resources['gui'].objects['actionname'].SetLabel(label)
        self.resources['gui'].objects['application'].Yield()

    # Perform specified action on the checked applications
    def do_action(self, action):
        # Get all sections selected
        checked = self.get_checked_sections()

        # Return if nothing checked
        if not len(checked): return

        # Figure out action
        count = 0
        if action == 'download':
            stepsize = 1000 / len(checked)
        elif action == 'install':
            stepsize = 500 / len(checked)
        elif action == 'uninstall':
            stepsize = 1000 / len(checked)
        elif action == 'upgrade':
            stepsize = 333 / len(checked)

        # Display progress bar
        self.resources['gui'].objects['progressbar'].Show()

        # Do action for each section
        for section in checked:
            # Display section information
            self.show_section_info(section)

            if action == 'download' or action == 'install' or action == 'upgrade':
                # Download latest version
                self.resources['gui'].objects['actionname'].SetLabel('Downloading :')
                self.resources['gui'].objects['application'].Yield()
                self.process[section].download_latest_version()
                count += stepsize
                self.resources['gui'].objects['progressbar'].SetValue(count)

            if action == 'uninstall' or (action == 'upgrade' and self.process[section].app_config['upgrades'] == 'true'):
                # Perform the uninstall
                self.resources['gui'].objects['actionname'].SetLabel('Uninstalling :')
                self.resources['gui'].objects['application'].Yield()
                if self.process[section].uninstall_version() == False:
                    return self.error_out('Uninstall')
                count += stepsize
                self.resources['gui'].objects['progressbar'].SetValue(count)

            if action == 'install' or action == 'upgrade':
                # Perform the install
                self.resources['gui'].objects['actionname'].SetLabel('Installing :')
                self.resources['gui'].objects['application'].Yield()
                if self.process[section].install_latest_version() == False:
                    return self.error_out('Install')
                count += stepsize
                self.resources['gui'].objects['progressbar'].SetValue(count)

            self.uncheck_section(section)

        # Clear all section info
        self.reset_section_info()

        # Mark as completed
        self.update_progress_bar(1000, 'Done')
        time.sleep(2)

        # Reset progressbar and hide
        self.update_progress_bar(0, '')
        self.resources['gui'].objects['progressbar'].Hide()

    # Error out if install/uninstall fails
    def error_out(self, action):
        # Mark as failed
        self.resources['gui'].objects['actionname'].SetLabel('Failed ' + action)
        self.resources['gui'].objects['application'].Yield()
        time.sleep(2)

        # Clear all section info
        self.reset_section_info()

        # Reset progressbar and hide
        self.update_progress_bar(0, '')
        self.resources['gui'].objects['progressbar'].Hide()

        # Return
        return False

    # Download checked applications
    def do_download(self, event):
        self.do_action('download')

    # Download and install checked applications
    def do_install(self, event):
        self.do_action('install')

    # Uninstall checked applications
    def do_uninstall(self, event):
        self.do_action('uninstall')

    # Upgrade checked applications
    def do_upgrade(self, event):
        self.do_action('upgrade')

    # Update database
    def do_db_update(self, event):
        # Display progress bar
        stepsize = 250
        count = 0
        self.resources['gui'].objects['progressbar'].Show()
        self.update_progress_bar(0, 'Downloading DB :')

        # Download latest DB.ini
        remote = self.curl_instance.get_web_data(self.configuration.database['location'])
        time.sleep(0.5)

        # Compare with existing DB
        count += stepsize
        self.update_progress_bar(count, 'Comparing :')
        local = open(config.DB, 'rb').read()
        time.sleep(0.5)

        if local != remote:
            # Update the DB file
            count += stepsize
            self.update_progress_bar(count, 'Updating local DB :')
            db = open(config.DB, 'wb')
            db.write(remote)
            db.close()
            time.sleep(0.5)

            # Reload settings
            count += stepsize
            self.update_progress_bar(count, 'Reloading DB :')
            self.do_reload(None)
            time.sleep(0.5)
        else:
            # No change found
            count += stepsize
            self.update_progress_bar(count, 'No changes found :')
            time.sleep(0.5)

        # Mark as completed
        self.update_progress_bar(1000, 'Done')
        time.sleep(2)

        # Reset progressbar and hide
        self.update_progress_bar(0, '')
        self.resources['gui'].objects['progressbar'].Hide()

    # Reload the configuration
    def do_reload(self, event):
        # Reload all ini files
        self.setup()

        # Clear the GUI
        self.reset_section_info()

        # Delete all process objects
        self.process = {}