# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import numpy as np
import json
import math
from collections import OrderedDict
from functools import partial
from vispy.gl import _gl
from vispy.gl import _constants


# -----------------------------------------------------------------------------
# WebGL dynamic code generation
# -----------------------------------------------------------------------------
class GLRecorder(object):
    """Capture all GL commands with the adequate arguments.
    
    TODO: capture the output for some annotated functions.
    """
    def __init__(self):
        self.clear()
        
    def clear(self):
        self.commands = []
        
    def _record(self, name, *args):
        self.commands.append((name, args))
        
    def __getattr__(self, name):
        try:
            return getattr(_constants, name)
        except AttributeError:
            return partial(self._record, name)        
gl = GLRecorder()

def wrap_gl_command(command):
    """Return a JSON string wrapping a given command.
    A command is a tuple (gl_function_name, args)."""
    name, args = command
    # Use WebGL syntax: there is no "gl" prefix and the first letter is
    # in lower case.
    if name.startswith('gl'):
        name = name[2].lower() + name[3:]
    d = OrderedDict(
        message_type='gl',
        command_name=name,
        args=args,
    )
    return json.dumps(d)

class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print "WebSocket opened"
        interval_ms = dt * 1000
        main_loop = tornado.ioloop.IOLoop.instance()
        self.sched = tornado.ioloop.PeriodicCallback(self.schedule_func, interval_ms, 
            io_loop=main_loop)
        self.sched.start()
        
    def schedule_func(self):
        # Flush the list of GL commands to send.
        gl.clear()
        # Call on_paint to generate the list of GL commands.
        on_paint(None)
        # Send the list of commands to the browser, command after command.
        self.send_commands()
        
    def send_commands(self):
        for command in gl.commands:
            self.write_message(wrap_gl_command(command))    

    def on_close(self):
        print "WebSocket closed"
        self.sched.stop()

def run():
    application = tornado.web.Application([
            (r"/", EchoWebSocket),
        ])
    application.listen(8888)
    main_loop = tornado.ioloop.IOLoop.instance()    
    main_loop.start()
    

# -----------------------------------------------------------------------------
# Rendering functions
# -----------------------------------------------------------------------------
t = 0.
dt = .01
def on_paint(e):
    global t
    c = abs(math.sin(t))
    gl.glClearColor(c, c, c, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    t += dt

if __name__ == "__main__":
    run()
