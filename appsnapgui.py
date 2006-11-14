import guisetup
import makegui
import sys
import time
import version

OLD_STDOUT = None

# Open debug log if -d specified
def start_debug():
    if len(sys.argv) == 2 and sys.argv[1] == '-d':
        OLD_STDOUT = sys.stdout
        sys.stdout = open('debug.log', 'a')
        print '\n========================'
        print time.asctime()
        print '========================\n'

# Close debug log if -d specified
def end_debug():    
    if len(sys.argv) == 2 and sys.argv[1] == '-d':
        sys.stdout.close()
        sys.stdout = OLD_STDOUT
        
# Main function
if __name__ == '__main__':
    # Start debug if requested
    start_debug()
    
    # Create a gui object
    gui = makegui.MakeGui(version.APPNAME + ' ' + version.APPVERSION, None, (guisetup.WIDTH, guisetup.HEIGHT))

    # Parse and run the GUI schema
    gui.parse_and_run(guisetup.schema, guisetup.Events({'gui' : gui}))

    # Run the app
    gui.run()
    
    # End debug
    end_debug()