## ✨ tblock guard ☠️

Only the essentials are published here: an encrypted payload (`payload.bin`) and a license‑aware bootstrapper (`bootstrap_install.py`). The real watcher + installer live inside the payload. When you launch the bootstrapper it prompts for your license key, calls the tblock license API, decrypts the payload in memory, and runs the hidden installer. That way authorized operators can deploy instantly while casual snoops see only ciphertext.

---

### 🔐 What you get after decryption

- **System service:** `tblock-watcher.service` tails your 3x-ui access log, disables torrent offenders, logs them once per run, and fires at most **one** webhook notification per user.
- **Webhook bundle:** a FastAPI app (plus README & Dockerfile) ready to receive DMCA alerts.
- **Full docs:** the decrypted package includes the complete README, context, `.env.example`, and requirements used by the real installer.

---

### 🖥️ Prerequisites on the VPS

```bash
sudo apt update
sudo apt install -y python3-pip git
sudo python3 -m pip install requests cryptography
```

Those two Python packages are all the bootstrapper needs.

---

### 🚀 Install steps (licensed VPS)

1. Make sure the license API is running (either your own deployment or ours) and note its URL.
2. Copy `bootstrap_install.py` and `payload.bin` to the VPS.
3. Run:

   ```bash
   python3 bootstrap_install.py
   ```

4. Enter your license when prompted. If accepted, the payload is decrypted in RAM and the real installer launches, asking for:
   - HTTP/HTTPS scheme & panel port
   - 3x-ui base path (no leading slash)
   - TLS domain (matches your certificate)
   - Panel credentials (optional 2FA)
   - Ban duration and optional webhook URL/token

5. When the installer finishes you can verify the watcher with:

   ```bash
   sudo systemctl status tblock-watcher.service
   sudo journalctl -u tblock-watcher.service -f
   ```

---

### 📡 Webhook endpoint

Inside the payload lives a FastAPI project you can deploy anywhere (DO App Platform, Fly.io, etc.). When enabled, the watcher posts JSON like:

```json
{
  "event": "torrent_blocked",
  "email": "user@example.com",
  "ip": "203.0.113.5",
  "recommended_review_hours": 5
}
```

Use it to alert users, integrate with ticketing, or trigger automated bans.

---

### 📝 Notes

- The bootstrapper won’t run until `requests` and `cryptography` are installed—do that once per VPS.
- Your 3x-ui instance still needs protocol sniffing + routing (bittorrent → blackhole). Without that, the watcher can’t see torrent traffic.
- To uninstall:  
  `sudo systemctl disable --now tblock-watcher.service && sudo rm /etc/systemd/system/tblock-watcher.service`
- License keys are enforced server-side. Only holders of a valid key can decrypt the payload—please treat your key like any other credential.

Enjoy the guard! 🛡️
