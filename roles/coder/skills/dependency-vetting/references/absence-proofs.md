# Proving an absence: "it makes no network calls"

The rule: a NONE result is suspect until the same detector has caught the
thing with it switched on. Always run the positive control, record both.

## Recipe for a Python library with an opt-out env var

1. **In-process tripwire, no admin needed.** In a child script, monkeypatch
   `socket.socket.connect` BEFORE importing the library; append every addr;
   print the list at exit. Run twice from a parent that sets the env:
   - OFF: opt-out vars set, plus the cache-offline var for any model hub
     (`HF_HUB_OFFLINE=1`) so a weights fetch does not pollute the result
   - ON (control): opt-out vars AND `CI` unset — most libraries silence
     telemetry under `CI`, so an inherited `CI=1` fakes a clean run
   Expect NONE vs. N connects to one host:443, one per call.
2. **Read the gate.** `rg -n 'telemetry|DO_NOT_TRACK|https://' <site-packages>/<pkg>`
   — the endpoint URL and the gating function are usually plain Python.
   Quote the gate in the write-up; it proves the switch exists. Look for an
   install-id file written under `~` on first ON run and delete it after.
3. **Whole-machine capture only when a closed binary is in the loop.**
   Windows `pktmon` needs an elevated shell: hand the user one command line
   to run as Administrator, never route around the elevation. Its
   `etl2txt` output is **UTF-16** — open with `encoding="utf-16"` before any
   regex, or every search returns nothing and the "clean" result is a
   decoding artefact. Sanity-check the parse first: print the packet count
   and a few raw lines, expect the machine's normal traffic to be visible.
4. **Do not use `netstat -ano` polling as per-process proof.** A telemetry
   POST lives shorter than the poll interval and is never seen; a NONE from
   netstat is silence, not evidence. Tripwire = per-process; capture =
   whole-box.

## Write-up shape

    OFF: tripwire NONE over N calls; capture shows no <endpoint>
    ON (control): N connects to <ip>:443 = <URL quoted from the gate file>

Both lines, or the verdict is "not proven", said in those words.
