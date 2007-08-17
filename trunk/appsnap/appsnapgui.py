import defines
import guisetup
import makegui
import pycurl
import sys
import time
import version
import wx

OLD_STDOUT = None

# Open debug log if -d specified, -s pipes to stdout
def start_debug():
    if len(sys.argv) == 2:
        if sys.argv[1] == '--debug' or sys.argv[1] == '-d':
            outfile = 'debug.log'
        elif sys.argv[1] == '--stdout' or sys.argv[1] == '-s':
            return
    else:
        outfile = 'nul'
    
    OLD_STDOUT = sys.stdout
    OLD_STDERR = sys.stderr
    sys.stdout = open(outfile, 'a')
    sys.stderr = sys.stdout
    print '\n========================'
    print time.asctime()
    print '========================\n'

# Close debug log if -d specified
def end_debug():
    if len(sys.argv) == 2 and (sys.argv[1] == '--stdout' or sys.argv[1] == '-s'):
        return
    
    sys.stdout.close()
    sys.stdout = OLD_STDOUT
    sys.stderr = OLD_STDERR

# Main function
if __name__ == '__main__':
    # Start debug if requested
    start_debug()
    
    # Print version information
    print 'AppSnap = ' + version.APPVERSION
    print 'wxPython = ' + wx.VERSION_STRING
    print 'PyCurl = ' + pycurl.version

    # Create a gui object
    gui = makegui.MakeGui(version.APPNAME + ' ' + version.APPVERSION, None, (defines.GUI_WIDTH, defines.GUI_HEIGHT))

    # Parse and run the GUI schema
    gui.parse_and_run(guisetup.schema, guisetup.Events({'gui' : gui}))

    # Run the app
    gui.run()
    
    # End debug
    end_debug()