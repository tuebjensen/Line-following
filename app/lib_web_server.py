import aiohttp #Is there a better way?
from aiohttp import web
import asyncio
import aiofiles
import json



class WebServer:

    def __init__(self):
        self._is_running = False
        self._frame_encoded = None
        self._is_frame_encoded_changed = False
        self._websocket_lock = False

    def set_frame_encoded(self, frame_encoded):
        self._frame_encoded = frame_encoded
        self._is_frame_encoded_changed = True

    async def send_message(self, type, data):
        message = {
            'type': type,
            'data': data,
            'processedIds': self._processed_ids        
        }

        self._ws.send_str(json.dumps(message))
        
        self._processed_ids.clear()

    async def set_current_node(self, current_node):
        async with aiofiles.open('server_state.json', 'r') as file:
            await file.write(json.dumps({'currentNode': current_node}))
        self.send_message('server-state-update', {'currentNode': current_node})

    async def start_running(self, address, port, path_callback):
        if self._is_running:
            return
        self._is_running = True


        async def websocket_test(request):
            return web.FileResponse('website/websocket.html')

        async def index(request):
            return web.FileResponse('website/index.html')

        async def make_full_state():
            async with aiofiles.open('server_state.json', 'r') as file:
                server_state = json.loads(await file.read())
            async with aiofiles.open('client_state.json', 'r') as file:
                client_state = json.loads(await file.read())

            full_state = { 
                "clientState": client_state, 
                "serverState": server_state
            }

            return full_state

        async def set_server_state(server_state):
            async with aiofiles.open('server_state.json', 'r') as file:
                await file.write(json.dumps({server_state}))

        async def set_client_state(client_state):
            async with aiofiles.open('client_state.json', 'w') as file:
                await file.write(json.dumps(client_state))
            path_callback(client_state['path'])

        async def update_client_state(client_state):
            async with aiofiles.open('client-state.json', 'wr') as file:
                old_client_state = json.loads(await file.read())
                new_client_state = old_client_state | client_state
                await file.write(json.dumps(new_client_state))
            if 'path' in client_state:
                path_callback(client_state['path'])
            
        async def websocket_handler(request):   
            if self._ws is not None:
                raise web.HTTPConflict()
            self._ws = web.WebSocketResponse()
            self._processed_ids = []
            await self._ws.prepare(request)
            #async with aiofiles.open('state.json', 'r') as file:
            #    contents = await file.read()
            contents = await make_full_state()
            await self.send_message('full-state-update', contents) 

            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    message = json.loads(msg.data)
                    data = message['data']
                    if 'id' in message:
                        self._processed_ids.append(message['id'])
                    if message['type'] == 'server-state-update':
                        set_server_state(data)
                    elif message['type'] == 'client-state-update':
                        set_client_state(data)
                        
            self._ws = None
            self._processed_ids.clear()
            update_client_state({'path': []})
            return self._ws


        async def show_image(request):
            resp = web.StreamResponse(status=200, 
                              reason='OK', 
                              headers={'Content-Type': 'multipart/x-mixed-replace; boundary=frame'})
    
            # The StreamResponse is a FSM. Enter it with a call to prepare.
            await resp.prepare(request)

            await resp.write(b'--frame\r\n')
            while True:
                if self._is_frame_encoded_changed:
                    self._is_frame_encoded_changed = False       
                    await resp.write(
                        b'Content-Type: image/jpeg\r\n\r\n' 
                        + (self._frame_encoded if self._frame_encoded is not None else b'') 
                        + b'\r\n'
                        + b'--frame\r\n'
                    ) 
                    await resp.drain()
                await asyncio.sleep(0.05)   
        loop = asyncio.get_event_loop()
        app = web.Application(loop=loop)
        app.router.add_route('GET', '/websocket', websocket_test)
        app.router.add_route('GET', '/', index)
        app.router.add_route('GET', '/video', show_image)
        app.router.add_routes([web.get('/self._ws', websocket_handler)])
        app.add_routes([web.static('/assets', 'website/assets')])
        

        return await loop.create_server(app.make_handler(), address, port)

        