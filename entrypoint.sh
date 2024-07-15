#!/bin/bash

# Export environment variables
printenv | grep -v "no_proxy" >> /etc/environment

# Start cron
cron

# Tail the log file
tail -f /var/log/hw_scrapping.log /var/log/w2tj_scrapping.log
