#!/bin/bash

TARGET="10.67.162.106:21337"
KEY="now_you_see_me"

mkdir -p memory_hunt
echo "[*] Logging everything to ./memory_hunt/"
echo

# ------------------------------
# 1. WINDOW 1 — SPAM /unlock
# ------------------------------
echo "[*] Starting flooder for /unlock ..."
(
  while true; do
    curl -s -X POST http://$TARGET/unlock \
    -H "Content-Type: application/json" \
    -d '{"k":"'"$KEY"'"}' >> memory_hunt/unlock.log
  done
) &
PID_UNLOCK=$!

# ------------------------------
# 2. WINDOW 2 — GOBUSTER root
# ------------------------------
echo "[*] Starting gobuster on ROOT ..."
gobuster dir \
  -u http://$TARGET \
  -w /usr/share/wordlists/dirb/common.txt \
  -t 50 -x txt,html,png,jpg,svg \
  2>/dev/null | tee memory_hunt/gobuster-root.log &

PID_GB1=$!

# ------------------------------
# 3. WINDOW 3 — GOBUSTER /static
# ------------------------------
echo "[*] Starting gobuster on /static ..."
gobuster dir \
  -u http://$TARGET/static \
  -w /usr/share/wordlists/dirb/common.txt \
  -t 50 -x txt,html,png,jpg,svg \
  2>/dev/null | tee memory_hunt/gobuster-static.log &

PID_GB2=$!

# ------------------------------
# 4. WINDOW 4 — TCPDUMP SNIFFING
# ------------------------------
echo "[*] Starting tcpdump (HTTP sniffing)..."
sudo tcpdump -A host $(echo $TARGET | cut -d: -f1) \
  2>/dev/null | tee memory_hunt/tcpdump.log &
PID_TCP=$!

echo
echo "[*] All scanners running!"
echo "[*] Press ENTER to stop everything..."
read

# ------------------------------
# STOP EVERYTHING
# ------------------------------
kill $PID_UNLOCK $PID_GB1 $PID_GB2 $PID_TCP 2>/dev/null
echo "[*] Done. Check ./memory_hunt/ for findings!"
