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