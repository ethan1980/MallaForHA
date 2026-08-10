from __future__ import annotations
from aiohttp import web

from custom_components.malla.api import _LOGGER
from homeassistant.components import frontend
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import HomeAssistantView
from datetime import datetime, timezone
from .const import DOMAIN

class MallaChatView(HomeAssistantView):
    url = "/api/malla/chat"
    name = "api:malla:chat"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        domain_data = self.hass.data.get("malla", {})

        chat = []

        for api in domain_data.values():
            chat = getattr(api, "chat", [])
            if chat:
                break

        return web.json_response(chat)

class MallaSendView(HomeAssistantView):
    url = "/api/malla/send"
    name = "api:malla:send"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def post(self, request: web.Request) -> web.Response:
        data = await request.json()

        message = (data.get("message") or "").strip()
        channel = (data.get("channel") or "SFNarrow").strip()

        if not message:
            return web.json_response(
                {"ok": False, "error": "Mensaje vacío"},
                status=400,
            )

        # Actualizar helpers que ya usa tu script
        await self.hass.services.async_call(
            "input_text",
            "set_value",
            {
                "entity_id": "input_text.mensaje_meshtastic",
                "value": message,
            },
            blocking=True,
        )

        await self.hass.services.async_call(
            "input_select",
            "select_option",
            {
                "entity_id": "input_select.canal_meshtastic",
                "option": channel,
            },
            blocking=True,
        )

        # Ejecutar el script que ya funciona
        await self.hass.services.async_call(
            "script",
            "enviar_meshtastic",
            {},
            blocking=True,
        )

        return web.json_response({"ok": True})

class MallaChannelsView(HomeAssistantView):
    url = "/api/malla/channels"
    name = "api:malla:channels"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        channels = []

        for state in self.hass.states.async_all():
            entity_id = state.entity_id

            if (
                entity_id.startswith("meshtastic.")
                and "_channel_" in entity_id
            ):
                raw = entity_id.split("_channel_", 1)[1]

                # Capitalización amigable
                if raw.lower() == "sfnarrow":
                    name = "SFNarrow"
                elif raw.lower() == "longfast":
                    name = "LongFast"
                elif raw.lower() == "mediumslow":
                    name = "MediumSlow"
                else:
                    name = raw.capitalize()

                channels.append(name)

        channels = sorted(set(channels))

        return web.json_response(channels)

class MallaNodesView(HomeAssistantView):
    url = "/api/malla/nodes"
    name = "api:malla:nodes"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request) -> web.Response:
        domain_data = self.hass.data.get(DOMAIN, {})

        if not domain_data:
            return web.json_response([])

        api = next(iter(domain_data.values()))

        data = await self.hass.async_add_executor_job(
            lambda: api._get("packets", limit=50)
        )

        _LOGGER.warning("MALLA NODES RAW: %s", data)

        if not data:
            return web.json_response([])

        packets = data.get("packets", [])

        now = datetime.now()

        nodes_by_id = {}

        for packet in packets:
            node_id = packet.get("from_node_id")

            if not node_id:
                continue

            import_time = packet.get("import_time_us")

            if not import_time:
                continue

            dt = datetime.fromtimestamp(import_time / 1_000_000)

            existing = nodes_by_id.get(node_id)

            if existing and existing["last_seen_dt"] >= dt:
                continue

            delta = now - dt
            minutes = int(delta.total_seconds() // 60)

            if minutes < 1:
                last_seen_human = "ahora mismo"
            elif minutes == 1:
                last_seen_human = "hace 1 min"
            elif minutes < 60:
                last_seen_human = f"hace {minutes} min"
            else:
                hours = minutes // 60
                last_seen_human = f"hace {hours} h"

            name = (
                packet.get("long_name")
                or packet.get("short_name")
                or node_id
            )

            nodes_by_id[node_id] = {
                "id": node_id,
                "name": name,
                "channel": packet.get("channel"),
                "last_seen": dt.isoformat(),
                "last_seen_human": last_seen_human,
                "online": minutes <= 5,
                "last_seen_dt": dt,
            }

        nodes = list(nodes_by_id.values())

        nodes.sort(
            key=lambda n: n["last_seen_dt"],
            reverse=True,
        )

        for node in nodes:
            node.pop("last_seen_dt", None)

        return web.json_response(nodes)

async def async_register_panel(hass: HomeAssistant) -> None:
    frontend.async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title="Malla",
        sidebar_icon="mdi:radio-tower",
        frontend_url_path="malla",
        config={
            "url": "/local/malla/index.html",
            "require_admin": False,
        },
    )

    hass.http.register_view(MallaChatView(hass))
    hass.http.register_view(MallaSendView(hass))
    hass.http.register_view(MallaChannelsView(hass))
    hass.http.register_view(MallaNodesView(hass))