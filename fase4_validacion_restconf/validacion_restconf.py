#!/usr/bin/env python3
# fase4_validacion_restconf/validacion_restconf.py
#
# Valida la misma configuracion usando RESTCONF (HTTP+JSON).
# Consulta 4 endpoints, guarda cada respuesta JSON en evidencias/responses/
# y compara contra vars_001V-04.yaml.

import json
import os
import socket
import sys
from datetime import datetime

import requests
import urllib3
import yaml

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------------------------------------------------------------------
# Carga de variables
# ----------------------------------------------------------------------
BASE = os.path.dirname(os.path.abspath(__file__))
VARS_PATH = os.path.join(BASE, "..", "vars", "vars_001V-04.yaml")
RESP_DIR = os.path.join(BASE, "evidencias", "responses")
os.makedirs(RESP_DIR, exist_ok=True)

with open(VARS_PATH, "r", encoding="utf-8") as f:
    V = yaml.safe_load(f)

R = V["router"]
CLI = V["cliente"]
AL = V["alumno"]

BASE_URL = f"https://{R['ip']}/restconf/data"
HEADERS = {
    "Accept": "application/yang-data+json",
    "Content-Type": "application/yang-data+json",
}
AUTH = (R["usuario"], R["password"])

# ----------------------------------------------------------------------
# Metadatos
# ----------------------------------------------------------------------
print("=" * 60)
print("VALIDACION RESTCONF - EP3")
print(f"Script    : validacion_restconf.py")
print(f"Alumno    : {AL['nombre']} ({AL['codigo']})")
print(f"Fecha/hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Host VM   : {socket.gethostname()}")
print(f"Router    : {BASE_URL}")
print("=" * 60)


def get(endpoint, outfile):
    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, headers=HEADERS, auth=AUTH, verify=False, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    with open(os.path.join(RESP_DIR, outfile), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def deep_contains(obj, target):
    """Busca recursivamente 'target' como valor en un dict/list/str."""
    if isinstance(obj, dict):
        return any(deep_contains(v, target) for v in obj.values())
    if isinstance(obj, list):
        return any(deep_contains(v, target) for v in obj)
    return str(obj).strip() == str(target).strip() or str(target) in str(obj)


def main():
    loop_iface = f"Loopback{R['loopback_id']}"
    consultas = [
        ("Cisco-IOS-XE-native:native/hostname", "get_hostname.json"),
        (f"ietf-interfaces:interfaces/interface={loop_iface}", "get_loopback.json"),
        ("ietf-interfaces:interfaces/interface=GigabitEthernet1", "get_interfaces.json"),
        ("Cisco-IOS-XE-native:native/ntp", "get_ntp.json"),
    ]

    data = {}
    for endpoint, outfile in consultas:
        print(f"[GET] {endpoint}")
        data[outfile] = get(endpoint, outfile)
    print(f"\n[i] Respuestas JSON guardadas en: {RESP_DIR}\n")

    checks = []

    # 1) Hostname
    hn = data["get_hostname.json"].get("Cisco-IOS-XE-native:hostname")
    checks.append(("Hostname", hn, CLI["hostname"], hn == CLI["hostname"]))

    # 2) IP Loopback
    loop = data["get_loopback.json"].get("ietf-interfaces:interface", {})
    loop_ip = None
    try:
        loop_ip = loop["ietf-ip:ipv4"]["address"][0]["ip"]
    except (KeyError, IndexError, TypeError):
        loop_ip = None
    if loop_ip is None and deep_contains(data["get_loopback.json"], R["loopback_ip"]):
        loop_ip = R["loopback_ip"]
    checks.append(("IP Loopback", loop_ip, R["loopback_ip"], loop_ip == R["loopback_ip"]))

    # 3) Descripcion WAN
    gi = data["get_interfaces.json"].get("ietf-interfaces:interface", {})
    wan_desc = gi.get("description")
    checks.append(("Descripcion WAN", wan_desc, R["descripcion_wan"],
                   wan_desc == R["descripcion_wan"]))

    # 4) Servidor NTP (estructura variable -> busqueda profunda)
    ntp_ok = deep_contains(data["get_ntp.json"], R["ntp_server"])
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
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR de conexion] {e}")
        print("Revisa: RESTCONF e 'ip http secure-server' habilitados (Fase 2).")
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        sys.exit(2)
