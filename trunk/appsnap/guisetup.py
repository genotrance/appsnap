import config
import curl
import process
import re
import threading
import time
import wx

WIDTH = 400
HEIGHT = 590

TBWIDTH = 60

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
      
    - name : sectionfont
      type : wx.Font
      pointSize : 10
      family : wx.FONTFAMILY_DECORATIVE
      style : wx.FONTSTYLE_NORMAL
      weight : wx.FONTWEIGHT_BOLD

    - name : dropdownfont
      type : wx.Font
      pointSize : 10
      family : wx.FONTFAMILY_SWISS
      style : wx.FONTSTYLE_NORMAL
      weight : wx.FONTWEIGHT_NORMAL

    - name : urlfont
      type : wx.Font
      pointSize : 6
      family : wx.FONTFAMILY_TELETYPE
      style : wx.FONTSTYLE_NORMAL
      weight : wx.FONTWEIGHT_BOLD

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
      size : (120, -1)
      pos : (200, -1)
      methods:
      - method : SetFont
        font : ~dropdownfont
      events:
      - type : wx.EVT_CHOICE
        method : category_chosen
        
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

    - name : toolbar
      type : wx.ToolBar
      parent : tbpanel
      style : wx.TB_TEXT | wx.TB_VERTICAL
      methods:
      - method : SetBackgroundColour
        colour : ~whitecolour
  
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
""" % (TBWIDTH, 'appsnap.ico', WIDTH, HEIGHT, WIDTH)

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
        categories.insert(0, 'All')
        categories.insert(1, 'Installed')
        categories.insert(2, 'Upgradeable')
        categories.insert(3, '--')

        # Add categories to dropdown and sections to sectionlist
        schema = """
            methods:
            - name : dropdown
              method : Clear

            - name : dropdown
              method : AppendItems
              strings : %s
        """ % (categories)
        self.resources['gui'].parse_and_run(schema)
        self.resources['gui'].execute([{'name' : 'dropdown', 'method' : 'Select', 'n' : 0}])

        # Get all sections
        self.initialize_section_list()
        self.update_section_list('All')
        
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
              label : Download
              shortHelp : Download selected applications

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~installbmp
              label : Install
              shortHelp : Download and install selected applications

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~upgradebmp
              label : Upgrade
              shortHelp : Upgrade selected applications

            - name : toolbar
              method : AddSeparator

            - name : toolbar
              method : AddLabelTool
              id : -1
              bitmap : ~uninstallbmp
              label : Uninstall
              shortHelp : Uninstall selected applications

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
              label : Update DB
              shortHelp : Update application database

            - name : toolbar
              method : AddSeparator

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
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[5].GetId(), self.do_install)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[7].GetId(), self.do_upgrade)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[9].GetId(), self.do_uninstall)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[13].GetId(), self.do_db_update)
        wx.EVT_MENU(self.resources['gui'].objects['frame'], retval[15].GetId(), self.do_reload)

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
        """ % (TBWIDTH, frame.y, frame.x - TBWIDTH + 1, frame.y, WIDTH - 80, frame.y - 80, WIDTH - TBWIDTH, frame.y - 80)
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
            """ % (section_title, section, items['describe'], items['website'], (WIDTH-TBWIDTH-100, 50), section_title)
            self.resources['gui'].parse_and_run(schema)
            self.resources['gui'].objects[section_title].set_event(self)

    # Update the section list
    def update_section_list(self, category):
        # Get sections by category
        if category == 'All':
            sections = self.configuration.get_sections()
        elif category == 'Installed' or category == 'Upgradeable':
            sections = self.configuration.installed.sections()
        elif category == '--':
            return
        else:
            sections = self.configuration.get_sections_by_category(category)

        # Disable GUI
        self.disable_gui()

        # Construct section list
        section_objs = []
        for section in sections:
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
                if category == 'Upgradeable':
                    self.refresh_section_list()
                    children.append(threading.Thread(target=item.GetWindow().display_if_upgradeable, args=[item]))
                    children[row].start()
                else:
                    item.GetWindow().set_colour_by_row(row)
                row = row + 1
            else:
                item.Show(False)

        # Wait for children to be done
        if category == 'Upgradeable':
            for child in children:
                child.join()
                self.refresh_section_list()
            # Recolour rows
            row = 0
            for item in self.resources['gui'].objects['bsizer'].GetChildren():
                if item.IsShown():
                    item.GetWindow().save_colour_by_row(row)
                    row = row + 1
        else:
            self.refresh_section_list()
        
        # Enable GUI
        self.enable_gui()

    # Refresh the section list
    def refresh_section_list(self):
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
        """
        self.resources['gui'].parse_and_run(schema)

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
        
    def get_checked_sections(self):
        checked = []
        items = self.resources['gui'].objects['bsizer'].GetChildren()
        for item in items:
            if item.GetWindow().checkbox.IsChecked() == True:
                checked.append(item.GetWindow().app_name)

        return checked

    def uncheck_section(self, name):
        section_obj = self.resources['gui'].objects[self.get_section_title(name)]
        section_obj.select(False)

    # Update progress bar and text
    def update_progress_bar(self, count, label):
        self.resources['gui'].objects['progressbar'].SetValue(count)
        self.resources['gui'].objects['actionname'].SetLabel(label)
        self.resources['gui'].objects['application'].Yield()

    # Disable GUI elements
    def disable_gui(self):
        self.resources['gui'].objects['toolbar'].Disable()
        self.resources['gui'].objects['dropdown'].Disable()

    # Enable GUI elements
    def enable_gui(self):
        self.resources['gui'].objects['toolbar'].Enable()
        self.resources['gui'].objects['toolbar'].Refresh()
        self.resources['gui'].objects['dropdown'].Enable()
        
    # Reset GUI
    def reset_gui(self):
        # Reset progressbar and hide
        self.update_progress_bar(0, '')
        self.resources['gui'].objects['progressbar'].Hide()

        # Enable GUI
        self.enable_gui()
        
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
                if self.process[section].download_latest_version() == False:
                    return self.error_out('Download')
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

        # Reset the GUI
        self.reset_gui()
        
    # Error out if install/uninstall fails
    def error_out(self, action):
        # Mark as failed
        self.resources['gui'].objects['actionname'].SetLabel('Failed ' + action)
        self.resources['gui'].objects['application'].Yield()
        time.sleep(2)

        # Clear all section info
        self.reset_section_info()

        # Reset the GUI
        self.reset_gui()
        
        # Return
        return False

    # Download checked applications
    def do_download(self, event):
        self.do_threaded_action('download')

    # Download and install checked applications
    def do_install(self, event):
        self.do_threaded_action('install')

    # Uninstall checked applications
    def do_uninstall(self, event):
        self.do_threaded_action('uninstall')

    # Upgrade checked applications
    def do_upgrade(self, event):
        self.do_threaded_action('upgrade')

    # Update database
    def do_db_update(self, event):
        self.do_threaded_db_update()
        
    # Update database
    def do_threaded_db_update(self):
        # Disable GUI
        self.disable_gui()
        
        # Display progress bar
        stepsize = 250
        count = 0
        self.resources['gui'].objects['progressbar'].Show()
        self.update_progress_bar(0, 'Downloading DB :')

        # Download latest DB.ini
        remote = self.curl_instance.get_web_data(self.configuration.database['location'])
        time.sleep(0.5)
        
        # If download failed
        if remote == None:
            return self.error_out('Download DB')

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

        # Reset the GUI
        self.reset_gui()
        
    # Reload the configuration
    def do_reload(self, event):
        # Reload all ini files
        self.setup()

        # Delete all process objects
        self.process = {}