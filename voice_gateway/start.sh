#!/bin/bash

# Start ngrok in the background if auth token is set
if [ -n "$NGROK_AUTH_TOKEN" ]; then
    echo "Starting ngrok tunnel..."
    ngrok config add-authtoken $NGROK_AUTH_TOKEN
    nohup ngrok http 8001 --log=stdout > /app/logs/ngrok.log 2>&1 &
    sleep 3
    echo "Ngrok started in background"
else
    echo "NGROK_AUTH_TOKEN not set, skipping ngrok"
fi

# Start the voice gateway
python voice_gateway.py
