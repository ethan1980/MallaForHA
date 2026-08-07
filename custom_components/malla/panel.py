from __future__ import annotations

from aiohttp import web

from homeassistant.components import frontend
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import HomeAssistantView


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