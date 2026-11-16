"""Final local-only SRS matrix, with the five user-requested states and explicit limits."""
from collections import Counter
from pathlib import Path

root=Path(__file__).resolve().parent.parent


def update():
    path=root/'docs/arquitectura/TRAZABILIDAD.md'
    html_bytes=(root/'captive-portal/dist/index.html').stat().st_size
    rows=[]
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if not line.startswith(('| RF-','| RNF-')):continue
        parts=[part.strip() for part in line.split('|')]
        rid,description,folio,module=parts[1:5]
        tests=parts[7] if len(parts)>=10 else parts[5]
        number=int(rid.split('-')[1]);status='Implementado y verificado'
        limit='Verificación local con PostgreSQL; no equivale a integración o despliegue institucional.'
        if rid.startswith('RF-'):
            if number in {1,3,5,9,34,44}:
                status='Dependiente de integración institucional'
                limit='Flujo DEMO local implementado; falta contrato/servicio AGA_AUTH, pfSense o SMTP real según requisito. No se inventa integración.'
            elif number in {7,8,17}:
                status='Parcial'
                limit='HTML ligero y diseño adaptable implementados. No se acredita WiFi real, Android/iOS físicos ni carga móvil institucional de 1–2 s.'
            if number in {4,6}:
                module='accounts/security.py y views.py; portal/identity.py y views.py'
                tests='SecurityTests; LoginConcurrencyTests; PortalTests; smoke_final_http.py'
            if number in {19,20,21,22,23,24,25,26,27,28,29,30,31,32,39,40,41,49,50,51,52,53,54,55,56,57,58,59,60}:
                suffix='; vigencia default configurable y consultas públicas existentes'
                if suffix not in module:module+=suffix
        else:
            if number in {1,2,3}:
                status='Parcial'
                limit='Mediciones loopback en RENDIMIENTO_FINAL.json. HTML 200 respuestas correctas; API con 429 al exceder cuota y latencia de ráfaga >500 ms. No certifica WiFi/producción.'
            elif number in {5,17}:
                status='Implementado sin verificar'
                limit='Configuración TLS/seguridad o Docker preparada; la demostración usa HTTP loopback sin Docker. Despliegue real no ejecutado.'
            elif number in {6,11,12,13,14}:
                status='Parcial'
                limit='Defensas y diseño/pruebas locales disponibles; faltan certificación WCAG, Manual de Identidad y dispositivos físicos. Ver alcance de navegador en RESULTADOS.md.'
            elif number==16:
                status='Pendiente'
                limit='Pendiente por decisión explícita del usuario: no GitHub/GitLab, repositorios remotos, publicación ni pipelines externos.'
            elif number in {20,23}:
                status='Dependiente de integración institucional'
                limit='Adaptadores/contratos preparados; sin acceso ni llamadas a AGA_AUTH/SIGENU/ASSET institucionales.'
            elif number==4:
                limit=f'Artefacto final de {html_bytes} bytes sin gzip, frente al máximo 204800; comprobador falla si se supera.'
            elif number==8:
                limit='Cuotas y 429 comprobados en proceso local. Antes de varios workers, configurar caché compartida y dimensionar NAT/usuarios.'
            elif number==19:
                limit='Categorías/contenidos dinámicos verificados en artefacto local; no se ha desplegado en pfSense.'
        evidence='docs/pruebas/RESULTADOS.md; E2E_FINAL.json; RENDIMIENTO_FINAL.json; OpenAPI; AUDITORIA_FINAL.md'
        rows.append([rid,description,folio,module,status,evidence,tests,limit])
    assert len(rows)==84 and len({row[0] for row in rows})==84
    header=['# Trazabilidad final del SRS · Entrega exclusivamente local','',
        'Se conservan los 61 RF y 23 RNF originales del PDF de 24 folios. Los estados describen el alcance comprobado, con limitaciones por requisito. No se publica código; RNF-16 queda pendiente por decisión del usuario.','',
        '| ID | Descripción original | Folio | Módulo | Estado | Evidencia | Prueba asociada | Limitaciones |',
        '|---|---|---|---|---|---|---|---|']
    text='\n'.join(header+['| '+' | '.join(row)+' |' for row in rows])+'\n\n'
    counts=Counter(row[4] for row in rows)
    text+='Estados: '+', '.join(f'{name}: {count}' for name,count in sorted(counts.items()))+'.\n\n'
    text+='Los requisitos generales 2.1–2.8, reglas 10–19 y CU-01–CU-04 se analizan en ARQUITECTURA.md/CONTRATOS.md/AUDITORIA_FINAL.md. Datos de prueba y adaptadores DEMO no sustituyen integraciones institucionales. Ver guía de VS Code y ENTREGA_FINAL.md.\n'
    path.write_text(text,encoding='utf-8')


if __name__=='__main__':update()
