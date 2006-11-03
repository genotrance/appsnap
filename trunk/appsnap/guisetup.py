import wx

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

    - name : configicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;35'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : configbmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~configicon

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

    - name : actionname
      type : wx.StaticText
      parent : panel
      pos : (175, 80)

    - name : progressbar
      type : wx.Gauge
      parent : panel
      range : 1000
      pos : (175, 100)
      size : (250, 15)
      methods:
      - method : Hide

    methods:
    - name : frame
      method : SetSizeHints
      minW : 450
      minH : 350
      maxW : 450

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
""" % ('appsnap.ico')

# Event processing methods
class Events:
    # Constructor
    def __init__(self, resources):
        # Save any resources provided
        self.resources = resources

        # Save process objects
        self.process = {}

        # A lock object to serialize
        import threading
        self.lock = threading.Lock()

    # Setup the event object
    def setup(self):
        # Load the configuration
        import config
        self.configuration = config.config()

        # Create a pycurl instance
        import curl
        self.curl_instance = curl.curl(self.configuration)

        # Get all categories
        categories = self.configuration.get_categories()
        categories.sort()
        categories.insert(0, 'All')

        # Get all sections
        sections = self.configuration.get_sections()
        sections.sort()

        # Add categories to dropdown and sections to sectionlist
        schema = """
            methods:
            - name : dropdown
              method : AppendItems
              strings : %s

            - name : sectionlist
              method : InsertItems
              items : %s
              pos : 0
        """ % (categories, sections)
        self.resources['gui'].parse_and_run(schema)
        self.resources['gui'].execute([{'name' : 'dropdown', 'method' : 'Select', 'n' : 0}])

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
            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~installbmp
              label : Install
            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~upgradebmp
              label : Upgrade
            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~uninstallbmp
              label : Uninstall
            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~configbmp
              label : Configure
            - name : toolbar
              method : Realize
        """
        (objects, methods, events) = self.resources['gui'].parse(schema)
        retval = self.resources['gui'].execute(methods)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[3].GetId(), self.do_download)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[4].GetId(), self.do_install)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[5].GetId(), self.do_upgrade)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[6].GetId(), self.do_uninstall)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[7].GetId(), self.do_configure)

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
              size : (280, %s)
        """ % (frame, frame.y - 87, frame.y - 80)
        self.resources['gui'].parse_and_run(schema)

    # Update the section list when category is changed
    def category_chosen(self, event):
        # Get the category selected
        category = event.GetString()

        # Get all sections for this category
        if category != "All":
            sections = self.configuration.get_sections_by_category(category)
        else:
            sections = self.configuration.get_sections()

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
        if len(items['website']) > 35:
            website = items['website'][0:35] + ' ...'
            tooltip = items['website']
        else:
            website = items['website']
            tooltip = ""

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

            - name : application
              method : Yield
        """ % (section, items['describe'], items['website'], website, tooltip)
        self.resources['gui'].parse_and_run(schema)

        # Get latest version
        if not self.process.has_key(section):
            import process
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
        import threading
        child = threading.Thread(target=self.show_section_info, args=[section])
        child.setDaemon(True)
        child.start()

    def selected_section(self, event):
        # Get the section clicked
        id = event.GetSelection()
        section = self.resources['gui'].objects['sectionlist'].GetString(id)

        # Show the information
        import threading
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

    def uncheck_all_sections(self):
        sectionlist = self.resources['gui'].objects['sectionlist']

        for i in range(sectionlist.GetCount()):
            if sectionlist.IsChecked(i):
                sectionlist.Check(i, False)

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
        self.resources['gui'].objects['application'].Yield()

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

            if action == 'uninstall' or action == 'upgrade':
                # Perform the uninstall
                self.resources['gui'].objects['actionname'].SetLabel('Uninstalling :')
                self.resources['gui'].objects['application'].Yield()
                self.process[section].uninstall_version()
                count += stepsize
                self.resources['gui'].objects['progressbar'].SetValue(count)

            if action == 'install' or action == 'upgrade':
                # Perform the install
                self.resources['gui'].objects['actionname'].SetLabel('Installing :')
                self.resources['gui'].objects['application'].Yield()
                self.process[section].install_latest_version()
                count += stepsize
                self.resources['gui'].objects['progressbar'].SetValue(count)

        # Clear all section info
        self.reset_section_info()

        # Mark as completed
        schema = """
            methods:
            - name : progressbar
              method : SetValue
              pos : 1000

            - name : actionname
              method : SetLabel
              label : Done

            - name : application
              method : Yield
        """
        self.resources['gui'].parse_and_run(schema)
        import time
        time.sleep(2)

        # Reset progressbar and hide
        schema = """
            methods:
            - name : actionname
              method : SetLabel
              label : ''

            - name : progressbar
              method : Hide

            - name : progressbar
              method : SetValue
              pos : 0
        """
        self.resources['gui'].parse_and_run(schema)

        # Uncheck all sections
        self.uncheck_all_sections()

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

    # Configuration
    def do_configure(self, event):
        pass