from vispy import app
from vispy import gl

canvas = app.Canvas()

@canvas.connect
def on_paint(e):
    gl.glClearColor(0,0,0,1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

canvas.show()
app.run()
