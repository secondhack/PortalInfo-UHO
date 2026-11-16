"""Update local Block 3 evidence while preserving the original SRS inventory."""
from pathlib import Path
root=Path(__file__).resolve().parent.parent


def update():
    path=root/'docs/arquitectura/TRAZABILIDAD.md'
    if '| Limitaciones |' in path.read_text(encoding='utf-8-sig'):
        from update_final_traceability import update as final_update
        final_update()
        return
    verified=set(range(29,34))|{35,36,37,38,42,43,45,46,47,58}
    partial={5,34,44}
    lines=[]
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        if line.startswith('| RF-'):
            parts=line.split('|');number=int(parts[1].strip().split('-')[1])
            if number in verified|partial:
                parts[4]=' approvals/notifications/analytics/audit; content/services.py; React Approvals/NotificationBell/Dashboard/Statistics/Audit; BLOQUE_3.md '
                parts[5]=' AdministrationTests; ConcurrentApprovalTests (PostgreSQL); administration.test.jsx; smoke_administration_http.py; RESULTADOS.md '
                parts[6]=' verificado ' if number in verified else ' parcial '
                line='|'.join(parts)
        if line.startswith('RF-28/50 conservan estado parcial'):
            line='RF-28/50 siguen parciales por pfSense pendiente. RF-46/58 se completaron localmente en el Bloque 3; RF-60 verifica la API dinámica, sin certificar el portal aún no construido.'
        lines.append(line)
    text='\n'.join(lines).split('## Cobertura del Bloque 3')[0].rstrip()
    text+='\n\n## Cobertura del Bloque 3\n\nLos estados verificados acreditan contratos y comportamiento local con PostgreSQL, componentes y HTTP real. RF-34 sigue parcial: correo local verificado, SMTP institucional pendiente. RF-05/44 conservan pendiente el registro enlazado al flujo real AGA_AUTH/pfSense; ya hay vistas/contexto seguros y acceso demo explícito. Las métricas provienen de filas PostgreSQL; la fuente predeterminada excluye semilla ficticia. No se certifican despliegue, carga ni WCAG con estos resultados.\n'
    path.write_text(text,encoding='utf-8')
    if (root/'scripts/update_block4_traceability.py').exists():
        from update_block4_traceability import update as update_next
        update_next()


if __name__=='__main__':update()
