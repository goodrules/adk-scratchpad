"""
Simple WebSocket client to test the ADK streaming chat app
"""
import asyncio
import json
import websockets


async def chat():
    """Connect to the websocket and send messages"""
    user_id = "test_user_123"
    uri = f"ws://localhost:8000/ws/{user_id}?is_audio=false"

    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as websocket:
        print("Connected! Type your messages (or 'quit' to exit):")

        # Task to receive messages from the agent
        async def receive_messages():
            try:
                async for message in websocket:
                    data = json.loads(message)

                    if "turn_complete" in data:
                        if data.get("turn_complete"):
                            print("\n[Turn complete]\n")
                        continue

                    if data.get("mime_type") == "text/plain":
                        print(data.get("data"), end="", flush=True)
            except Exception as e:
                print(f"\nError receiving: {e}")

        # Task to send messages to the agent
        async def send_messages():
            try:
                while True:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, "\nYou: "
                    )

                    if user_input.lower() == 'quit':
                        break

                    message = {
                        "mime_type": "text/plain",
                        "data": user_input
                    }
                    await websocket.send(json.dumps(message))
            except Exception as e:
                print(f"\nError sending: {e}")

        # Run both tasks concurrently
        await asyncio.gather(
            receive_messages(),
            send_messages()
        )


if __name__ == "__main__":
    asyncio.run(chat())
