# Wake-on-LAN Relay

This repository contains a Python script to act as a Wake-on-LAN (WOL) relay. It listens for incoming WOL packets and relays them to a specified target device.

## Features
- Listens for WOL packets on a specified UDP port.
- Relays the WOL magic packet to a target device.
- Prevents feedback loops by ignoring packets from the relay itself.
- Logs activity to a rotating log file.

## Prerequisites
- Python 3.6 or higher
- `wakeonlan` command-line tool
- `python-dotenv` library

## Installation
1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd wake-on-lan
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt

   # Raspberry Pi OS does not allow package installation in the root Python. Either installation needs to be don in a virtual environment or install the packages using apt
   sudo apt install python3-dotenv
   ```

3. Create a `.env` file in the root directory following the schema in the [example.env](./example.env)

4. Ensure the `wakeonlan` command-line tool is installed. On Debian-based systems, you can install it with:
   ```bash
   sudo apt install wakeonlan
   ```

## Usage
To install the Wake-on-LAN relay as a systemd service, use the Makefile commands below:

### Install the Service
Run the following command to create and start the systemd service:
```bash
make install
```

### Uninstall the Service
To stop and remove the systemd service, run:
```bash
make uninstall
```

### Check the service status:
```bash
sudo systemctl status wake_on_lan_relay
```

## Logging
Logs are stored in `/var/log/wake_on_lan_service.log`. The log file rotates automatically when it reaches 1MB, keeping up to 3 backups.

## Setup tailscale
Install tailscale following official documentation
Obtain an authentication key
Authenticate the machine, run 
```bash
sudo tailscale up --auth-key <KEY>
```
then advertise the routes using
```bash
sudo tailscale set --advertise-routes=192.168.1.0/24
```
On the tailscale dashboard allow the route advertisement

To send a wake signal via tailscale:
- connect the source device to the tailscale network
- send the packet to the tailscale address exactly as it is, no need to use the broadcast.

## License
This project is licensed under the MIT License. See the LICENSE file for details.