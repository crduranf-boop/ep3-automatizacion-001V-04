#!/usr/bin/env python3
# fase3_validacion_netconf/validacion_netconf.py
import os
import socket
import sys
from datetime import datetime
import xml.etree.ElementTree as ET

import yaml
from ncclient import manager

BASE = os.path.dirname(os.path.abspath(__file__))
VARS_PATH = os.path.join(BASE, "..", "vars", "vars_001V-04.yaml")
EVID = os.path.join(BASE, "evidencias")
os.makedirs(EVID, exist_ok=True)

with open(VARS_PATH, "r", encoding="utf-8") as f:
    V = yaml.safe_load(f)

R = V["router"]
CLI = V["cliente"]
AL = V["alumno"]

print("=" * 60)
print("VALIDACION NETCONF - EP3")
print("Script    : validacion_netconf.py")
print(f"Alumno    : {AL['nombre']} ({AL['codigo']})")
print(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Host VM   : {socket.gethostname()}")
print(f"Router    : {R['ip']}:830")
print("=" * 60)


def strip_ns(tree):
    for el in tree.iter():
        if isinstance(el.tag, str) and "}" in el.tag:
            el.tag = el.tag.split("}", 1)[1]
    return tree


def main():
    with manager.connect(
        host=R["ip"],
        port=830,
        username=R["usuario"],
        password=R["password"],
        hostkey_verify=False,
        allow_agent=False,
        look_for_keys=False,
        device_params={"name": "iosxe"},
    ) as m:
        resp = m.get_config(source="running")

    raw = resp.xml
    raw_path = os.path.join(EVID, "rpc_reply_raw.xml")
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw)
    print(f"\n[i] XML crudo guardado en: {raw_path} ({len(raw)} bytes)\n")

    root = strip_ns(ET.fromstring(raw))

    def first_text(path):
        el = root.find(path)
        return el.text.strip() if el is not None and el.text else None

    def subtree_has(tag, value):
        for sub in root.iter(tag):
            for el in sub.iter():
                if el.text and value in el.text:
                    return True
        return False

    hostname = first_text(".//hostname")

    loop_ip = loop_mask = None
    for loop in root.iter("Loopback"):
        name = loop.find("name")
        if name is not None and name.text and name.text.strip() == str(R["loopback_id"]):
            addr = loop.find(".//primary/address")
            mask = loop.find(".//primary/mask")
            loop_ip = addr.text.strip() if addr is not None and addr.text else None
            loop_mask = mask.text.strip() if mask is not None and mask.text else None

    wan_desc = None
    for gi in root.iter("GigabitEthernet"):
        name = gi.find("name")
        if name is not None and name.text and name.text.strip() == "1":
            d = gi.find("description")
            wan_desc = d.text.strip() if d is not None and d.text else None

    checks = []
    checks.append(("Hostname", hostname, CLI["hostname"], hostname == CLI["hostname"]))
    checks.append(("IP Loopback", loop_ip, R["loopback_ip"], loop_ip == R["loopback_ip"]))
    checks.append(("Mascara Loopback", loop_mask, R["loopback_mask"], loop_mask == R["loopback_mask"]))
    checks.append(("Descripcion WAN", wan_desc, R["descripcion_wan"], wan_desc == R["descripcion_wan"]))

    ntp_ok = subtree_has("ntp", R["ntp_server"])
    ntp_found = R["ntp_server"] if ntp_ok else "(no encontrado)"
    checks.append(("Servidor NTP", ntp_found, R["ntp_server"], ntp_ok))

    print("RESULTADO DE LA VALIDACION:")
    print("-" * 60)
    ok = 0
    for nombre, obtenido, esperado, passed in checks:
        estado = "[OK]  " if passed else "[FAIL]"
        if passed:
            ok += 1
        print(f"{estado} {nombre:<18} esperado='{esperado}'  obtenido='{obtenido}'")
    print("-" * 60)

    total = len(checks)
    print(f"\nCRITERIOS CONFORMES: {ok}/{total}")
    global_result = "CONFORME" if ok == total else "NO CONFORME"
    print(f"RESULTADO GLOBAL   : {global_result}")
    print("=" * 60)
    sys.exit(0 if ok == total else 1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        sys.exit(2)
