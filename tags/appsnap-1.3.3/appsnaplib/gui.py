import defines
import guisetup
import makegui
import pycurl
import StringIO
import string
import strings
import sys
import time
import traceback
import version
import wx
import wx.lib.dialogs

OLD_STDOUT = None
OLD_STDERR = None
gui = None

# Redirect stdout and stderr to memory file
def start_debug():
    OLD_STDOUT = sys.stdout
    OLD_STDERR = sys.stderr
    sys.stdout = StringIO.StringIO()
    sys.stderr = sys.stdout
    print '========================'
    print time.asctime()
    print '========================\n'

# Close memory file and restore stdout and stderr
def end_debug():
    if len(sys.argv) == 2 and (sys.argv[1] == '--debug' or sys.argv[1] == '-d'):
        # Save to debug.log
        dbg = open('debug.log', 'a')
        dbg.write(sys.stdout.getvalue().encode('utf-8'))
        dbg.close()
    
    sys.stdout.close()
    sys.stdout = OLD_STDOUT
    sys.stderr = OLD_STDERR
    
# Handle uncaught exceptions
def handle_exceptions(type, value, tb):
    # Create traceback log
    list = traceback.format_tb(tb, None) + traceback.format_exception_only(type, value)
    tracelog = '\nTraceback (most recent call last):\n' + "%-20s%s" % (string.join(list[:-1], ""), list[-1])
    sys.stderr.write(tracelog)
    
    # Create dialog message
    message = strings.UNCAUGHT_EXCEPTION
    message += '\n\n%s' % sys.stdout.getvalue()
    
    # Shutdown GUI
    global gui
    if gui != None:
        gui.objects['frame'].Hide()
        gui.objects['application'].ExitMainLoop()
        gui = None

    # Display in dialog
    app = wx.App(False)
    dlg = wx.lib.dialogs.ScrolledMessageDialog(None, message, strings.ERROR)
    dlg.ShowModal()
    
    # Save to debug.log
    dbg = open('debug.log', 'a')
    dbg.write(sys.stdout.getvalue().encode('utf-8'))
    dbg.close()

    # Restore streams
    sys.stdout.close()
    sys.stdout = OLD_STDOUT
    sys.stderr = OLD_STDERR
    
# Run the GUI
def appsnap_start():
    # Remap exception handler
    sys.excepthook = handle_exceptions
    
    # Start debug if requested
    start_debug()
    
    # Print version information
    print 'AppSnap = %s' % version.APPVERSION
    print 'wxPython = %s' % wx.VERSION_STRING
    print 'PyCurl = %s' % pycurl.version

    # Create a gui object
    global gui
    gui = makegui.MakeGui('%s %s' % (version.APPNAME, version.APPVERSION), None, (defines.GUI_WIDTH, defines.GUI_HEIGHT))

    # Parse and run the GUI schema
    gui.parse_and_run(guisetup.schema, guisetup.Events({'gui' : gui}))

    # Run the app
    gui.run()
    gui = None
    
    # End debug
    end_debug()
