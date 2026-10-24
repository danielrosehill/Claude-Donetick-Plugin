#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyscard>=2.0", "nfcpy>=1.0.4"]
# ///
"""Write (and optionally permanently lock) a Donetick chore URL onto an NFC tag.

Reader-agnostic: two backends.
  pcsc  - any PC/SC (CCID) USB reader via pcscd: ACR122U, ACR1252U, Identiv, ...
  nfcpy - readers nfcpy drives directly over USB: PN533, Sony RC-S380, ACR122U.
`auto` tries pcsc first, then nfcpy.

Tags: NFC Forum Type 2 (NTAG213/215/216, MIFARE Ultralight). The URL is a single
NDEF URI record, the same thing Donetick's own "Write NFC" button writes:
  <public base URL>/chores/<id>[?auto_complete=true]

Subcommands: url, readers, read, write, lock. Writes and locks are logged as JSONL.
Lock is separate on purpose: test the tag with a phone first, then lock.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

URI_PREFIXES = [  # NFC Forum URI RTD identifier codes, longest first
    (0x04, "https://"), (0x03, "http://"), (0x02, "https://www."), (0x01, "http://www."),
]
# CC byte 2 (data area size / 8) -> NTAG model, config page (from nfcpy tt2_nxp)
NTAG_BY_SIZE = {0x12: ("NTAG213", 41), 0x3E: ("NTAG215", 131), 0x6D: ("NTAG216", 227)}


def log_path() -> Path:
    base = os.environ.get("CLAUDE_USER_DATA") or os.path.join(
        os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "claude-plugins")
    p = Path(base) / "donetick" / "nfc-write-log.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def chore_url(base: str, chore_id: int, auto_complete: bool) -> str:
    url = f"{base.rstrip('/')}/chores/{chore_id}"
    return url + "?auto_complete=true" if auto_complete else url


# ---------- NDEF encoding (no library needed for one URI record) ----------

def ndef_uri_message(url: str) -> bytes:
    code, rest = 0x00, url
    for c, prefix in sorted(URI_PREFIXES, key=lambda x: -len(x[1])):
        if url.startswith(prefix):
            code, rest = c, url[len(prefix):]
            break
    payload = bytes([code]) + rest.encode()
    if len(payload) > 255:
        raise SystemExit("URL too long for a short NDEF record")
    # MB|ME|SR, TNF=well-known (0x01) -> 0xD1; type 'U'
    return bytes([0xD1, 0x01, len(payload)]) + b"U" + payload


def ndef_tlv(msg: bytes) -> bytes:
    if len(msg) >= 0xFF:
        raise SystemExit("NDEF message too long")
    return bytes([0x03, len(msg)]) + msg + b"\xFE"


def parse_uri_from_tlv(data: bytes) -> str | None:
    i = 0
    while i < len(data):
        t = data[i]
        if t == 0x00:
            i += 1
            continue
        if t == 0xFE:
            return None
        length = data[i + 1]
        val = data[i + 2:i + 2 + length]
        if t == 0x03 and len(val) >= 4 and val[1] == 1 and val[3:4] == b"U":
            plen = val[2]
            payload = val[4:4 + plen]
            prefix = dict(URI_PREFIXES).get(payload[0], "")
            return prefix + payload[1:].decode(errors="replace")
        i += 2 + length
    return None


# ---------- PC/SC backend ----------

class PcscTag:
    def __init__(self, timeout: int):
        from smartcard.CardRequest import CardRequest
        from smartcard.CardType import AnyCardType
        from smartcard.System import readers
        if not readers():
            raise RuntimeError("no PC/SC readers (is pcscd running and the reader plugged in?)")
        print(f"Present the tag to: {readers()[0]}", file=sys.stderr)
        svc = CardRequest(timeout=timeout, cardType=AnyCardType()).waitforcard()
        self.conn = svc.connection
        self.conn.connect()

    def apdu(self, cmd):
        data, sw1, sw2 = self.conn.transmit(list(cmd))
        if (sw1, sw2) != (0x90, 0x00):
            raise RuntimeError(f"APDU {bytes(cmd[:5]).hex()} failed: {sw1:02X}{sw2:02X}")
        return bytes(data)

    def uid(self) -> str:
        return self.apdu([0xFF, 0xCA, 0x00, 0x00, 0x00]).hex().upper()

    def read4(self, page: int) -> bytes:  # 4 pages = 16 bytes
        return self.apdu([0xFF, 0xB0, 0x00, page, 0x10])

    def write_page(self, page: int, data: bytes):
        assert len(data) == 4
        self.apdu([0xFF, 0xD6, 0x00, page, 0x04, *data])


def pcsc_info(tag: PcscTag) -> dict:
    head = tag.read4(0)  # pages 0-3
    cc = head[12:16]
    model, cfg = NTAG_BY_SIZE.get(cc[2], (f"Type2 (CC size 0x{cc[2]:02X})", None))
    return {
        "uid": tag.uid(), "model": model, "cfgpage": cfg, "cc": cc.hex(),
        "capacity": cc[2] * 8,
        "locked": head[10] != 0 or head[11] != 0 or (cc[3] & 0x0F) != 0,
        "ndef_formatted": cc[0] == 0xE1,
    }


def pcsc_read_url(tag: PcscTag, capacity: int) -> str | None:
    data = b""
    for page in range(4, 4 + (capacity + 15) // 4, 4):
        data += tag.read4(page)
        if 0xFE in data:
            break
    return parse_uri_from_tlv(data)


def pcsc_write(tag: PcscTag, info: dict, url: str):
    if not info["ndef_formatted"]:
        if info["cfgpage"] is None:
            raise RuntimeError("blank tag of unknown type; format it as NDEF first")
        tag.write_page(3, bytes([0xE1, 0x10, int(info["cc"][4:6], 16), 0x00]))
    blob = ndef_tlv(ndef_uri_message(url))
    if len(blob) > info["capacity"]:
        raise RuntimeError(f"payload {len(blob)} B exceeds tag capacity {info['capacity']} B")
    blob += b"\x00" * (-len(blob) % 4)
    for i in range(0, len(blob), 4):
        tag.write_page(4 + i // 4, blob[i:i + 4])


def pcsc_lock(tag: PcscTag, info: dict):
    """Permanent read-only, same sequence as nfcpy's NTAG21x lock-bit protect."""
    cfg = info["cfgpage"]
    if cfg is None:
        raise RuntimeError("lock supported for NTAG213/215/216 only on the pcsc backend")
    cc = bytearray(tag.read4(3)[0:4])
    cc[3] = 0x0F
    tag.write_page(3, bytes(cc))                    # CC: no write access
    tag.write_page(2, b"\x00\x00\xFF\xFF")          # static lock bytes (OR-ed by the tag)
    tag.write_page(cfg - 1, b"\xFF\xFF\xFF\x00")    # dynamic lock bytes
    access = bytearray(tag.read4(cfg)[4:8])
    if not access[0] & 0x40:
        access[0] |= 0x40                           # CFGLCK
        tag.write_page(cfg + 1, bytes(access))


