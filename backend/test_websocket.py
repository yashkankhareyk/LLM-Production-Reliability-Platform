"""
WebSocket test client — run this to see live events.

Usage:
    python test_websocket.py

Then in another terminal, send a chat request:
    curl -X POST http://localhost:8000/v1/chat ...

You'll see events appear here in real-time.
"""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("Install websockets: pip install websockets")
    sys.exit(1)


# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

LAYER_COLORS = {
    "foundation": GREEN,
    "intelligence": BLUE,
    "orchestration": CYAN,
    "presentation": YELLOW,
}


def format_event(data: dict) -> str:
    """Format an event for pretty terminal output."""
    event_type = data.get("event_type", "unknown")
    layer = data.get("layer", "unknown")
    cid = data.get("correlation_id", "")[:8]
    payload = data.get("payload", {})
    timestamp = data.get("timestamp", "")

    color = LAYER_COLORS.get(layer, RESET)

    # Time (just HH:MM:SS)
    time_str = timestamp.split("T")[1][:8] if "T" in timestamp else timestamp

    # Icon based on event type
    if "started" in event_type:
        icon = "▶️ "
    elif "completed" in event_type:
        icon = "✅"
    elif "failed" in event_type:
        icon = "❌"
    elif "decision" in event_type:
        icon = "🔀"
    elif "trying" in event_type:
        icon = "🔄"
    elif "success" in event_type:
        icon = "✅"
    else:
        icon = "📡"

    # Build output
    output = (
        f"{color}{BOLD}[{time_str}] "
        f"{icon} [{layer}] {event_type}{RESET}"
        f"  {YELLOW}cid={cid}...{RESET}"
    )

    # Show important payload fields
    if payload:
        details = []
        for key in [
            "node", "provider", "model",
            "tokens_used", "latency_ms",
            "results_count", "best_score",
            "decision", "search_layer",
            "error", "query",
            "total_latency_ms", "search_path",
        ]:
            if key in payload:
                val = payload[key]
                if isinstance(val, float):
                    val = round(val, 2)
                details.append(f"{key}={val}")

        if details:
            output += f"\n    {', '.join(details)}"

    return output


async def listen():
    uri = "ws://localhost:8000/v1/ws"
    print(f"\n{BOLD}{'='*60}")
    print(f"  WebSocket Live Events Client")
    print(f"  Connecting to {uri}")
    print(f"{'='*60}{RESET}\n")

    try:
        async with websockets.connect(uri) as ws:
            print(f"{GREEN}✅ Connected!{RESET}")
            print(
                f"{YELLOW}Waiting for events... "
                f"(send a chat request in another terminal){RESET}\n"
            )
            print(f"Commands: type 'history', 'metrics', 'ping', 'status'\n")

            # Start a task to read user input
            async def read_input():
                loop = asyncio.get_event_loop()
                while True:
                    try:
                        line = await loop.run_in_executor(
                            None, sys.stdin.readline
                        )
                        line = line.strip()
                        if line:
                            await ws.send(line)
                            print(f"{CYAN}→ Sent: {line}{RESET}")
                    except Exception:
                        break

            # Start input reader
            input_task = asyncio.create_task(read_input())

            try:
                while True:
                    message = await ws.recv()
                    data = json.loads(message)

                    msg_type = data.get("type", "unknown")

                    if msg_type == "event":
                        print(format_event(data))
                        print()

                    elif msg_type == "connection":
                        print(
                            f"{GREEN}🔌 {data.get('message', '')}{RESET}"
                        )
                        print(
                            f"   Active connections: "
                            f"{data.get('active_connections', 0)}"
                        )
                        print()

                    elif msg_type == "history":
                        events = data.get("events", [])
                        print(
                            f"\n{BOLD}📜 Event History "
                            f"({data.get('count', 0)} events):{RESET}"
                        )
                        for evt in events:
                            print(format_event(evt))
                        print()

                    elif msg_type == "metrics":
                        print(f"\n{BOLD}📊 Live Metrics:{RESET}")
                        for key, val in data.items():
                            if key != "type":
                                print(f"   {key}: {val}")
                        print()

                    elif msg_type == "pong":
                        print(f"{GREEN}🏓 pong{RESET}\n")

                    elif msg_type == "status":
                        print(f"\n{BOLD}📋 Status:{RESET}")
                        for key, val in data.items():
                            if key != "type":
                                print(f"   {key}: {val}")
                        print()

                    elif msg_type == "error":
                        print(
                            f"{RED}⚠️  {data.get('message', '')}{RESET}\n"
                        )

                    else:
                        print(
                            f"{YELLOW}Unknown: {json.dumps(data, indent=2)}{RESET}\n"
                        )

            finally:
                input_task.cancel()

    except ConnectionRefusedError:
        print(
            f"\n{RED}❌ Cannot connect to {uri}{RESET}"
        )
        print(
            f"   Make sure Layer 5 is running: "
            f"python -m apps.presentation.main"
        )
    except Exception as e:
        print(f"\n{RED}❌ Error: {e}{RESET}")


if __name__ == "__main__":
    print(
        f"\n{BOLD}Tip:{RESET} While this is running, "
        f"open another terminal and send:"
    )
    print(
        f'  curl -X POST http://localhost:8000/v1/chat '
        f'-H "Content-Type: application/json" '
        f"-d '{{\"messages\": [{{\"role\": \"user\", "
        f"\"content\": \"hello\"}}], \"use_rag\": true}}'"
    )
    print()

    asyncio.run(listen())