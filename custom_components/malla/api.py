from __future__ import annotations

import logging
import time
import requests

from .parser import parse_packet

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://meshview.meshtastic.es/api"


class MeshViewAPI:

    def __init__(self, node_id):

        self.node_id = int(node_id)

        self.sent = []
        self.reported = []

        # Historial persistente de paquetes reportados
        self._reported_history = {}

        # Caché de paquetes ya procesados
        self._seen_cache = {}

        # Evita refrescos duplicados
        self._last_refresh = 0.0
        self._refresh_interval = 10
        
        # Evita refrescos simultáneos
        self._refreshing = False

        # Reintentos diferidos tras timeout
        self._failed_packets = {}

        # Reutiliza conexiones HTTPS
        self._session = requests.Session()

        # Circuit breaker cuando MeshView falla
        self._circuit_open_until = 0.0
        self._circuit_timeout = 300

    def _get(self, endpoint, **params):

        if time.time() < self._circuit_open_until:
            return None

        try:
            response = self._session.get(
                f"{BASE_URL}/{endpoint}",
                params=params,
                timeout=5,
            )
            response.raise_for_status()
            self._circuit_open_until = 0.0
            return response.json()
        except requests.exceptions.RequestException as err:
            self._circuit_open_until = time.time() + self._circuit_timeout
            _LOGGER.warning(
                "MeshView API error: %s (circuit abierto %ss)",
                err,
                self._circuit_timeout,
            )
            return None

    def refresh(self):

        if self._refreshing:
            _LOGGER.debug("Refresh ya en curso, se omite esta actualización.")
            return

        self._refreshing = True

        try:
            now = time.time()

            # Si acabamos de actualizar, reutilizamos los datos
            if now - self._last_refresh < self._refresh_interval:
                return

            self._last_refresh = now

            sent = self._get_sent()
            if sent is not None:
                self.sent = sent
            else:
                return

            reported = self._get_reported()
            if reported is not None:
                self.reported = reported

        finally:
            self._refreshing = False

        # Reintentos diferidos tras timeout
        self._failed_packets = {}

    def _get_sent(self, limit=25):

        data = self._get(
            "packets",
            from_node_id=self.node_id,
            limit=limit,
        )

        if data is None:
            return None

        packets = data.get("packets", [])

        packets.sort(
            key=lambda x: x["import_time_us"],
            reverse=True,
        )

        return [
            parse_packet(packet)
            for packet in packets
        ]

    def _get_reported(self, limit=15):

        data = self._get(
            "packets",
            limit=limit,
        )

        if data is None:
            return sorted(
                self._reported_history.values(),
                key=lambda x: x["time"],
                reverse=True,
            )

        packets = data.get("packets", [])
        history = self._reported_history

        MAX_NEW_PACKETS = 3
        processed = 0
        now = time.time()

        for packet in packets:
            packet_id = packet["id"]

            cached = self._seen_cache.get(packet_id)
            if isinstance(cached, dict):
                history[packet_id] = cached
                continue

            if cached is False:
                last_fail = self._failed_packets.get(packet_id, 0)
                if now - last_fail < 300:
                    continue

            if processed >= MAX_NEW_PACKETS:
                continue

            try:
                seen_data = self._get(f"packets_seen/{packet_id}")
                if seen_data is None:
                    self._failed_packets[packet_id] = now
                    continue

                seen = seen_data.get("seen", [])

                seen_info = next(
                    (item for item in seen if item["node_id"] == self.node_id),
                    None,
                )

                if not seen_info:
                    self._seen_cache[packet_id] = False
                    continue

                packet["rx_rssi"] = seen_info.get("rx_rssi")
                packet["rx_snr"] = seen_info.get("rx_snr")
                packet["hop_limit"] = seen_info.get("hop_limit")
                packet["hop_start"] = seen_info.get("hop_start")
                packet["rx_time"] = seen_info.get("rx_time")
                packet["channel"] = seen_info.get("channel")
                packet["hops"] = (packet.get("hop_start") or 0) - (packet.get("hop_limit") or 0)

                parsed = parse_packet(packet)
                history[packet_id] = parsed
                self._seen_cache[packet_id] = parsed
                self._failed_packets.pop(packet_id, None)
                processed += 1

            except Exception as err:
                _LOGGER.debug("Packet %s: %s", packet_id, err)
                self._seen_cache[packet_id] = False
                self._failed_packets[packet_id] = now

        while len(history) > 50:
            oldest = min(history, key=lambda k: history[k]["time"])
            del history[oldest]

        return sorted(
            history.values(),
            key=lambda x: x["time"],
            reverse=True,
        )