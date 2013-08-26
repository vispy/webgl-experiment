# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------
import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import numpy as np
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
class GLRecorder(object):
    """Capture all GL commands with the adequate arguments.
    """
    def __init__(self):
        self.clear()
        
    def clear(self):
        self.commands = []
        
    def _record(self, name, *args):
        self.commands.append((name, args))
        # Return the index of the current command.
        return dict(output_index=(len(self.commands) - 1))
        
    def __getattr__(self, name):
        try:
            return getattr(_constants, name)
        except AttributeError:
            if name in _gl._glfunctions:
                return partial(self._record, name)
        raise AttributeError(name)
gl = GLRecorder()

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

class MyEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, np.ndarray):
            # TODO: use base64 encoding
            return dict(ndarray=o.ravel().tolist())
        return super(MyEncoder, self).default(o)
        
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
    d = OrderedDict(
        message_type='gl',
        commands=list(map(wrap_gl_command, commands)))
    try:
        return json.dumps(d, indent=indent, cls=MyEncoder)
    except:
        import pprint
        pprint.pprint(d, indent=4)
        raise

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
            # Flush the list of GL commands to send.
            gl.clear()
            # Call on_paint to generate the list of GL commands.
            on_paint(None)
            # Send the list of commands to the browser, command after command.
            self.send_commands()
        except:
            # If an exception happens, stop the server before showing the
            # exception.
            tornado.ioloop.IOLoop.instance().stop()
            raise
        
    def send_commands(self):
        message = wrap_gl_commands(gl.commands, indent=4)
        # print message
        self.write_message(message)

    def on_close(self):
        print("WebSocket closed")
        self.sched.stop()

def run():
    webbrowser.open("client.html", new=2)
    application = tornado.web.Application([
            (r"/", GLWebSocket),
        ])
    application.listen(8888)
    main_loop = tornado.ioloop.IOLoop.instance()
    main_loop.start()
    
    
# -----------------------------------------------------------------------------
# Rendering functions
# -----------------------------------------------------------------------------

VS = """
attribute vec2 position;
void main()
{
    gl_Position = vec4(position, 0., 1.);
}
"""
FS = """
void main()
{
    gl_FragColor = vec4(1., 1., 0., .25);
}
"""

def compile_shader(source, type):
    shader = gl.glCreateShader(type)
    gl.glShaderSource(shader, source)
    gl.glCompileShader(shader)
    result = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
    if not(result):
        raise RuntimeError(gl.glGetShaderInfoLog(shader))
    return shader

def link_shader_program(vertex_shader, fragment_shader):
    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertex_shader)
    gl.glAttachShader(program, fragment_shader)
    gl.glLinkProgram(program)
    result = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
    if not(result):
        raise RuntimeError(gl.glGetProgramInfoLog(program))
    return program

t = 0.
dt = .1
def on_paint(e):
    global t
    
    data = .2 * np.random.randn(100, 2).astype(np.float32)
    
    vs = compile_shader(VS, gl.GL_VERTEX_SHADER)
    fs = compile_shader(FS, gl.GL_FRAGMENT_SHADER)
    shaders_program = link_shader_program(vs, fs)
    
    buffer = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, data, gl.GL_STATIC_DRAW)
    
    
    l = gl.glGetAttribLocation(shaders_program, "position")
    gl.glEnableVertexAttribArray(l);
    
    gl.glUseProgram(shaders_program)
    
    gl.glViewport(0, 0, 500, 500)
    gl.glClearColor(0., 0., 0., 1.)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
    gl.glVertexAttribPointer(l, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    
    gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, data.shape[0])
    
    t += dt

if __name__ == "__main__":
    run()
