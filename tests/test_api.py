#!/usr/bin/env python3

from spygraph.workers import main

if __name__ == "__main__":
    print("Starting API with log processing...")
    print("Press Ctrl+C to stop\n")

    main(host="127.0.0.1", port=8000)