# ---------- nfcpy backend ----------

def nfcpy_session(device: str, timeout: int, fn):
    import nfc
    with nfc.ContactlessFrontend(device) as clf:
        print(f"Present the tag to: {clf}", file=sys.stderr)
        deadline = time.time() + timeout
        tag = clf.connect(rdwr={"on-connect": lambda t: False},
                          terminate=lambda: time.time() > deadline)
        if not tag:
            raise RuntimeError("no tag presented before timeout")
        return fn(tag)


def nfcpy_info(tag) -> dict:
    nd = tag.ndef
    return {"uid": tag.identifier.hex().upper(), "model": str(tag.product),
            "capacity": nd.capacity if nd else None,
            "locked": bool(nd) and not nd.is_writeable, "ndef_formatted": bool(nd)}


def nfcpy_read_url(tag) -> str | None:
    if not tag.ndef:
        return None
    for r in tag.ndef.records:
        if getattr(r, "iri", None) or getattr(r, "uri", None):
            return getattr(r, "iri", None) or r.uri
    return None


def nfcpy_write(tag, url: str):
    import ndef
    if not tag.ndef:
        if not tag.format():
            raise RuntimeError("tag is not NDEF formatted and nfcpy could not format it")
    tag.ndef.records = [ndef.UriRecord(url)]


# ---------- commands ----------

def pick_backend(name: str) -> str:
    if name != "auto":
        return name
    try:
        from smartcard.System import readers
        if readers():
            return "pcsc"
    except Exception:
        pass
    return "nfcpy"


