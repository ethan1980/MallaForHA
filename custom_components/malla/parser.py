from datetime import datetime


PORT_NAMES = {
    0: "Unknown App",
    1: "Text",
    3: "Position",
    4: "Node Info",
    5: "Routing",
    67: "Telemetry",
    70: "Traceroute",
}


def parse_packet(packet):

    protocol = PORT_NAMES.get(
        packet.get("portnum"),
        f"Port {packet.get('portnum')}",
    )

    timestamp = (
        packet.get("rx_time")
        or packet.get("import_time_us", 0) / 1000000
    )

    time = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")

    return {
        "id": packet.get("id"),
        "time": time,
        "protocol": protocol,
        "from": packet.get("long_name"),
        "to": packet.get("to_long_name") or "Broadcast",
        "channel": packet.get("channel"),
        "rssi": packet.get("rx_rssi"),
        "snr": packet.get("rx_snr"),
        "hops": packet.get("hops"),
        "summary": build_summary(packet),
        "raw": packet.get("payload", ""),
    }


def build_summary(packet):

    port = packet.get("portnum")
    payload = packet.get("payload", "")

    if port == 1:
        return payload

    if port == 3:

        lat = None
        lon = None

        for line in payload.splitlines():

            line = line.strip()

            if line.startswith("latitude_i:"):
                lat = float(line.split(":")[1].strip()) / 10000000

            elif line.startswith("longitude_i:"):
                lon = float(line.split(":")[1].strip()) / 10000000

        if lat is not None and lon is not None:
            return f"📍 {lat:.5f}, {lon:.5f}"

        return "📍 Position"

    if port == 4:
        return parse_nodeinfo(payload)

    if port == 5:
        return parse_routing(payload)

    if port == 67:
        return parse_telemetry(payload)

    if port == 70:
        return parse_traceroute(payload)

    if port == 0:
        return "❓ Unknown payload"

    return payload if payload else "❓ Unknown payload"


def parse_nodeinfo(payload):

    short = None
    hw = None

    for line in payload.splitlines():

        line = line.strip()

        if line.startswith("short_name:"):
            short = line.split(":")[1].replace('"', "").strip()

        elif line.startswith("hw_model:"):
            hw = line.split(":")[1].strip()

    if hw and short:
        return f"👤 {hw} · {short}"

    if hw:
        return f"👤 {hw}"

    return "👤 Node Info"


def parse_routing(payload):

    for line in payload.splitlines():

        line = line.strip()

        if line.startswith("error_reason:"):
            return f"❌ {line.split(':')[1].strip()}"

    return "🛣️ Routing"


def parse_traceroute(payload):

    hops = payload.count("route:")

    return f"📡 {hops} hops"


def parse_telemetry(payload):

    for line in payload.splitlines():

        line = line.strip()

        if line.startswith("battery_level:"):
            return f"🔋 {line.split(':')[1].strip()}%"

    for line in payload.splitlines():

        line = line.strip()

        if line.startswith("ch1_voltage:"):
            return f"⚡ CH1 {line.split(':')[1].strip()}V"

    for line in payload.splitlines():

        line = line.strip()

        if line.startswith("voltage:"):
            return f"⚡ {line.split(':')[1].strip()}V"

    if "power_metrics" in payload:
        return "⚡ Power"

    if "device_metrics" in payload:
        return "📈 Device"

    return "🔋 Telemetry"