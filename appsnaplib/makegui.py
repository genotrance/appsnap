import re
import string
import widgets
import wx
import yaml

class MakeGui:
    # Create an application and top level frame
    def __init__(self, title="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        # Initialize list of all objects
        self.objects = {}

        # Create an application object
        self.objects['application'] = wx.App(False)

        # Setup internationalization
        self.objects['locale'] = wx.Locale(wx.LANGUAGE_DEFAULT)
        self.objects['locale'].AddCatalogLookupPathPrefix("locale")
        self.objects['locale'].AddCatalog("appsnap")
        print 'Locale = %s' % self.objects['locale'].GetName()
        print
    
        # Create a frame object
        self.objects['frame'] = wx.Frame(None, -1, title, pos, size, style)
        self.objects['application'].SetTopWindow(self.objects['frame'])

    # Run the GUI
    def run(self):
        # Show the frame
        self.objects['frame'].Show()

        # Start the application main loop
        self.objects['application'].MainLoop()

    # Parse a config string into a list of dictionaries usable in create(), execute() and bind()
    def parse(self, string):
        # List of objects
        objects = []

        # Use yaml parser
        schema = yaml.load(string)

        # Parse any standalone methods
        if schema.has_key('methods'): methods = schema['methods']
        else: methods = []

        # Parse any standalone events
        if schema.has_key('events'): events = schema['events']
        else: events = []

        # Parse the objects
        if schema.has_key('objects'):
            for o in schema['objects']:
                # Pull out methods if any
                if o.has_key('methods'):
                    ms = o['methods']
                    del o['methods']
                else: ms = []

                # Pull out events if any
                if o.has_key('events'):
                    es = o['events']
                    del o['events']
                else: es = []

                # Add object name field into each method and event
                name = o['name']
                for m in ms: m['name'] = name
                for e in es: e['name'] = name

                # Add objects, methods and events to main lists
                objects.append(o)
                methods.extend(ms)
                events.extend(es)

        # Return the parsed objects, methods and events
        return (objects, methods, events)

    # Create objects
    def create(self, objects):
         for i in range(len(objects)):
            # Pull out name and type
            object = objects[i]
            type = object['type']
            name = object['name']
            del object['type']
            del object['name']

            # Create the code to execute
            code = [type, "( "]
            for key, value in object.iteritems():
                # Remove escapers
                if key[0] == '^': key = key[1:]
                
                try:
                    if (key == 'parent'):
                        if (value.__str__() != 'None'):
                            code.append("%s=self.objects['%s']," % (key, value.__str__()))
                        else:
                            code.append("%s=None," % key)
                    elif (value.__str__() != "" and value.__str__()[0] == '~'):
                        code.append("%s=self.objects['%s']," % (key, value.__str_()[1:]))
                    else:
                        try:
                            if (eval(value.__str__())):
                                code.append("%s=%s," % (key, value.__str__()))
                        except (NameError, SyntaxError):
                            code.append("%s='%s'," % (key, value.__str__()))
                except UnicodeEncodeError:
                    code.append("%s=u\"%s\"," % (key, value))
            code[-1] = code[-1][:len(code[-1])-1] + " )"
            code = string.join(code, '')

            # Save in object list
            self.objects[name] = eval(code)
            try:
                print '>>> %s = %s\n... %s' % (name, code, self.objects[name].__str__())
            except UnicodeEncodeError:
                print '>>> %s = %s\n... %s' % (name.encode("utf-8"), code.encode("utf-8"), self.objects[name].__str__())

    # Run gui object methods
    def execute(self, methods):
        # Capture return values
        retval = []

        for i in range(len(methods)):
            # Pull out object and method
            m = methods[i]
            name = m['name']
            method = m['method']
            del m['name']
            del m['method']

            # Create the code to execute
            code = ["self.objects['%s'].%s( " % (name, method)]
            for key, value in m.iteritems():
                # Remove escapers
                if key[0] == '^': key = key[1:]

                try:
                    if (key == 'parent'):
                        code.append("%s=self.objects['%s']," % (key, value.__str__()))
                    elif (value.__str__() != "" and value.__str__()[0] == '~'):
                        code.append("%s=self.objects['%s']," % (key, value.__str__()[1:]))
                    else:
                        try:
                            if (type(eval(value.__str__()))):
                                code.append("%s=%s," % (key, value.__str__()))
                        except (NameError, SyntaxError):
                            code.append("%s=u\"%s\"," % (key, value.__str__()))
                except UnicodeEncodeError:
                    if value[0] == '~':
                        code.append("%s=self.objects[u\"%s\"]," % (key, value[1:]))
                    else:
                        code.append("%s=u\"%s\"," % (key, value))
            code[-1] = code[-1][:len(code[-1])-1] + " )"
            code = string.join(code, '')

            # Execute and capture return value
            ret = eval(code)
            retval.append(ret)
            try:
                print '>>> %s\n... %s' % (code, ret.__str__())
            except UnicodeEncodeError:
                print '>>> %s\n... %s' % (code.encode("utf-8"), ret.__str__())

        # Return captured returned values
        return retval

    # Bind gui events
    def bind(self, events, event_object):
        for i in range(len(events)):
            e = events[i]

            # Create the code to execute
            code = [e['type'], "( "]

            if (e['type'] in ['wx.EVT_SIZE', 'wx.EVT_MOVE', 'wx.EVT_LEFT_DOWN', 'wx.EVT_LEFT_UP', 'wx.EVT_LEFT_DCLICK', 'wx.EVT_SET_FOCUS', 'wx.EVT_KILL_FOCUS']):
                code.append("self.objects['%s']," % e['name'])
            else:
                code.append("self.objects['frame'], self.objects['%s'].GetId()," % e['name'])

            code.append("event_object.%s )" % e['method'])

            # Bind the event
            eval(string.join(code, ''))
            print '>>> %s' % code

     # Parse and run a schema
    def parse_and_run(self, schema, event_object=None):
        # Parse the schema
        (objects, methods, events) = self.parse(schema)

        # Create the gui objects if any
        self.create(objects)

        # Run gui object methods if any
        self.execute(methods)

        # Bind gui events if any
        self.bind(events, event_object)

        # Setup the event object if possible
        if hasattr(event_object, 'setup'): event_object.setup()

   # Return a created object
    def get(self, name):
        return self.objects[name]
