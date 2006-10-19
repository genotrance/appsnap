import guisetup
import makegui
import version

if __name__ == '__main__':

    # Create a gui object
    gui = makegui.MakeGui(version.APPNAME + ' ' + version.APPVERSION, None, (400, 300))

    # Parse and run the GUI schema
    gui.parse_and_run(guisetup.schema, guisetup.Events({'gui' : gui}))

    # Run the app
    gui.run()