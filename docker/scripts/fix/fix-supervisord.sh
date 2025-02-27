#!/bin/bash

# Fix the supervisord.conf file to remove problematic VNC password formatting
sed -i 's/%(ENV_VNC_PASSWORD:+-passwd)s %(ENV_VNC_PASSWORD)s//g' /etc/supervisor/conf.d/supervisord.conf

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf 