import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado import gen

init = False
class EchoWebSocket(tornado.websocket.WebSocketHandler):
    def open(self):
        global init
        if init:
            return
        print "WebSocket opened"
        interval_ms = 10
        main_loop = tornado.ioloop.IOLoop.instance()
        sched = tornado.ioloop.PeriodicCallback(self.schedule_func, interval_ms, 
            io_loop=main_loop)
        sched.start()
        init = True

    def on_message(self, message):
        print "Received:", message

    def on_close(self):
        print "WebSocket closed"
    
    def schedule_func(self):
        self.write_message("Python to JSON")

if __name__ == "__main__":
    application = tornado.web.Application([
            (r"/", EchoWebSocket),
        ])
    application.listen(8888)
    main_loop = tornado.ioloop.IOLoop.instance()    
    main_loop.start()
    
    