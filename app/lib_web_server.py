import aiohttp #Is there a better way?
from aiohttp import web
import asyncio
import aiofiles
import json



class VideoStreaming:

    def __init__(self):
        self._is_running = False
        self._frame_encoded = None
        self._is_frame_encoded_changed = False

    def set_frame_encoded(self, frame_encoded):
        self._frame_encoded = frame_encoded
        self._is_frame_encoded_changed = True

    async def start_running(self, address, port, path_callback):
        if self._is_running:
            return
        self._is_running = True

        async def websocket_test(request):
            return web.FileResponse('website/websocket.html')

        async def index(request):
            return web.FileResponse('website/index.html')

        lock = False
        async def websocket_handler(request):
            if self.lock:
                raise web.HTTPConflict()
            self.lock = True
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            async with aiofiles.open('state.json', 'r') as f:
                contents = await f.read()
            await ws.send_str(contents) 
        
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    async with aiofiles.open('client_state.json', 'w') as file:
                        message_data = msg.data
                        await file.write(message_data)
                        data = json.loads(msg.data)
                    path_callback(data["path"])
            lock = False
            return ws


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
        app.router.add_routes([web.get('/ws', websocket_handler)])

        return await loop.create_server(app.make_handler(), address, port)

        