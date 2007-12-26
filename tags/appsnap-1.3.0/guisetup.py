import config
import defines
import curl
import os
import os.path
import process
import re
import strings
import threading
import time
import version
import wx

# Setup localization
_ = wx.GetTranslation

# GUI schema in YAML format
schema = """
    objects:
    - name : whitecolour
      type : wx.Colour
      red : 255
      green : 255
      blue : 255
      
    - name : lightgreycolour
      type : wx.Colour
      red : 240
      green : 240
      blue : 240

    - name : darkgreycolour
      type : wx.Colour
      red : 200
      green : 200
      blue : 200
      
    - name : lightredcolour
      type : wx.Colour
      red : 255
      green : 180
      blue : 180
      
    - name : lightbluecolour
      type : wx.Colour
      red : 180
      green : 200
      blue : 255
      
    - name : bluecolour
      type : wx.Colour
      red : 0
      green : 0
      blue : 255
      
    - name : sectionfont
      type : wx.Font
      pointSize : 10
      family : wx.FONTFAMILY_DECORATIVE
      style : wx.FONTSTYLE_NORMAL
      weight : wx.FONTWEIGHT_BOLD
      face : Comic Sans MS

    - name : dropdownfont
      type : wx.Font
      pointSize : 10
      family : wx.FONTFAMILY_SWISS
      style : wx.FONTSTYLE_NORMAL
      weight : wx.FONTWEIGHT_NORMAL
      face : Arial

    - name : filterfont
      type : wx.Font
      pointSize : 9
      family : wx.FONTFAMILY_SWISS
      style : wx.FONTSTYLE_NORMAL
      weight : wx.FONTWEIGHT_NORMAL
      face : Arial
      
    - name : urlfont
      type : wx.Font
      pointSize : 6
      family : wx.FONTFAMILY_TELETYPE
      style : wx.FONTSTYLE_NORMAL
      weight : wx.FONTWEIGHT_BOLD
      face : Courier New

    - name : tbpanel
      type : wx.Panel
      parent : frame
      pos : (0, 0)
      methods:
      - method : SetBackgroundColour
        colour : ~whitecolour
      
    - name : panel
      type : wx.Panel
      parent : frame
      pos : (%s, 1)
      methods:
      - method : SetBackgroundColour
        colour : ~whitecolour

    - name : dropdown
      type : wx.Choice
      parent : panel
      size : (%s, -1)
      pos : (0, -1)
      methods:
      - method : SetFont
        font : ~dropdownfont
      events:
      - type : wx.EVT_CHOICE
        method : category_chosen
    
    - name : filterbox
      type : wx.TextCtrl
      parent : panel
      size : (%s, %s)
      pos : (200, 3)
      methods:
      - method : SetFont
        font : ~filterfont
      - method : SetValue
        value : "%s"
      - method : SetForegroundColour
        colour : ~darkgreycolour
      events:
      - type : wx.EVT_TEXT
        method : filter_section_list
      - type : wx.EVT_SET_FOCUS 
        method : adjust_filter_box_text
      - type : wx.EVT_KILL_FOCUS
        method : adjust_filter_box_text
    
    - name : bsizer
      type : wx.BoxSizer
      orient : wx.VERTICAL
      
    - name : scrollwindow
      type : wx.ScrolledWindow
      parent : panel
      pos : (0, 25)
      methods:
      - method : SetBackgroundColour
        colour : ~whitecolour
      - method : SetScrollRate
        xstep : 0
        ystep : 10
      - method : SetSizer
        sizer : ~bsizer
      - method : EnableScrolling
        x_scrolling : False
        y_scrolling : True
      - method : SetFocus
      
    - name : icon
      type : wx.Icon
      ^name : '%s'
      ^type : wx.BITMAP_TYPE_ICO

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
      ^name : '%%systemroot%%\system32\shell32.dll;15'
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

    - name : reportbugicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;13'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : reportbugbmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~reportbugicon

    - name : helpicon
      type : wx.Icon
      ^name : '%%systemroot%%\system32\shell32.dll;23'
      ^type : wx.BITMAP_TYPE_ICO
      desiredWidth: 16
      desiredHeight: 16

    - name : helpbmp
      type : wx.EmptyBitmap
      width : 16
      height : 16
      methods:
      - method : CopyFromIcon
        icon : ~helpicon

    - name : toolbar
      type : wx.ToolBar
      parent : tbpanel
      style : wx.TB_TEXT | wx.TB_VERTICAL
      methods:
      - method : SetBackgroundColour
        colour : ~whitecolour
        
    - name : statusbar
      type : wx.StatusBar
      parent : frame
      methods:
      - method : SetFieldsCount
        number : 2
  
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
      
    - name : frame
      method : SetStatusBar
      statBar : ~statusbar
  
    events:
    - name : frame
      type : wx.EVT_SIZE
      method : resize_all
""" % (defines.TOOLBAR_WIDTH,
       defines.CATEGORY_DROPDOWN_WIDTH, 
       defines.FILTER_BOX_WIDTH, defines.FILTER_BOX_HEIGHT,
       strings.FILTER,
       'appsnap.ico', 
       defines.GUI_WIDTH, defines.GUI_HEIGHT, defines.GUI_WIDTH
       )

