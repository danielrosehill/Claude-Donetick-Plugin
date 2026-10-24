---
name: nfc-chore-tag
description: Write a Donetick chore link onto a physical NFC tag with a USB NFC reader, test it with a phone, then permanently lock the tag, so tapping it opens or completes that chore. Works with any PC/SC reader (ACR122U, ACR1252U, Identiv…) or an nfcpy-supported one (PN533, Sony RC-S380), and NTAG213/215/216 or Ultralight tags. Use for "make an NFC tag for the dishwasher chore", "write chore tags", "lock this tag", "what's on this tag".
---

# NFC chore tags

A tag holds one NDEF URI record, the same URL Donetick's own "Write NFC" button writes:

```
<public Donetick URL>/chores/<chore id>[?auto_complete=true]
```

Tapping it with a phone opens the chore in Donetick (web app, or the mobile app if it
handles the link). With `?auto_complete=true` the chore is marked done straight away, as
**whoever is signed in on that phone**, so each person's completions are credited to them.
Format confirmed from the Donetick frontend source (`src/views/Chores/components/ChoreModals.jsx`,
`getNFCUrl`, and `WriteNFCModal.jsx`) on 2026-10-24.

Script: `scripts/nfc_tag.py` in this skill's folder. It is a `uv` script, so run it directly. If
`${CLAUDE_PLUGIN_ROOT}` is unset (skill read from a catalogue), find the clone of
`danielrosehill/Claude-Donetick-Plugin`. Every write and lock is appended to
`${CLAUDE_USER_DATA:-~/.local/share/claude-plugins}/donetick/nfc-write-log.jsonl`
(UID → URL → label), which is the record of which tag is which.

## Before starting

1. **Public URL.** The tag must carry a URL the phones can reach from anywhere. Use
   `$DONETICK_PUBLIC_URL` if set. Otherwise ask, or use the value a household or family
   plugin config records. **Not** `DONETICK_BASE_URL` if that is a LAN IP: the tag would
   only work at home, and a locked tag can't be fixed.
2. **Reader.** `nfc_tag.py readers`.
   - PC/SC reader listed → backend `pcsc` (needs `pcscd`; `sudo systemctl start pcscd` if
     the list is empty with the reader plugged in).
   - `nfcpy_usb: true` → backend `nfcpy`. nfcpy and pcscd both want the USB device. If
     nfcpy can't open it, stop pcscd (or use `pcsc`).
   - Neither → the reader isn't detected. Check `lsusb` and replug it. Don't go on.
3. **Tags.** Use NTAG213/215/216 (cheap stickers and keyfobs). NTAG213 holds 144 bytes,
   plenty for a chore URL. Use blank or rewritable tags. A tag that is already locked can't
   be reused.

## Procedure (one tag)

1. **Resolve the chore**: `list_chores` / `get_chore` (see `list-chores`), and confirm the
   name and ID with the user.
2. **Auto-complete or open?** Default: auto-complete, since the point is recording chores
   with a tap. Use plain open for chores that need a note, a photo or subtasks ticked.
3. **Build and show the URL**: `nfc_tag.py url --base <public> --chore-id <id> [--auto-complete]`.
   For a quick sanity check, `write --url … --dry-run` shows the encoded bytes and a round-trip.
4. **Write**: ask the user to put the tag on the reader, then
   `nfc_tag.py write --url "<url>" --label "<chore name>" [--backend pcsc|nfcpy]`.
   The script refuses a locked tag, writes the record, reads it back, and fails on a
   mismatch.
5. **Phone test**: the user taps the tag with their phone and confirms the right chore opens.
   With auto-complete the test *does* complete the chore. Say so first, and undo it or
   reschedule in Donetick afterwards if needed.
6. **Lock** (permanent, ask for an explicit yes after the phone test):
   `nfc_tag.py lock --url "<same url>" --label "<chore name>" --i-understand-lock-is-permanent`.
   It refuses unless the tag still holds exactly that URL. It then sets the CC to read-only,
   the static and dynamic lock bits, and CFGLCK. This is the same sequence as nfcpy's
   NTAG21x `protect()`. It can't be undone: a changed URL, chore ID or domain means a new
   tag.
7. **Report** the UID, chore, URL and lock state. Suggest labelling the physical tag.

### Several tags

Loop the procedure, one tag at a time. Write all of them, phone-test all of them, then lock
all of them, so one bad URL pattern doesn't get locked across a batch. For large batches from
a CSV, `nfc-ops:bulk-write` is the generic route. This skill is for Donetick URLs.

## Not this skill

- Password-protecting a tag instead of locking it: `nfc-ops:password-protect`.
- Generic NDEF payloads (Wi-Fi, text, other URLs): `nfc-ops:write-tag`.
- Inspecting a tag that won't write: `nfc-ops:inspect-tag`, or `nfc_tag.py read`, which
  reports the model, capacity, lock state and current URL.

## Status

The script's NDEF encoding was checked byte for byte against `ndeflib` (2026-10-24). The
reader and tag I/O paths have not been run against hardware yet. Record the reader model
and the outcome here after the first real write.
