from channels.routing import route
from .consumers import ws_message, ws_connect, ws_disconnect
from otree.channels.routing import channel_routing
from channels.routing import include, route_class

wageauction_routing = [route("websocket.connect",
                             ws_connect, path=r'^/(?P<group_name>\w+)$'),
                       route("websocket.receive",
                             ws_message, path=r'^/(?P<group_name>\w+)$'),
                       route("websocket.disconnect",
                             ws_disconnect, path=r'^/(?P<group_name>\w+)$'), ]

workpage_routing = [route("websocket.connect",
                          ws_connect, path=r'^/(?P<worker_code>\w+)$'),
                    route("websocket.receive",
                          ws_message, path=r'^/(?P<worker_code>\w+)$'),
                    route("websocket.disconnect",
                          ws_disconnect, path=r'^/(?P<worker_code>\w+)$'), ]

channel_routing += [
    include(wageauction_routing, path=r"^/wageauction"),
    include(workpage_routing, path=r"^/workpage"),
]
