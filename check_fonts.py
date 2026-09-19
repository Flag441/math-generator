import re, zlib, sys

raw = open(sys.argv[1], "rb").read()
blobs = [raw]
for m in re.finditer(rb"stream\r?\n", raw):
    s = m.end()
    e = raw.find(b"endstream", s)
    try:
        blobs.append(zlib.decompress(raw[s:e]))
    except Exception:
        pass
full = b"\n".join(blobs)

print(f"--- {sys.argv[1]}  ({len(raw)} バイト) ---")
for f in sorted(set(re.findall(rb"/BaseFont\s*/([A-Za-z0-9+\-,._]+)", full))):
    print("   ", f.decode())
print("   フォントの実体(FontFile)の数:", len(re.findall(rb"/FontFile[23]?[\s/>\[]", full)))