#!/usr/bin/env python3
"""
Extracteur de couleurs Spotify - Combine client Spotify et extraction de couleurs
"""

import time
import os
import logging
import threading
from .spotify_client_service import SpotifyClient
from .color_extractor_service import ColorExtractor


class SpotifyColorExtractor:
    def __init__(self, data_dir: str | None = None):
        self.spotify_client = SpotifyClient()
        self.color_extractor = ColorExtractor()

        self.current_track_image_url = None
        self.current_track_id = None

        self.color_cache = {}
        self.last_extraction_time = 0
        self.cache_duration = 5

        self.monitoring_enabled = True
        self.monitoring_thread = None
        self.spotify_check_interval = float(os.getenv("SPOTIFY_POLLING_INTERVAL", 3.0))
        self.last_spotify_check = 0

        self.stats = {"requests": 0, "cache_hits": 0, "extractions": 0, "errors": 0}
        self.verbose_logs = os.getenv("VERBOSE_SPOTIFY_LOGS", "false").lower() == "true"
        # Couleur de secours par défaut (peut être remplacée par utilisateur)
        self.default_fallback_rgb = (0x25, 0xD8, 0x65)  # #25d865
        self.start_monitoring()

    def set_default_fallback_hex(self, hex_color: str | None):
        try:
            if not hex_color or not isinstance(hex_color, str):
                return
            s = hex_color.strip()
            if s.startswith("#"):
                s = s[1:]
            if len(s) != 6:
                return
            r = int(s[0:2], 16)
            g = int(s[2:4], 16)
            b = int(s[4:6], 16)
            self.default_fallback_rgb = (r, g, b)
        except Exception:
            # Ne pas interrompre si parsing échoue
            pass

    def start_monitoring(self):
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        self.monitoring_enabled = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()
        if self.verbose_logs:
            logging.info("⚡ Surveillance active - Logs réduits")

    def _monitoring_loop(self):
        last_track_id = None
        last_is_playing = None
        while self.monitoring_enabled:
            try:
                current_time = time.time()
                if (
                    self.spotify_client.spotify_enabled
                    and current_time - self.last_spotify_check
                    >= self.spotify_check_interval
                ):
                    track_info = self.spotify_client.get_current_track()
                    self.last_spotify_check = current_time
                    if track_info:
                        current_track_id = track_info.get("id")
                        current_is_playing = track_info.get("is_playing", False)
                        track_changed = (last_track_id != current_track_id) and bool(
                            current_track_id
                        )
                        playstate_changed = last_is_playing != current_is_playing
                        if track_changed:
                            if self.verbose_logs:
                                logging.info(
                                    f"🎵 {track_info.get('artist', 'Unknown')} - {track_info.get('name', 'Unknown')}"
                                )
                            self.current_track_image_url = track_info.get("image_url")
                            self.current_track_id = current_track_id
                            self.color_cache.clear()
                            if current_is_playing:
                                new_color = self.extract_color()
                                if self.verbose_logs:
                                    logging.info(
                                        f"🎨 #{new_color[0]:02x}{new_color[1]:02x}{new_color[2]:02x}"
                                    )
                            last_track_id = current_track_id
                            last_is_playing = current_is_playing
                        elif playstate_changed:
                            if current_is_playing:
                                if self.verbose_logs:
                                    logging.info(
                                        f"▶️ {track_info.get('artist', 'Unknown')} - {track_info.get('name', 'Unknown')}"
                                    )
                                if self.current_track_id != current_track_id:
                                    self.current_track_image_url = track_info.get(
                                        "image_url"
                                    )
                                    self.current_track_id = current_track_id
                                    self.color_cache.clear()
                                new_color = self.extract_color()
                                if self.verbose_logs:
                                    logging.info(
                                        f"🎨 #{new_color[0]:02x}{new_color[1]:02x}{new_color[2]:02x}"
                                    )
                            else:
                                if self.verbose_logs:
                                    logging.info("⏸️ PAUSE")
                            last_is_playing = current_is_playing
                    else:
                        if last_track_id is not None or last_is_playing is not None:
                            if self.verbose_logs:
                                logging.info("🔇 STOP")
                            last_track_id = None
                            last_is_playing = None
                time.sleep(1)
            except Exception as e:
                logging.error(f"❌ Erreur monitoring: {e}")
                time.sleep(10)

    def extract_color(self):
        current_time = time.time()
        self.stats["requests"] += 1
        track_info = self.spotify_client.get_current_track()
        # Si pas de piste ou en pause => couleur de secours (toujours actualisée via state)
        if not track_info or not track_info.get("is_playing", False):
            return self._get_fallback_color()

        cache_key = f"color_{self.current_track_id}"
        if (
            cache_key in self.color_cache
            and current_time - self.last_extraction_time < self.cache_duration
        ):
            self.stats["cache_hits"] += 1
            return self.color_cache[cache_key]

        self.stats["extractions"] += 1
        try:
            if not self.current_track_image_url:
                if track_info and track_info.get("image_url"):
                    self.current_track_image_url = track_info["image_url"]
                    self.current_track_id = track_info.get("id")
                else:
                    return self._get_fallback_color()
            if not self.current_track_image_url:
                return self._get_fallback_color()
            image = self.color_extractor.download_image(self.current_track_image_url)
            if not image:
                return self._get_fallback_color()
            color = self.color_extractor.extract_primary_color(image)
            if self.current_track_id:
                cache_key = f"color_{self.current_track_id}"
                self.color_cache[cache_key] = color
            self.last_extraction_time = current_time
            return color
        except Exception as e:
            self.stats["errors"] += 1
            logging.error(f"❌ Erreur extraction couleur: {e}")
            return self._get_fallback_color()

    def _get_fallback_color(self):
        # Utiliser la couleur par défaut (paramétrable par utilisateur)
        return self.default_fallback_rgb

    def get_current_track_info(self):
        return self.spotify_client.get_current_track()

    def get_stats(self):
        return self.stats

    def exchange_code_for_tokens(self, authorization_code):
        return self.spotify_client.exchange_code_for_tokens(authorization_code)

    @property
    def spotify_client_id(self):
        return self.spotify_client.spotify_client_id

    @property
    def spotify_enabled(self):
        return self.spotify_client.spotify_enabled
