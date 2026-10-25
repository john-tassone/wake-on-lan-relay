SERVICE_NAME=wake_on_lan_service
SERVICE_FILE=/etc/systemd/system/$(SERVICE_NAME).service
SCRIPT_PATH=$(shell pwd)/wake_on_lan_relay.py

install:
	@echo "Creating systemd service file..."
	echo "[Unit]" > $(SERVICE_FILE)
	echo "Description=Wake-on-LAN Listener Service" >> $(SERVICE_FILE)
	echo "After=network.target" >> $(SERVICE_FILE)
	echo "" >> $(SERVICE_FILE)
	echo "[Service]" >> $(SERVICE_FILE)
	echo "ExecStart=/usr/bin/python3 $(SCRIPT_PATH)" >> $(SERVICE_FILE)
	echo "Restart=always" >> $(SERVICE_FILE)
	echo "RestartSec=5" >> $(SERVICE_FILE)
	echo "User=$$(whoami)" >> $(SERVICE_FILE)
	echo "StandardOutput=journal" >> $(SERVICE_FILE)
	echo "StandardError=journal" >> $(SERVICE_FILE)
	echo "" >> $(SERVICE_FILE)
	echo "[Install]" >> $(SERVICE_FILE)
	echo "WantedBy=multi-user.target" >> $(SERVICE_FILE)
	@echo "Reloading systemd daemon..."
	sudo systemctl daemon-reload
	@echo "Enabling and starting the service..."
	sudo systemctl enable $(SERVICE_NAME)
	sudo systemctl start $(SERVICE_NAME)
	@echo "Service installed and started."

uninstall:
	@echo "Stopping and disabling the service..."
	sudo systemctl stop $(SERVICE_NAME)
	sudo systemctl disable $(SERVICE_NAME)
	@echo "Removing systemd service file..."
	sudo rm -f $(SERVICE_FILE)
	@echo "Reloading systemd daemon..."
	sudo systemctl daemon-reload
	@echo "Service uninstalled."

.PHONY: install uninstall