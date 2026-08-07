from __future__ import annotations

from pathlib import Path

from homeassistant.components import frontend
from homeassistant.core import HomeAssistant


async def async_register_panel(hass: HomeAssistant) -> None:
    panel_dir = Path(__file__).parent / 'frontend'

    frontend.async_register_built_in_panel(
        hass,
        component_name='iframe',
        sidebar_title='Malla',
        sidebar_icon='mdi:radio-tower',
        frontend_url_path='malla',
        config={
            'url': '/local/malla/index.html',
            'require_admin': False,
        },
    )