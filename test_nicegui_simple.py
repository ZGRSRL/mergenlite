#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Basit NiceGUI test sayfası"""

from nicegui import ui

@ui.page('/')
def main():
    ui.label('MergenLite Test').classes('text-4xl font-bold text-blue-600')
    ui.label('Uygulama çalışıyor! ✅').classes('text-2xl text-green-600 mt-4')
    ui.label('Port 8082 aktif').classes('text-lg text-gray-600 mt-2')

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8083, show=True)

