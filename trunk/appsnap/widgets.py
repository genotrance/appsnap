import process
import threading
import wx
import wx.lib.hyperlink

# Application panel
class ApplicationPanel(wx.Panel):
    # Constructor
    def __init__(self, parent, label, description, url, gui, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL | wx.NO_BORDER):
        wx.Panel.__init__(self, parent, -1, pos=pos, size=size, style=style)

        # State information
        self.gui = gui
        self.app_name = label
        self.selected = False
        
        # Widgets
        self.label = wx.StaticText(self, -1, label, pos=(40, 10))
        self.label.SetFont(self.gui.objects['sectionfont'])

        self.checkbox = wx.CheckBox(self, -1, pos=(10, 20))
        self.description = wx.StaticText(self, -1, description, pos=(40, 30))

        self.version = wx.StaticText(self, -1, '')
        self.installed_version = wx.StaticText(self, -1, '')
        
        self.url = wx.lib.hyperlink.HyperLinkCtrl(self, pos=(45 + self.label.GetSize().GetWidth(), 10))
        self.url.SetFont(self.gui.objects['urlfont'])
        self.url.SetLabel(">>")
        self.url.SetURL(url)
        self.url.SetToolTipString(url)
        
        # Size
        self.SetMinSize(size)
        self.SetMaxSize(size)
        
        # Events
        self.setup_click_event([self, self.label, self.description, self.version, self.installed_version])
        wx.EVT_CHECKBOX(self.gui.objects['frame'], self.checkbox.GetId(), self.on_checkbox_click)
    
    #####
    # Setup helpers

    # Set event object
    def set_event(self, event):
        self.event = event

    # Setup left click event
    def setup_click_event(self, widgets):
        for widget in widgets:
            wx.EVT_LEFT_DOWN(widget, self.on_click)
            wx.EVT_LEFT_DCLICK(widget, self.on_click)
        
    # Set the colour of panel based on row number
    def set_colour_by_row(self, row):
        # Color
        if (row % 4 == 0):
            self.row_colour = self.gui.objects['darkgreycolour']
        elif (row % 2 == 0):
            self.row_colour = self.gui.objects['lightgreycolour']
        else:
            self.row_colour = self.gui.objects['whitecolour']
        self.SetBackgroundColour(self.row_colour)

    #####
    # Display helpers

    # Display version information
    def set_version(self, version):
        if self.selected == True:
            self.version.SetLabel(version)
            self.version.SetPosition((40, 45))

    # Hide version information
    def unset_version(self):
        self.version.SetLabel('')
        self.version.SetPosition((0, 0))

    # Display installed version
    def set_installed_version(self, installed_version):
        if self.selected == True:
            self.installed_version.SetLabel(installed_version)
            self.installed_version.SetPosition((40, 60))

    # Hide installed version
    def unset_installed_version(self):
        self.installed_version.SetLabel('')
        self.installed_version.SetPosition((0, 0))

    # Show version information
    def show_info(self):
        # Get configuration
        items = self.event.configuration.get_section_items(self.app_name)
        height = 50

        # Get installed version
        installed_version = self.event.configuration.get_installed_version(self.app_name)
        if installed_version != '':
            installed_version = 'Installed Version : ' + installed_version
            self.set_installed_version(installed_version)
            height = height + 15

        # Display latest version text
        self.set_version('Latest Version : loading...')
        height = height + 15
        
        # Update layout
        self.SetMinSize((self.GetMinWidth(), height))
        self.SetMaxSize((self.GetMinWidth(), height))
        self.gui.objects['scrollwindow'].Refresh()
        self.gui.objects['bsizer'].Layout()
        self.gui.objects['bsizer'].FitInside(self.gui.objects['scrollwindow'])
        
        # Get the latest version
        if not self.event.process.has_key(self.app_name):
            self.event.process[self.app_name] = process.process(self.event.configuration, self.event.curl_instance, self.app_name, items)
        latest_version = self.event.process[self.app_name].get_latest_version()
        if latest_version == None:
            latest_version = 'failed to connect'
        self.set_version('Latest Version : ' + latest_version)

    # Hide information
    def hide_info(self):
        self.unset_version()
        self.unset_installed_version()
        self.SetMinSize((self.GetMinWidth(), 50))
        self.Refresh()
        self.gui.objects['bsizer'].Layout()
        self.gui.objects['bsizer'].FitInside(self.gui.objects['scrollwindow'])
    
    #####
    # State helpers

    # Select application
    def select(self, value):
        if value == True:
            self.selected = True
            self.SetBackgroundColour(self.gui.objects['lightredcolour'])
            child = threading.Thread(target=self.show_info)
            child.setDaemon(True)
            child.start()
        else:
            self.selected = False
            self.SetBackgroundColour(self.row_colour)
            self.checkbox.SetValue(False)
            self.hide_info()
        self.Refresh()
        
    # Reset state
    def reset(self):
        self.selected = False
        self.checkbox.SetValue(False)
        self.unset_version()
        self.unset_installed_version()

    #####
    # Event methods
    
    # When panel or text is clicked
    def on_click(self, event):
        if self.selected == True and self.checkbox.IsChecked() == False:
            self.select(False)
        elif self.selected == False and self.checkbox.IsChecked() == False:
            self.selected = True
            self.SetBackgroundColour(self.gui.objects['lightbluecolour'])
            child = threading.Thread(target=self.show_info)
            child.setDaemon(True)
            child.start()
        self.Refresh()
        
    # When checkbox is clicked
    def on_checkbox_click(self, event):
        if event.IsChecked() == True:
            self.select(True)
        else:
            self.select(False)

    # Perform specified action
    def do_action(self, action):
        # Display action field
        
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

        # Clear all section info
        self.reset_section_info()

        # Mark as completed
        self.update_progress_bar(1000, 'Done')
        time.sleep(2)

        # Reset the GUI
        self.reset_gui()
        
