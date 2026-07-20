"""Telnet protocol client for Crestron HD-MD series HDMI switchers.

The HD-MD4X2-4K-E (and siblings such as the HD-MD6X2-4K-E and
HD-MD4X1-4K-E) expose a plain-text console on TCP port 23:

    > show output 1 route
    event output 1 route 4

    > conf output 1 route 2
    event output 1 route 2

Route number 0 means nothing is routed to that output. The device may
emit additional unsolicited ``event ...`` lines (for example
``event output 1 video output disabled true``) before the line we are
waiting for, so responses are scanned rather than read line-by-line.

The switcher only supports a small number of concurrent telnet
sessions, so a connection is opened per operation and guarded by a
lock, keeping this integration to a single session at a time.
"""

from __future__ import annotations

import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)

CONNECT_TIMEOUT = 10
RESPONSE_TIMEOUT = 5


class CrestronConnectionError(Exception):
    """Raised when the switcher cannot be reached or does not respond."""


class CrestronHdMd:
    """Minimal async client for the HD-MD telnet console."""

    def __init__(self, host: str, port: int = 23) -> None:
        self.host = host
        self.port = port
        self._lock = asyncio.Lock()

    async def async_get_routes(self, outputs: int) -> dict[int, int]:
        """Return {output_number: input_number} for all outputs."""
        async with self._lock:
            reader, writer = await self._connect()
            try:
                routes: dict[int, int] = {}
                for output in range(1, outputs + 1):
                    routes[output] = await self._command(
                        reader,
                        writer,
                        f"show output {output} route",
                        output,
                    )
                return routes
            finally:
                await self._close(writer)

    async def async_set_route(self, output: int, route: int) -> int:
        """Route ``route`` (0 = none) to ``output``; return confirmed route."""
        async with self._lock:
            reader, writer = await self._connect()
            try:
                return await self._command(
                    reader,
                    writer,
                    f"conf output {output} route {route}",
                    output,
                )
            finally:
                await self._close(writer)

    async def async_test_connection(self) -> None:
        """Probe the device; raise CrestronConnectionError on failure."""
        await self.async_get_routes(1)

    async def _connect(
        self,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        try:
            return await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                CONNECT_TIMEOUT,
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise CrestronConnectionError(
                f"Cannot connect to {self.host}:{self.port}: {err}"
            ) from err

    @staticmethod
    async def _close(writer: asyncio.StreamWriter) -> None:
        try:
            writer.close()
            await writer.wait_closed()
        except OSError:
            pass

    async def _command(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        command: str,
        output: int,
    ) -> int:
        """Send a command and wait for its ``event output N route M`` reply."""
        pattern = re.compile(rf"event output {output} route (\d+)")
        try:
            writer.write(command.encode("ascii") + b"\r\n")
            await writer.drain()

            buffer = ""
            deadline = asyncio.get_event_loop().time() + RESPONSE_TIMEOUT
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    raise CrestronConnectionError(
                        f"No route confirmation for {command!r}; "
                        f"received: {buffer!r}"
                    )
                chunk = await asyncio.wait_for(reader.read(256), remaining)
                if not chunk:
                    raise CrestronConnectionError(
                        f"Connection closed while waiting for reply "
                        f"to {command!r}"
                    )
                # Drop telnet negotiation / non-ASCII bytes.
                buffer += chunk.decode("ascii", errors="ignore")
                match = pattern.search(buffer)
                if match:
                    route = int(match.group(1))
                    _LOGGER.debug("%r -> output %s route %s", command, output, route)
                    return route
        except (OSError, asyncio.TimeoutError) as err:
            raise CrestronConnectionError(
                f"Error talking to {self.host}: {err}"
            ) from err