def run(args, mode: str):
    want_write = mode == "write"
    backend = pick_backend(args.backend)
    result = {"backend": backend}
    if backend == "pcsc":
        tag = PcscTag(args.timeout)
        info = pcsc_info(tag)
        result.update(info)
        result["before"] = pcsc_read_url(tag, info["capacity"]) if info["ndef_formatted"] else None
        if want_write:
            if info["locked"]:
                raise RuntimeError("tag is already locked/read-only; use a new tag")
            pcsc_write(tag, info, args.url)
            result["after"] = pcsc_read_url(tag, info["capacity"])
            if result["after"] != args.url:
                raise RuntimeError(f"read-back mismatch: {result['after']!r}")
        if mode == "lock":
            if info["locked"]:
                raise RuntimeError("tag is already locked")
            if result["before"] != args.url:
                raise RuntimeError(f"tag holds {result['before']!r}, not {args.url!r}; refusing to lock")
            pcsc_lock(tag, info)
            result["locked"] = pcsc_info(tag)["locked"]
    else:
        def fn(tag):
            info = nfcpy_info(tag)
            result.update(info)
            result["before"] = nfcpy_read_url(tag)
            if want_write:
                if info["locked"]:
                    raise RuntimeError("tag is already locked/read-only; use a new tag")
                nfcpy_write(tag, args.url)
                result["after"] = nfcpy_read_url(tag)
                if result["after"] != args.url:
                    raise RuntimeError(f"read-back mismatch: {result['after']!r}")
            if mode == "lock":
                if info["locked"]:
                    raise RuntimeError("tag is already locked")
                if result["before"] != args.url:
                    raise RuntimeError(f"tag holds {result['before']!r}, not {args.url!r}; refusing to lock")
                if not tag.protect():
                    raise RuntimeError("nfcpy could not lock this tag")
                result["locked"] = not tag.ndef.is_writeable
            return result
        nfcpy_session(args.device, args.timeout, fn)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    u = sub.add_parser("url", help="print the URL for a chore")
    u.add_argument("--base", default=os.environ.get("DONETICK_PUBLIC_URL"), required=not os.environ.get("DONETICK_PUBLIC_URL"))
    u.add_argument("--chore-id", type=int, required=True)
    u.add_argument("--auto-complete", action="store_true")

    sub.add_parser("readers", help="list PC/SC readers and nfcpy USB devices")

    for name in ("read", "write", "lock"):
        p = sub.add_parser(name)
        p.add_argument("--backend", choices=["auto", "pcsc", "nfcpy"], default="auto")
        p.add_argument("--device", default="usb", help="nfcpy device path (default usb)")
        p.add_argument("--timeout", type=int, default=30)
        if name in ("write", "lock"):
            p.add_argument("--url", required=True, help="URL to write / URL the tag must already hold before locking")
            p.add_argument("--label", default="")
        if name == "write":
            p.add_argument("--dry-run", action="store_true", help="show the encoded bytes and exit")
        if name == "lock":
            p.add_argument("--i-understand-lock-is-permanent", dest="lock_ack", action="store_true")

    args = ap.parse_args()

    if args.cmd == "url":
        print(chore_url(args.base, args.chore_id, args.auto_complete))
        return
    if args.cmd == "readers":
        try:
            from smartcard.System import readers
            print(json.dumps({"pcsc": [str(r) for r in readers()]}))
        except Exception as e:
            print(json.dumps({"pcsc_error": str(e)}))
        try:
            import nfc
            clf = nfc.ContactlessFrontend()
            print(json.dumps({"nfcpy_usb": bool(clf.open("usb"))}))
            clf.close()
        except Exception as e:
            print(json.dumps({"nfcpy_error": str(e)}))
        return
    if args.cmd == "lock" and not args.lock_ack:
        raise SystemExit("lock needs --i-understand-lock-is-permanent")
    if args.cmd == "write":
        if args.dry_run:
            tlv = ndef_tlv(ndef_uri_message(args.url))
            print(json.dumps({"url": args.url, "tlv_hex": tlv.hex(), "bytes": len(tlv),
                              "roundtrip": parse_uri_from_tlv(tlv)}))
            return

    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "cmd": args.cmd}
    try:
        res = run(args, args.cmd)
        entry.update(res, ok=True)
    except Exception as e:
        entry.update(ok=False, error=str(e))
    if args.cmd in ("write", "lock"):
        entry.update(url=args.url, label=args.label)
        with log_path().open("a") as f:
            f.write(json.dumps(entry) + "\n")
    print(json.dumps(entry, indent=2))
    sys.exit(0 if entry["ok"] else 1)


if __name__ == "__main__":
    main()
