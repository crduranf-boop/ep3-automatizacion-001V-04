# EP3 — Implementación de Automatización de Red con Compliance Auditado

**Alumno:** Cristobal Alonso Duran Figueroa — Código 001V-04
**Cliente:** Tecnologías Verdes SpA
**Equipo:** RTR-TECVERD (Cisco CSR1000v)
**Asignatura:** DRY7122 — Programación y Redes Virtualizadas (SDN-NFV)

---

## 1. Objetivo del proyecto

Se incorporó un router nuevo (Cisco CSR1000v) a la red corporativa de Tecnologías
Verdes SpA, aplicando de forma automatizada y reproducible la configuración estándar
de la empresa. El objetivo final fue dejar el equipo certificado y listo para operar,
con evidencia auditable de cada paso del ciclo de implementación.

## 2. Alcance

Dentro del alcance: documentación del estado inicial, habilitación de los servicios
de automatización (NETCONF/RESTCONF/HTTPS) y aplicación de la configuración
corporativa (hostname, banner, NTP, descripción de interfaz WAN e interfaz Loopback
de gestión), más su validación independiente por dos protocolos y el certificado de
compliance.

Fuera del alcance: enrutamiento dinámico, políticas de seguridad/ACL, QoS, alta
disponibilidad y conexión a servicios productivos. Todo el trabajo se realizó sobre
el entorno de laboratorio (DEVASC VM + CSR1kv).

## 3. Infraestructura utilizada

| Componente | Detalle |
|---|---|
| Router | Cisco CSR1000v, IOS-XE 16.09.05 — IP de gestión 192.168.56.113 |
| Estación de trabajo | DEVASC VM (Linux, host labvm) |
| Control de versiones | Git + GitHub (ep3-automatizacion-001V-04) |
| Herramientas | pyATS/Genie, Ansible (cisco.ios), ncclient, requests, Python 3 |

## 4. Tecnologías empleadas y justificación

- pyATS / Genie (Fase 1 y 5): captura el estado del equipo vía SSH/CLI, por lo que
  funciona aun antes de habilitar NETCONF. Se usó para el baseline inicial y el diff
  final porque entrega snapshots estructurados y comparables.
- Ansible (Fase 2): aprovisionamiento idempotente y reproducible. Aplica toda la
  configuración desde un playbook versionado, sin tocar el equipo a mano y
  garantizando que reejecutar no genere cambios.
- NETCONF / ncclient (Fase 3): validación independiente sobre el árbol de
  configuración en XML; ideal para verificar de forma transaccional lo que Ansible
  dejó aplicado.
- RESTCONF / requests (Fase 4): segunda validación consultando recursos puntuales en
  JSON vía HTTPS, confirmando los mismos parámetros por otra vía.

## 5. Configuración aplicada

| Parámetro | Valor final en el router |
|---|---|
| Hostname | RTR-TECVERD |
| Loopback de gestión | 10.1.4.1 / 255.255.255.0 (Loopback10) |
| Descripción WAN (Gi1) | Enlace-WAN-La-Serena |
| Banner de acceso | ACCESO RESTRINGIDO - TECVERD |
| Servidor NTP | 208.67.222.222 |
| Servicios | netconf-yang, restconf, ip http secure-server |

## 6. Resultados de validación

| Criterio | NETCONF (Fase 3) | RESTCONF (Fase 4) |
|---|---|---|
| Hostname | CONFORME | CONFORME |
| IP Loopback | CONFORME | CONFORME |
| Máscara Loopback | CONFORME | — |
| Descripción WAN | CONFORME | CONFORME |
| Servidor NTP | CONFORME | CONFORME |
| Resultado global | CONFORME (5/5) | CONFORME (4/4) |

## 7. Conclusiones

El router RTR-TECVERD quedó configurado conforme al estándar corporativo de
Tecnologías Verdes SpA. Ambas validaciones independientes (NETCONF y RESTCONF)
confirmaron los cinco/cuatro parámetros aplicados, y el diff de Genie evidenció los
cambios respecto del estado inicial (descripción de Gi1 de "VBox" a
"Enlace-WAN-La-Serena" y la creación de la interfaz Loopback10 con IP 10.1.4.1).

Durante la ejecución se resolvieron varios ajustes propios del entorno real: la IP
del CSR era 192.168.56.113 (no la del ejemplo), el SSH requería habilitar
algoritmos legados (diffie-hellman-group14-sha1 y ssh-rsa), y para el snapshot final
con Genie fue necesario sortear el banner corporativo que interfería con la lectura
del prompt. El equipo se entrega a operaciones con resultado de compliance CONFORME
y todo el proceso queda auditado en este repositorio.
