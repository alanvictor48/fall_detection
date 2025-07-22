import asyncio
import websockets
import json
import numpy as np
import threading
from tensorflow.keras.models import load_model
from collections import deque
from datetime import datetime

ESP32_URI = "ws://192.168.1.91/ws"
sliding_window = deque(maxlen=600)
model = load_model("models/128_bilstm_cnn_trained_model.h5")

connected_clients = set()
prediction_count = 0
last_prediction_time = None

# ⏱️ Atualiza contagem e horário da última predição
def log_prediction(score, resultado):
    global prediction_count, last_prediction_time
    prediction_count += 1
    last_prediction_time = datetime.now().strftime("%H:%M:%S")
    print(f"\n📊 Predição #{prediction_count} às {last_prediction_time}")
    print(f"📤 Score: {score:.4f} → {'✅ QUEDA' if resultado else '✅ SEM QUEDA'}")

async def frontend_server():
    server = await websockets.serve(frontend_handler, 'localhost', 8765)

    for sock in server.sockets:
        addr = sock.getsockname()
        print(f"🌐 Servidor WebSocket ouvindo em ws://{addr[0]}:{addr[1]}")
                    
    await server.wait_closed()

async def frontend_handler(websocket):
    print("🌐 Cliente frontend conectado.")
    connected_clients.add(websocket)
    try:
        async for _ in websocket:
            pass
    finally:
        print("❌ Cliente desconectado.")
        connected_clients.remove(websocket)

# 🌐 Envia predição a todos os clientes conectados
async def broadcast_to_clients(prediction):
    try:
        if connected_clients:
            message = json.dumps(prediction)
            await asyncio.gather(*[client.send(message) for client in connected_clients])
        else:
            print("⚠️ Nenhum cliente frontend conectado.")
    except Exception as err:
        print("Ocorreu um erro na transmissão")

# 🔄 Listener com reconexão automática ao ESP32
async def esp32_listener():
    while True:
        try:
            async with websockets.connect(ESP32_URI) as websocket:
                print("✅ Conectado ao ESP32!")
                await handle_esp32_data(websocket)
        except Exception as e:
            print("⚠️ Erro na conexão com o ESP32:", e)
            print("🔁 Tentando reconectar em 2 segundos...")
            await asyncio.sleep(2)

# 🔍 Processa os dados recebidos do ESP32
async def handle_esp32_data(websocket):
    global sliding_window
    
    async for message in websocket:
        data = json.loads(message)

        if isinstance(data, list):
            for sample in data:
                acc = sample["a"]
                gyro = sample["g"]
                features = acc + gyro
                sliding_window.append(features)

                if len(sliding_window) == 600:
                    window_np = np.array(sliding_window, dtype=np.float32).reshape(1, 600, 6)
                    
                    prediction = await asyncio.to_thread(
                        model.predict, 
                        [window_np[:, :, 0:3], window_np[:, :, 3:6]], 
                        verbose=0
                    )

                    score = float(prediction[0][0])
                    resultado = score > 0.5

                    log_prediction(score, resultado)

                    asyncio.create_task(broadcast_to_clients({
                        "score": score,
                        "resultado": resultado,
                        "count": prediction_count,
                        "time": last_prediction_time
                    }))

            await asyncio.sleep(0)
        else:
            print("⚠️ Formato inesperado:", data)

# 🚀 Inicializa os dois servidores
async def main():
    print("🚀 Inicializando sistema...")

    await asyncio.gather(
        esp32_listener(),
        frontend_server()
    )

if __name__ == "__main__":
    asyncio.run(main())
