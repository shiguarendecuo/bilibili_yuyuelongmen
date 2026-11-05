# -*- coding: utf-8 -*-
import asyncio
import json
import websockets
import blivedm
import blivedm.models.open_live as open_models
import blivedm.models.web as web_models

# ⚙️ 你的配置信息
ACCESS_KEY_ID = 'QldtkJqVGbhmYyNG0VTP3Deq'
ACCESS_KEY_SECRET = 'AfYEbO6WX6hWFuREboZAzwE9avtCW2'
APP_ID = 1795828964513
ROOM_OWNER_AUTH_CODE = 'F3H4TIHD8IDC6'

# 存放所有连上来的网页/Godot客户端
connected_websockets = set()

# 建立 8888 端口服务器
async def websocket_server(websocket):
    connected_websockets.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connected_websockets.remove(websocket)

# 把消息广播给所有客户端
async def broadcast_to_clients(data):
    if connected_websockets:
        message = json.dumps(data, ensure_ascii=False)
        await asyncio.gather(*[ws.send(message) for ws in connected_websockets])

# B站弹幕处理
class MyHandler(blivedm.BaseHandler):
    def _on_open_live_danmaku(self, client: blivedm.OpenLiveClient, message: open_models.DanmakuMessage):
        print(f'[收到指令] {message.uname}：{message.msg}')
        
        # 🔥 把更多用户信息打包发给 Godot
        game_data = {
            "uname": message.uname,
            "text": message.msg,
            "open_id": message.open_id,
            "uface": message.uface,                       # 用户头像链接
            "guard_level": message.guard_level,           # 大航海等级 (0普通, 3舰长)
            "fans_medal_level": message.fans_medal_level  # 粉丝牌等级
        }
        asyncio.create_task(broadcast_to_clients(game_data))

async def run_bilibili_client():
    client = blivedm.OpenLiveClient(
        access_key_id=ACCESS_KEY_ID,
        access_key_secret=ACCESS_KEY_SECRET,
        app_id=APP_ID,
        room_owner_auth_code=ROOM_OWNER_AUTH_CODE,
    )
    client.set_handler(MyHandler())
    client.start()
    try:
        await client.join()
    finally:
        await client.stop_and_close()

async def main():
    # 同时启动：1. 连B站  2. 开8888端口等Godot连过来
    server = await websockets.serve(websocket_server, "127.0.0.1", 8888)
    print("✅ 广播站已建好！端口: ws://127.0.0.1:8888")
    print("👉 等待B站弹幕和 Godot 客户端连接...")
    
    await asyncio.gather(
        run_bilibili_client(),
        server.wait_closed()
    )

if __name__ == '__main__':
    asyncio.run(main())