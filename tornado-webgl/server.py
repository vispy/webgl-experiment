import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen
import numpy as np
import json

dt = .01
t = 0.
class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        print "WebSocket opened"
        interval_ms = dt * 1000
        main_loop = tornado.ioloop.IOLoop.instance()
        self.sched = tornado.ioloop.PeriodicCallback(self.schedule_func, interval_ms, 
            io_loop=main_loop)
        self.sched.start()

    # def on_message(self, message):
        # print "Received:", message

    def on_close(self):
        print "WebSocket closed"
        self.sched.stop()
    
    def schedule_func(self):
        global t
        d = dict(x=np.cos(t), y=np.sin(t))
        self.write_message(json.dumps(d))
        t += dt

if __name__ == "__main__":
    application = tornado.web.Application([
            (r"/", EchoWebSocket),
        ])
    application.listen(8888)
    main_loop = tornado.ioloop.IOLoop.instance()    
    main_loop.start()
    
    