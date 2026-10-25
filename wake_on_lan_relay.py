import socket
import subprocess
import time
import logging
from enum import Enum, auto
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# --- CONFIGURATION ---
try:
    TARGET_MAC = os.environ["TARGET_MAC"].lower()
    TARGET_UDP_PORT = int(os.environ["TARGET_UDP_PORT"])
    LISTEN_UDP_PORT = int(os.environ["LISTEN_UDP_PORT"])
    LISTENER_MAC_ADDRESS = os.environ["LISTENER_MAC_ADDRESS"].lower()
except KeyError as e:
    raise RuntimeError(f"Missing required environment variable: {e.args[0]}")

if LISTEN_UDP_PORT == TARGET_UDP_PORT:
    raise RuntimeError(
        "LISTEN_UDP_PORT must be different from TARGET_UDP_PORT to avoid relaying our "
        "own wake packet"
    )

# Configure logging
LOG_FILE = "/var/log/wake_on_lan_service.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=3)],
)


# --- FSM STATES ---
class WoLState(Enum):
    SYNC_HEADER = auto()  # Expecting 6 consecutive 0xFF bytes
    CAPTURE_MAC = auto()  # Reading the 1st MAC address (6 bytes)
    VERIFY_MAC = auto()  # Verifying remaining 15 MAC repetitions (90 bytes)
    VALID_FRAME = auto()  # Packet fully validated
    INVALID_FRAME = auto()  # Frame validation failed


class WoLParserFSM:
    """Byte-by-byte Finite State Machine for Wake-on-LAN Magic Packets."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.state = WoLState.SYNC_HEADER
        self.sync_count = 0
        self.captured_mac = bytearray()
        self.mac_byte_index = 0
        self.mac_repeat_count = 0

    def process_byte(self, b: int) -> WoLState:
        """Processes a single byte and transitions the FSM state."""

        # STATE 1: Expect 6 x 0xFF bytes
        if self.state == WoLState.SYNC_HEADER:
            if b == 0xFF:
                self.sync_count += 1
                if self.sync_count == 6:
                    self.state = WoLState.CAPTURE_MAC
            else:
                self.state = WoLState.INVALID_FRAME

        # STATE 2: Capture the target MAC address (6 bytes)
        elif self.state == WoLState.CAPTURE_MAC:
            self.captured_mac.append(b)
            if len(self.captured_mac) == 6:
                self.state = WoLState.VERIFY_MAC
                self.mac_repeat_count = 1  # 1st repetition is stored in captured_mac

        # STATE 3: Verify the remaining 15 repetitions (90 bytes)
        elif self.state == WoLState.VERIFY_MAC:
            expected_byte = self.captured_mac[self.mac_byte_index]

            if b == expected_byte:
                self.mac_byte_index = (self.mac_byte_index + 1) % 6
                if self.mac_byte_index == 0:
                    self.mac_repeat_count += 1

                if self.mac_repeat_count == 16:
                    self.state = WoLState.VALID_FRAME
            else:
                self.state = WoLState.INVALID_FRAME

        return self.state


def validate_packet(data: bytes) -> tuple[bool, str]:
    """Runs data through the FSM byte-by-byte."""
    fsm = WoLParserFSM()

    for b in data:
        state = fsm.process_byte(b)

        # Exit early if frame turns invalid or reaches completion
        if state in (WoLState.VALID_FRAME, WoLState.INVALID_FRAME):
            break

    if fsm.state == WoLState.VALID_FRAME:
        formatted_mac = ":".join(f"{b:02X}" for b in fsm.captured_mac)
        return True, formatted_mac

    return False, ""


def listen_for_wake():
    logging.info("Starting Wake-on-LAN Relay...")
    logging.info("Listening for packets on port %d...", LISTEN_UDP_PORT)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind(("0.0.0.0", LISTEN_UDP_PORT))
    except PermissionError:
        logging.error("Error: Run with sudo.")
        return

    while True:
        data, addr = sock.recvfrom(1024)
        sender_ip = addr[0]

        # Process packet byte-by-byte through the FSM
        is_valid, extracted_mac = validate_packet(data)

        if is_valid:
            logging.info("--- Valid Magic Packet Received from %s ---", sender_ip)
            logging.info("Extracted recipient MAC: %s", extracted_mac)

            if extracted_mac.lower() != LISTENER_MAC_ADDRESS:
                logging.info(
                    "Ignoring packet from (%s) we are not the recipients: "
                    "us != recipient (%s) != (%s).",
                    sender_ip,
                    LISTENER_MAC_ADDRESS,
                    extracted_mac,
                )
                continue

            logging.info(
                "Relaying Magic Packet to %s on port %d...", TARGET_MAC, TARGET_UDP_PORT
            )

            subprocess.run(["wakeonlan", "-p", str(TARGET_UDP_PORT), TARGET_MAC])
            continue

        else:
            logging.warning("Frame rejected from %s (%d bytes)", sender_ip, len(data))

        time.sleep(1)


if __name__ == "__main__":
    listen_for_wake()
