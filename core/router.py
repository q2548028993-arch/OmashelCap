import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Maps msg_type → handler function
HandlerMap = dict[str, Callable[[dict], None]]


class MessageRouter:
    """
    Routes incoming WebSocket messages to registered handlers by msg_type.
    Any unregistered msg_type is logged and dropped.
    """

    def __init__(self):
        self._handlers: HandlerMap = {}

    def register(self, msg_type: str, handler: Callable[[dict], None]) -> None:
        self._handlers[msg_type] = handler

    def dispatch(self, message: dict) -> None:
        msg_type = message.get("msg_type")
        error = message.get("error")

        if error:
            logger.error(
                f"API error [{msg_type}]: {error.get('message')} (code: {error.get('code')})"
            )
            return

        if msg_type is None:
            logger.warning(f"Message with no msg_type: {message}")
            return

        handler = self._handlers.get(msg_type)
        if handler:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Handler error for [{msg_type}]: {e}", exc_info=True)
        else:
            logger.debug(f"No handler for msg_type: {msg_type}")
