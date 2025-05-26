#!/usr/bin/env python3
"""
WebSocket Test Script for OTA System
"""
import socketio
import time
import sys

# Create a Socket.IO client
sio = socketio.Client()

# Event handlers
@sio.event
def connect():
    print("✅ Connected to OTA WebSocket server!")

@sio.event
def disconnect():
    print("❌ Disconnected from OTA WebSocket server")

@sio.on("update_check_complete")
def on_update_check(data):
    print(f"🔍 Update check complete: {data}")

@sio.on("update_applied")
def on_update_applied(data):
    print(f"📦 Update applied: {data}")

# Main function
def main():
    print("Connecting to WebSocket server...")
    try:
        sio.connect("http://localhost:5000")
        print("Connection successful! Waiting for events...")
        print("Open another terminal and run:")
        print("curl -X POST -H \"X-API-Key: admin-key-example\" http://localhost:5000/api/v1/check")
        print("\nPress Ctrl+C to exit")
        
        # Keep the script running until interrupted
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Error connecting to WebSocket server: {e}")
    except KeyboardInterrupt:
        print("Keyboard interrupt received, exiting...")
    finally:
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    main() 