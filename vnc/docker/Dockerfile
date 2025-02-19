FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    python3-websockify \
    novnc \
    lxde-core \
    x11-xserver-utils \
    && rm -rf /var/lib/apt/lists/*

COPY config/novnc.nginx.conf /etc/nginx/sites-available/novnc
COPY config/novnc.service /etc/systemd/system/novnc.service
COPY scripts/start-novnc /usr/local/bin/
COPY scripts/start-desktop /usr/local/bin/
COPY config/vnc.token /usr/local/bin/

RUN chmod +x /usr/local/bin/start-novnc \
    && chmod +x /usr/local/bin/start-desktop

EXPOSE 5900 6080 6081

CMD ["/usr/local/bin/start-desktop"]
