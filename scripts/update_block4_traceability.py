"""Append local portal evidence without changing original SRS identifiers/text."""
from pathlib import Path

root = Path(__file__).resolve().parent.parent


def update():
    path = root/'docs/arquitectura/TRAZABILIDAD.md'
    if '| Limitaciones |' in path.read_text(encoding='utf-8-sig'):
        from update_final_traceability import update as final_update
        final_update()
        return
    verified_rf = set(range(10,17)) | {18,28,50}
    partial_rf = {5,7,8,9,17,44}
    public_rf = set(range(24,28)) | set(range(52,61))
    partial_rnf = {1,2,5,6,7,8,9,10,11,12,13,14,15}
    lines = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith(('| RF-', '| RNF-')):
            parts = line.split('|')
            rid = parts[1].strip(); kind, number = rid.split('-'); number = int(number)
            if (kind=='RF' and number in verified_rf|partial_rf|public_rf) or (kind=='RNF' and number in partial_rnf|{3,4,19}):
                parts[4] = ' captive-portal/src y dist/index.html; apps.portal; content/queries.py y surveys.py; analytics/services.py; PORTAL_CAUTIVO.md '
                parts[5] = ' PortalTests; portal.test.cjs; regresiones; smoke_portal_http.py; RENDIMIENTO_BLOQUE_4.json; RESULTADOS.md (alcance local y límites) '
                if kind=='RF' and number in verified_rf: parts[6] = ' verificado '
                if kind=='RF' and number in partial_rf: parts[6] = ' parcial '
                if kind=='RNF': parts[6] = ' verificado ' if number in {4,19} else ' pendiente ' if number==3 else ' parcial '
                line = '|'.join(parts)
        if line.startswith('RF-28/50 siguen parciales'):
            line = 'RF-28/50 tienen interfaz funcional local en el Bloque 4, con categorías/secciones descubiertas sin cambiar HTML. El despliegue pfSense real permanece pendiente; no se confunde con la adaptación editorial comprobada.'
        lines.append(line)
    text = '\n'.join(lines).split('## Cobertura del Bloque 4')[0].rstrip()
    text += '\n\n## Cobertura del Bloque 4\n\n'
    text += ('Portal real conectado a la API local: contenido, navegación dinámica, encuestas, sesión demo separada, logout y vistas. '
        'RF-05/09/44 conservan parcial por AGA_AUTH/pfSense pendiente. RF-07/08/17 y RNF de móvil/visual/accesibilidad no se certifican por DOM. '
        'RNF-04 verifica 24370 bytes sin gzip. RNF-02 solo tiene muestras secuenciales loopback (máximo API 63,758 ms); '
        'RNF-03 sigue pendiente: 132 rechazos HTML y 134 API en ráfagas de 200 con runserver. '
        'No se acredita carga completa móvil en 1–2 s, TLS, Manual de Identidad, Android/iOS ni producción. '
        'Las 147 pruebas funcionales finales pasan; el resultado negativo de carga se informa por separado.\n')
    path.write_text(text, encoding='utf-8')
    if (root/'scripts/update_final_traceability.py').exists():
        from update_final_traceability import update as final_update
        final_update()


if __name__ == '__main__': update()
