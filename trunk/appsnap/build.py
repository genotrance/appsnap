import distutils.core
import os.path
import py2exe
import sys
import types
import version
import _winreg

# Class to build application
class build:
    # Constructor
    def __init__(self):
        self.get_dependencies()
        self.setup_py2exe()
        self.build_executable()
        self.rezip_zipfile()
        
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
        # Initialize
        self.py2exe = {}
        
        # Console executable
        self.py2exe['console'] = [{
                         "script"         : "appsnap.py",
                         "icon_resources" : [(1, "appsnap.ico")]
               }]
        
        # GUI executable
        self.py2exe['windows'] = [{
                         "script"         : "appsnapgui.py",
                         "icon_resources" : [(1, "appsnap.ico")]
                         }]
        
        # Py2Exe options
        self.py2exe['options'] = {
                        "py2exe": {
                                   "packages" : ["encodings"],
                                   "optimize" : 2,
                                   "compressed" : 0,
                                   }
                       }
        
        # Resource files to include
        self.py2exe['data_files'] = [(
                            "" , 
                            ["appsnap.ico","db.ini","config.ini",]
                            )]
        
        # Name of zip file to generate
        self.py2exe['zipfile'] = "shared.lib"
        
        # Specify py2exe as a command line option
        sys.argv.append('py2exe')
            
    # Execute Py2Exe to generate executables
    def build_executable(self):
        print 'Building executable using Py2Exe'
        command = 'distutils.core.setup('
        for key in self.py2exe:
            if type(self.py2exe[key]) is types.StringType:
                command += key + ' = "' + self.py2exe[key] + '", '
            else:
                command += key + ' = ' + self.py2exe[key].__str__() + ', '
        command = command[:-2] + ')'
        eval(command)
        
    # Rezip shared library
    def rezip_zipfile(self):
        if self.py2exe.has_key('zipfile'):
            print 'Rezipping shared library using 7-Zip'
            os.spawnl(os.P_WAIT, self.sevenzip, '-aoa', 'x', '-y', '"dist' + os.path.sep + self.py2exe['zipfile'] + '"', '-o"dist' + os.path.sep + 'shared"')
            
            os.chdir('dist' + os.path.sep + 'shared')
            os.spawnl(os.P_WAIT, self.sevenzip, 'a', '-tzip', '-mx9', '"..' + os.path.sep + self.py2exe['zipfile'] + '"', '-r')
            
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