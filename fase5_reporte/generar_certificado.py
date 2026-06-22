#!/usr/bin/env python3
# fase5_reporte/generar_certificado.py
#
# Lee el diff de Genie y los outputs de validacion de las Fases 3 y 4,
# y genera el certificado de compliance que cierra el ticket.

import os
import socket
from datetime import datetime

import yaml

BASE = os.path.dirname(os.path.abspath(__file__))
VARS_PATH = os.path.join(BASE, "..", "vars", "vars_001V-04.yaml")

with open(VARS_PATH, "r", encoding="utf-8") as f:
    V = yaml.safe_load(f)

AL = V["alumno"]
CLI = V["cliente"]
R = V["router"]

# Rutas de evidencia de las fases anteriores
NETCONF_OUT = os.path.join(BASE, "..", "fase3_validacion_netconf",
                           "evidencias", "output_validacion_netconf.txt")
RESTCONF_OUT = os.path.join(BASE, "..", "fase4_validacion_restconf",
                            "evidencias", "output_validacion_restconf.txt")
DIFF_DIR = os.path.join(BASE, "evidencias", "diff_001V-04")
CERT_PATH = os.path.join(BASE, "evidencias",
                         "certificado_compliance_001V-04.txt")


def leer(path):
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def conforme(texto):
    """CONFORME solo si aparece 'CONFORME' y NO 'NO CONFORME'."""
    t = texto.upper()
    return "CONFORME" in t and "NO CONFORME" not in t


def diff_tiene_cambios():
    if not os.path.isdir(DIFF_DIR):
        return False
    archivos = [a for a in os.listdir(DIFF_DIR)
                if os.path.isfile(os.path.join(DIFF_DIR, a))]
    for a in archivos:
        if os.path.getsize(os.path.join(DIFF_DIR, a)) > 0:
            return True
    return False


def main():
    netconf_txt = leer(NETCONF_OUT)
    restconf_txt = leer(RESTCONF_OUT)

    netconf_ok = conforme(netconf_txt)
    restconf_ok = conforme(restconf_txt)
    diff_ok = diff_tiene_cambios()

    compliance = "CONFORME" if (netconf_ok and restconf_ok) else "NO CONFORME"

    lineas = []
    lineas.append("=" * 64)
    lineas.append("       CERTIFICADO DE COMPLIANCE - IMPLEMENTACION DE RED")
    lineas.append("=" * 64)
    lineas.append("")
    lineas.append(f"Alumno          : {AL['nombre']}")
    lineas.append(f"Codigo          : {AL['codigo']}")
    lineas.append(f"Empresa cliente : {CLI['empresa']}")
    lineas.append(f"Equipo (host)   : {CLI['hostname']}")
    lineas.append(f"Generado en VM  : {socket.gethostname()}")
    lineas.append(f"Fecha/hora      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lineas.append("")
    lineas.append("-" * 64)
    lineas.append("PARAMETROS APLICADOS")
    lineas.append("-" * 64)
    lineas.append(f"  Hostname          : {CLI['hostname']}")
    lineas.append(f"  Loopback gestion  : {R['loopback_ip']} {R['loopback_mask']} (Loopback{R['loopback_id']})")
    lineas.append(f"  Descripcion WAN   : {R['descripcion_wan']}")
    lineas.append(f"  Banner            : {R['banner']}")
    lineas.append(f"  Servidor NTP      : {R['ntp_server']}")
    lineas.append("")
    lineas.append("-" * 64)
    lineas.append("RESULTADOS DE VALIDACION")
    lineas.append("-" * 64)
    lineas.append(f"  Validacion NETCONF  : {'CONFORME' if netconf_ok else 'NO CONFORME'}")
    lineas.append(f"  Validacion RESTCONF : {'CONFORME' if restconf_ok else 'NO CONFORME'}")
    lineas.append(f"  Diff Genie c/cambios: {'SI' if diff_ok else 'NO'}")
    lineas.append("")
    lineas.append("=" * 64)
    lineas.append(f"  RESULTADO DE COMPLIANCE: {compliance}")
    lineas.append("=" * 64)
    if compliance == "CONFORME":
        lineas.append("  El equipo cumple la configuracion corporativa y queda")
        lineas.append("  LISTO PARA OPERAR. Ticket de implementacion cerrado.")
    else:
        lineas.append("  El equipo NO cumple todos los criterios. Revisar Fase 2.")
    lineas.append("=" * 64)

    contenido = "\n".join(lineas)
    with open(CERT_PATH, "w", encoding="utf-8") as f:
        f.write(contenido + "\n")

    print(contenido)
    print(f"\n[i] Certificado guardado en: {CERT_PATH}")


if __name__ == "__main__":
    main()
