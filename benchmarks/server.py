# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import numpy as np
import timeit
import base64
import os
import webbrowser
import json
from json import JSONEncoder
import math
from collections import OrderedDict
from functools import partial
from vispy.gl import _gl
from vispy.gl import _constants


# -----------------------------------------------------------------------------
# WebGL dynamic code generation
# -----------------------------------------------------------------------------

def convert_name(name):
    """Return the ES command name."""
    # Use WebGL syntax: there is no "gl" prefix and the first letter is
    # in lower case.
    # TODO: generate a dict with "GL name" ==> "WebGL name" and tweak it
    if name == 'glGet':
        return 'getParameter'
    elif name == 'glGenBuffers':
        return 'createBuffer'
    elif name == 'glGetShaderiv':
        return 'getShaderParameter'
    elif name == 'glGetProgramiv':
        return 'getProgramParameter'
    elif name.startswith('gl'):
        return name[2].lower() + name[3:]

        
        
def encode_data(data):
    """Return the Base64 encoding of a Numpy array."""
    return base64.b64encode(data)
        
def decode_data(s, dtype=None):
    """Return a Numpy array from its encoded Base64 string. The dtype
    must be provided (float32 by default)."""
    return np.fromstring(base64.b64decode(s), dtype=dtype)

class ArrayEncoder(json.JSONEncoder):
    """JSON encoder that handles Numpy arrays and serialize them with base64
    encoding."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return dict(ndarray=encode_data(obj))
        return json.JSONEncoder.default(self, obj)
        
def wrap_gl_command(command):
    """Return a JSON string wrapping a given command.
    A command is a tuple (gl_function_name, args)."""
    name_gl, args = command
    name = convert_name(name_gl)
    d = OrderedDict(
        name=name,
        args=args,
    )
    return d
    
def wrap_gl_commands(commands, indent=None):
    hash = os.urandom(16).encode('hex')
    d = OrderedDict(
        message_type='gl',
        hash=hash,
        commands=list(map(wrap_gl_command, commands)))
    try:
        return json.dumps(d, indent=indent, cls=ArrayEncoder, ensure_ascii=True), hash
    except:
        import pprint
        pprint.pprint(d, indent=4)
        raise

dt = 1.
class GLWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print("WebSocket opened")
        interval_ms = dt * 1000
        main_loop = tornado.ioloop.IOLoop.instance()
        self.sched = tornado.ioloop.PeriodicCallback(self.schedule_func, interval_ms, 
            io_loop=main_loop)
        self.sched.start()
        
    def schedule_func(self):
        try:
            self.send_commands()
        except:
            # If an exception happens, stop the server before showing the
            # exception.
            tornado.ioloop.IOLoop.instance().stop()
            raise
        
    x = np.random.randn(1000000).astype(np.float32)
    timer = {}
    def send_commands(self):
        commands = [('', self.x)]
        t0 = timeit.default_timer()
        message, hash = wrap_gl_commands(commands)
        t1 = timeit.default_timer()
        self.timer[hash] = timeit.default_timer()
        self.write_message(message)
        t2 = timeit.default_timer()
        print("Wrap: {d1}, send: {d2}".format(d1=(t1-t0),d2=(t2-t1)))

    def on_message(self, e):
        print(timeit.default_timer() - self.timer[e])
        
    def on_close(self):
        print("WebSocket closed")
        self.sched.stop()
        tornado.ioloop.IOLoop.instance().stop()

def run():
    webbrowser.open("client.html", new=2)
    application = tornado.web.Application([
            (r"/", GLWebSocket),
        ])
    application.listen(8888)
    main_loop = tornado.ioloop.IOLoop.instance()
    main_loop.start()
    
if __name__ == "__main__":
    run()
