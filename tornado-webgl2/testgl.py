import numpy as np

from vispy import app
from vispy import gl

VS = """
attribute vec2 position;
attribute vec4 color;
varying vec4 v_color;
void main()
{
    gl_Position = vec4(position, 0., 1.);
    v_color = color;
}
"""
FS = """
varying vec4 v_color;
void main()
{
    gl_FragColor = v_color;
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

canvas = app.Canvas()

@canvas.connect
def on_paint(e):
    paint()
    
def paint():
    
    n = 100
    data = np.hstack((
        .2 * np.random.randn(n, 2),
        np.random.rand(n, 4)
    )).astype(np.float32)
    
    vs = compile_shader(VS, gl.GL_VERTEX_SHADER)
    fs = compile_shader(FS, gl.GL_FRAGMENT_SHADER)
    shaders_program = link_shader_program(vs, fs)
    
    buffer = gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, data, gl.GL_STATIC_DRAW)
    
    
    l = gl.glGetAttribLocation(shaders_program, "position")
    gl.glVertexAttribPointer(l, 2, gl.GL_FLOAT, gl.GL_FALSE, 0, None)
    gl.glEnableVertexAttribArray(l);
    
    lc = gl.glGetAttribLocation(shaders_program, "color")
    gl.glVertexAttribPointer(lc, 4, gl.GL_FLOAT, gl.GL_FALSE, 2 * 4, None)
    gl.glEnableVertexAttribArray(lc);
    
    gl.glUseProgram(shaders_program)
    
    gl.glViewport(0, 0, 500, 500)
    gl.glClearColor(0., 0., 0., 1.)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE)

    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
    
    gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, data.shape[0])
    
if __name__ == '__main__':
    canvas.show()
    app.run()
