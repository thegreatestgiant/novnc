FROM ghcr.io/jonico/codespace-with-vnc-chrome-and-ps:latest

COPY fluxbox/menu /home/vscode/.fluxbox/

VOLUME [ "/var/lib/docker" ]


ENV DBUS_SESSION_BUS_ADDRESS="autolaunch:" \
	VNC_RESOLUTION="1440x768x16" \
	VNC_DPI="96" \
	VNC_PORT="5901" \
	NOVNC_PORT="6080" \
	DISPLAY=":1" \
	LANG="en_US.UTF-8" \
	LANGUAGE="en_US.UTF-8"
ENTRYPOINT ["/usr/local/share/desktop-init.sh", "/usr/local/share/docker-init.sh" ]
CMD ["sleep", "infinity"]