# Event processing methods
class Events:
    # Constructor
    def __init__(self, resources):
        # Save any resources provided
        self.resources = resources

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
        categories.insert(0, config.ALL.encode('UTF-8'))
        categories.insert(1, config.INSTALLED.encode('UTF-8'))
        categories.insert(2, config.UPGRADEABLE.encode('UTF-8'))
        categories.insert(3, '--')

        # Add categories to dropdown and sections to sectionlist
        schema = """
            methods:
            - name : dropdown
              method : Clear
        """
        for category in categories:
            schema += """
            - name : dropdown
              method : Append
              item : "%s"
            """ % (category)
        self.resources['gui'].parse_and_run(schema)
        self.resources['gui'].execute([{'name' : 'dropdown', 'method' : 'Select', 'n' : 0}])

        # Get all sections
        self.initialize_section_list()
        self.update_section_list(config.ALL)
        
        if self.toolbar == False:
            self.create_toolbar()

    # Create the toolbar
    def create_toolbar(self):
        schema = """
            methods:
            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~downloadbmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~installbmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~upgradebmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~uninstallbmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~dbupdatebmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~reloadbmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~reportbugbmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~helpbmp
              label : "%s"
              shortHelp : "%s"

            - name : toolbar
              method : Realize
        """ % (strings.DOWNLOAD, strings.DOWNLOAD_DESCRIPTION,
               strings.INSTALL, strings.INSTALL_DESCRIPTION,
               strings.UPGRADE, strings.UPGRADE_DESCRIPTION,
               strings.UNINSTALL, strings.UNINSTALL_DESCRIPTION,
               strings.UPDATE_DB, strings.UPDATE_DB_DESCRIPTION,
               strings.RELOAD, strings.RELOAD_DESCRIPTION,
               strings.REPORT_BUG, strings.REPORT_BUG_DESCRIPTION,
               strings.HELP, strings.HELP_DESCRIPTION
               )
        (objects, methods, events) = self.resources['gui'].parse(schema)
        retval = self.resources['gui'].execute(methods)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[3].GetId(), self.do_download)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[5].GetId(), self.do_install)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[7].GetId(), self.do_upgrade)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[9].GetId(), self.do_uninstall)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[13].GetId(), self.do_db_update)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[15].GetId(), self.do_reload)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[19].GetId(), self.do_report)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[21].GetId(), self.do_help)
        
        # Create toolbar only once
        self.toolbar = True

    # Resize the GUI on drag or startup
    def resize_all(self, event):
        # Get the frame size
        frame = event.GetSize()
        
        schema = """
            methods:
            - name : tbpanel
              method : SetSize
              size : (%s, %s)
            
            - name : panel
              method : SetSize
              size : (%s, %s)

            - name : scrollwindow
              method : SetSize
              size : (%s, %s)
              
            - name : bsizer
              method : SetMinSize
              size : (%s, %s)
        """ % (defines.TOOLBAR_WIDTH, frame.y,
               defines.GUI_WIDTH - defines.TOOLBAR_WIDTH, frame.y, 
               defines.GUI_WIDTH - defines.TOOLBAR_WIDTH - 15, frame.y - defines.TOP_MARGIN, 
               defines.GUI_WIDTH - defines.TOOLBAR_WIDTH - 15, frame.y - defines.TOP_MARGIN
               )
        self.resources['gui'].parse_and_run(schema)
    
    # Get the title of a section
    def get_section_title(self, section):
        return "section_" + re.sub(' ', '', section)
    
    # Initialize section list
    def initialize_section_list(self):
        # Section list
        sections = self.configuration.get_sections()
        
        # Clear sizer and hide scrollwindow
        schema = """
            methods:
            - name : bsizer
              method : Clear
              deleteWindows : True
              
            - name : scrollwindow
              method : Hide
        """
        self.resources['gui'].parse_and_run(schema)
        
        for section in sections:
            section_title = self.get_section_title(section)
            items = self.configuration.get_section_items(section)
            schema = """
                objects:
                - name : %s
                  type : widgets.ApplicationPanel
                  parent : scrollwindow
                  label : %s
                  description : %s
                  url : %s
                  size : %s
                  gui : self
                  
                methods:
                - name : bsizer
                  method : Add
                  item : ~%s
                  flag : wx.GROW
            """ % (section_title, 
                   section, 
                   items[process.APP_DESCRIBE], 
                   items[process.APP_WEBSITE], 
                   (defines.GUI_WIDTH-defines.TOOLBAR_WIDTH-100, defines.SECTION_HEIGHT), 
                   section_title
                   )
            self.resources['gui'].parse_and_run(schema)
            self.resources['gui'].objects[section_title].set_event(self)

    # Update the section list
    def update_section_list(self, category):
        # Get sections by category
        if category == config.ALL:
            sections = self.configuration.get_sections()
        elif category == config.INSTALLED or category == config.UPGRADEABLE:
            sections = self.configuration.installed.sections()
        elif category == '--':
            return
        else:
            sections = self.configuration.get_sections_by_category(category)

        # Disable GUI
        self.disable_gui()

        # Get filter string if any
        filter = self.resources['gui'].objects['filterbox'].GetValue().lower()
        if filter == strings.FILTER.lower():
            filter = ''

        # Construct section list
        section_objs = []
        for section in sections:
            if (len(filter) == 0) or (len(filter) and section.lower().find(filter) != -1):
                section_objs.append(self.resources['gui'].objects[self.get_section_title(section)])

        # Show scrollwindow
        schema = """
            methods:
            - name : scrollwindow
              method : Hide
        """
        self.resources['gui'].parse_and_run(schema)

        row = 0
        children = []
        for item in self.resources['gui'].objects['bsizer'].GetChildren():
            item.GetWindow().reset()
            if item.GetWindow() in section_objs:
                item.Show(True)
                if category == config.UPGRADEABLE:
                    self.refresh_section_list()
                    children.append(threading.Thread(target=item.GetWindow().display_if_upgradeable, args=[item]))
                    children[row].start()
                else:
                    item.GetWindow().set_colour_by_row(row)
                row = row + 1
            else:
                item.Show(False)

        # Wait for children to be done
        if category == config.UPGRADEABLE:
            for child in children:
                child.join()
                self.refresh_section_list()
            # Recolour rows
            row = 0
            for item in self.resources['gui'].objects['bsizer'].GetChildren():
                if item.IsShown():
                    item.GetWindow().save_colour_by_row(row)
                    row = row + 1

        self.refresh_section_list()
        
        # Enable GUI
        self.enable_gui()
        
    # Filter the section list by string
    def filter_section_list(self, event):
        # Get current selected category
        category = self.resources['gui'].objects['dropdown'].GetStringSelection()
        time.sleep(defines.SLEEP_GUI_FILTER_SECTION_LIST)
        child = threading.Thread(target=self.update_section_list, args=[category])
        child.setDaemon(True)
        child.start()
        
    # Display or hide the word "Filter :" in the filterbox
    def adjust_filter_box_text(self, event):
        # Get filter string if any
        filter = self.resources['gui'].objects['filterbox'].GetValue()
        if filter == strings.FILTER:
            self.resources['gui'].objects['filterbox'].ChangeValue('')
        elif filter == '':
            self.resources['gui'].objects['filterbox'].ChangeValue(strings.FILTER)

    # Refresh the section list
    def refresh_section_list(self):
        # Acquire lock
        self.lock.acquire()
        
        schema = """
            methods:
            - name : bsizer
              method : Layout

            - name : bsizer
              method : FitInside
              window : ~scrollwindow

            - name : scrollwindow
              method : Refresh

            - name : scrollwindow
              method : Show
              
            - name : statusbar
              method : Refresh
        """
        self.resources['gui'].parse_and_run(schema)

        # Fix for disappearing section information
        for item in self.resources['gui'].objects['bsizer'].GetChildren():
            if item.IsShown():
                item.GetWindow().set_position()

        # Release lock
        self.lock.release()
        
    # Update the section list when category is changed
    def category_chosen(self, event):
        # Get the category selected
        category = event.GetString()
        child = threading.Thread(target=self.update_section_list, args=[category])
        child.setDaemon(True)
        child.start()

        schema = """
            methods:
            - name : scrollwindow
              method : SetFocus
        """
        self.resources['gui'].parse_and_run(schema)
        
    # Get all visible and checked sections
    def get_checked_sections(self):
        checked = []
        items = self.resources['gui'].objects['bsizer'].GetChildren()
        for item in items:
            if item.IsShown() and item.GetWindow().checkbox.IsChecked() == True:
                checked.append(item.GetWindow())

        return checked

    # Update status bar text
    def update_status_bar(self, first, second):
        schema = """
            methods:
            - name : statusbar
              method : SetStatusText
              text : "%s"
              number : 0
              
            - name : statusbar
              method : SetStatusText
              text : "%s"
              number : 1
              
            - name : statusbar
              method : Refresh
        """ % (_(first).encode('UTF-8'), _(second).encode('UTF-8'))
        self.resources['gui'].parse_and_run(schema)

    # Disable GUI elements
    def disable_gui(self):
        schema = """
            methods:
            - name : toolbar
              method : Disable
              
            - name : toolbar
              method : Refresh
              
            - name : dropdown
              method : Disable
              
            - name : filterbox
              method : Disable

            - name : statusbar
              method : Refresh
              
            - name : application
              method : Yield
        """
        self.resources['gui'].parse_and_run(schema)

    # Enable GUI elements
    def enable_gui(self):
        schema = """
            methods:
            - name : toolbar
              method : Enable
              
            - name : toolbar
              method : Refresh
              
            - name : dropdown
              method : Enable

            - name : filterbox
              method : Enable

            - name : statusbar
              method : Refresh

            - name : application
              method : Yield
        """
        self.resources['gui'].parse_and_run(schema)
        
    # Start an action thread
    def do_threaded_action(self, action):
        child = threading.Thread(target=self.do_action, args=[action])
        child.setDaemon(True)
        child.start()
        
    # Perform specified action on the checked applications
    def do_action(self, action):
        # Get all sections selected
        checked = self.get_checked_sections()

        # Return if nothing checked
        if not len(checked): return
        
        # Disable GUI
        self.disable_gui()
        
        # Update status bar
        self.update_status_bar(action[0].capitalize() + action[1:], '')

        # Do action for each section
        children = []
        for section in checked:
            # Limit number of parallel threads
            self.curl_instance.limit_threads(children)
            
            child = threading.Thread(target=section.do_action, args=[action])
            children.append(child)
            child.start()

        # Reset the GUI
        self.update_status_bar('', '')
        self.enable_gui()
        
    # Error out if an action fails
    def error_out(self, action, message):
        # Mark as failed
        self.update_status_bar(action, message)
        time.sleep(defines.SLEEP_GUI_ERROR_OUT)
        self.update_status_bar('', '')

        # Reset the GUI
        self.enable_gui()
        
        # Return
        return False
    
    # Download checked applications
    def do_download(self, event):
        self.do_threaded_action(process.ACT_DOWNLOAD)

    # Download and install checked applications
    def do_install(self, event):
        self.do_threaded_action(process.ACT_INSTALL)

    # Uninstall checked applications
    def do_uninstall(self, event):
        self.do_threaded_action(process.ACT_UNINSTALL)

    # Upgrade checked applications
    def do_upgrade(self, event):
        self.do_threaded_action(process.ACT_UPGRADE)

    # Update database
    def do_db_update(self, event):
        # Action name
        action = strings.UPDATING_DATABASE
        
        # Disable GUI
        self.disable_gui()
        
        # Update statusbar
        self.update_status_bar(action, strings.DOWNLOADING + ' ...')

        # Download latest DB.ini
        remote = self.curl_instance.get_web_data(self.configuration.database[config.LOCATION] + '/?version=' + version.APPVERSION)
        time.sleep(defines.SLEEP_GUI_DB_UPDATE_STEP)
        
        # If download failed
        if remote == None:
            return self.error_out(action, strings.DOWNLOAD_FAILED)

        # Compare with existing DB
        self.update_status_bar(action, strings.COMPARING + ' ...')
        local = open(config.DB_INI, 'rb').read()
        time.sleep(defines.SLEEP_GUI_DB_UPDATE_STEP)

        if local != remote:
            # Update the DB file
            self.update_status_bar(action, strings.UPDATING_LOCAL_DATABASE + ' ...')
            try:
                db = open(config.DB_INI, 'wb')
                db.write(remote)
                db.close()
                time.sleep(defines.SLEEP_GUI_DB_UPDATE_STEP)

                # Reload settings
                self.update_status_bar(action, strings.RELOADING_DATABASE + ' ...')
                self.setup()
                time.sleep(defines.SLEEP_GUI_DB_UPDATE_STEP)
                self.update_status_bar(action, strings.DONE)
                self.configuration.copy_database_to_cache(True)
                time.sleep(defines.SLEEP_GUI_DB_UPDATE_DONE)
            except IOError:
                self.update_status_bar(action, strings.UNABLE_TO_WRITE_DB_INI)
                time.sleep(defines.SLEEP_GUI_DB_UPDATE_DONE)
        else:
            # No change found
            self.update_status_bar(action, strings.NO_CHANGES_FOUND)
            time.sleep(defines.SLEEP_GUI_DB_UPDATE_DONE)

        # Reset the GUI
        self.update_status_bar('', '')
        self.enable_gui()
        
    # Reload the configuration
    def do_reload(self, event):
        # Disable the GUI
        self.disable_gui()
        self.update_status_bar(strings.RELOADING_DATABASE, '')
        
        # Reload all ini files
        self.setup()
        
        # Reset the GUI
        self.update_status_bar('', '')
        self.enable_gui()
        
    # Report a bug
    def do_report(self, event):
        os.startfile('http://code.google.com/p/appsnap/issues/entry')
        
    # Open help
    def do_help(self, event):
        if os.path.exists('appsnap.html'):
            os.startfile('appsnap.html')