from django.core.management.commands.runserver import Command as DjangoRunserverCommand
from django.conf import settings
from django import get_version as django_version
import os
import platform
import socket
import sys
import logging
from datetime import datetime


class Command(DjangoRunserverCommand):
    help = "Run the Django development server with an enhanced startup notification."

    def inner_run(self, *args, **options):
        addrport = options.get("addrport")
        host = "127.0.0.1"
        port = "8000"

        if addrport:
            if ":" in addrport:
                host_part, port_part = addrport.rsplit(":", 1)
                host = host_part or host
                port = port_part or port
            else:
                if addrport.isdigit():
                    port = addrport
                else:
                    host = addrport

        resolved_host_display = host
        if host in ("0.0.0.0", "::"):
            try:
                resolved_host_display = socket.gethostbyname(socket.gethostname())
            except Exception:
                resolved_host_display = "127.0.0.1"

        settings_module = os.getenv("DJANGO_SETTINGS_MODULE") or "(not set)"
        inferred_env = (
            getattr(settings, "ENV", None)
            or os.getenv("DJANGO_ENV")
            or ("development" if getattr(settings, "DEBUG", False) else "production")
        )

        machine = platform.node()
        os_info = f"{platform.system()} {platform.release()}"
        python_info = f"{sys.version.split()[0]}"
        django_info = django_version()
        time_info = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        banner_lines = [
            "----------------------------------------",
            f"Environment    : {inferred_env}",
            f"Settings module: {settings_module}",
            f"Host binding   : {host}",
            f"Port binding   : {port}",
            f"Access URL     : http://{resolved_host_display}:{port}/",
            f"Machine        : {machine}",
            f"OS             : {os_info}",
            f"Python         : {python_info}",
            f"Django         : {django_info}",
            f"Started at     : {time_info}",
            "----------------------------------------",
        ]

        logger = logging.getLogger("django.server")
        logger.info("Django runserver started successfully:")
        for line in banner_lines:
            logger.info(line)

        return super().inner_run(*args, **options)
