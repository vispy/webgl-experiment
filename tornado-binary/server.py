import numpy as np
from timeit import default_timer

import tornado.ioloop
import tornado.web
import tornado.websocket

N = 1000000
class EchoWebSocket(tornado.websocket.WebSocketHandler):
    x = np.random.rand(N).astype(np.float32)
    def open(self):
        self.t = default_timer()
        self.write_message(self.x.tostring(), binary=True)
        print "Sending message in", default_timer() - self.t
        
    def on_message(self, msg):
        print "Received response in", default_timer() - self.t
        tornado.ioloop.IOLoop.instance().stop()
        
if __name__ == "__main__":
    application = tornado.web.Application([
            (r"/", EchoWebSocket),
        ])
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
    