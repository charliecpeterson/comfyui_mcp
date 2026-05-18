"""Shared ComfyClient instance used by every tool/helper module.

Keeping it in its own module avoids a circular dependency: helpers can
`from .client import comfy` without importing server.py (which would in
turn import the helpers to register their tools).
"""
from .comfy import ComfyClient

comfy = ComfyClient()
