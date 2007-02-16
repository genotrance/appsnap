import distutils.core
import os.path
import py2exe
import sys
import version
import _winreg

# Class to build application
class build:
    # Constructor
    def __init__(self):
        self.get_dependencies()
        self.setup_py2exe()
        self.build_executable()
    
    # Get build dependencies
    def get_dependencies(self):
        self.sevenzip = self.get_registry_key(_winreg.HKEY_LOCAL_MACHINE,
                                              'SOFTWARE\\7-Zip',
                                              'Path'
                                              ) + os.path.sep + '7z.exe'
        if self.sevenzip == os.path.sep + '7z.exe' or not os.path.exists(self.sevenzip):
            self.error_out('7-Zip not available.')
            
        self.upx = os.path.expandvars('${systemroot}\\upx.exe')
        if not os.path.exists(self.upx):
            self.error_out('UPX not available.')
            
        self.nsis = self.get_registry_key(_winreg.HKEY_LOCAL_MACHINE,
                                          'SOFTWARE\\NSIS',
                                          '') + os.path.sep + 'makensis.exe'
        if self.nsis == os.path.sep + 'makensis.exe' or not os.path.exists(self.nsis):
            self.error_out('NSIS not available')
            
    # Initialize the Py2Exe variables
    def setup_py2exe(self):
        # Console executable
        self.console = [{
                         "script"         : "appsnap.py",
                         "icon_resources" : [(1, "appsnap.ico")]
               }]
        
        # GUI executable
        self.windows = [{
                         "script"         : "appsnapgui.py",
                         "icon_resources" : [(1, "appsnap.ico")]
                         }]
        
        # Py2Exe options
        self.options = {
                        "py2exe": {
                                   "packages" : ["encodings"],
                                   "optimize" : 2,
                                   "compressed" : 0,
                                   }
                       }
        
        # Resource files to include
        self.data_files = [(
                            "" , 
                            ["appsnap.ico","db.ini","config.ini",]
                            )]
        
        # Name of zip file to generate
        self.zipfile = "shared.lib"
        
        # Specify py2exe as a command line option
        sys.argv.append('py2exe')
            
    # Execute Py2Exe to generate executables
    def build_executable(self):
        distutils.core.setup(
                             console = self.console, 
                             windows = self.windows, 
                             options = self.options,
                             data_files = self.data_files, 
                             zipfile = self.zipfile)
        
    # Die on error
    def error_out(self, text):
        print text + ' Build failed.'
        sys.exit(1)

    #####
    # Helper Functions
    #####

    # Get data from the registry
    def get_registry_key(self, database, key, value):
        try:
            key = _winreg.OpenKey(database, key)
            data, temp = _winreg.QueryValueEx(key, value)
            _winreg.CloseKey(key)
        except WindowsError:
            data = ''
            
        return data
    
if __name__ == '__main__':
    build()