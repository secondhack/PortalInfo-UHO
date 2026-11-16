# Manual del Superadmin

Inicia sesión en http://127.0.0.1:5174 con la cuenta ficticia de .local/demo-credentials.txt. La cuenta protegida no se elimina, desactiva ni degrada desde la API.

- Usuarios: crea Admins/Gestores ficticios, asigna categorías y configura activación/autorización. Una contraseña demo vacía al crear deja acceso local inutilizable; al editar conserva la actual.
- Roles: consulta los tres códigos estables y cambia sus nombres. Las capacidades reservadas no se convierten en concesiones arbitrarias.
- Permisos: elige usuario o rol, categoría y operación. El Gestor necesita también la categoría asignada; las concesiones son aditivas.
- Categorías: crea secciones dinámicas con slug único, descripción, límites y campos extra requeridos como lista JSON. API/portal las descubren sin editar HTML. Los slugs base y reservados están protegidos.
- Nomencladores: administra tipos/valores y jerarquías; los valores en uso no se eliminan y los ciclos se rechazan.
- Configuración: controla límites, vigencia predeterminada, votos autenticados, bloqueo/sesión/retención/correo y reglas defensivas. Los cambios se auditan; vigencia predeterminada solo afecta guardados nuevos que la seleccionan.
- Auditoría: filtra acciones/actor/entidad/período, consulta antes/después y exporta. Es solo lectura, sin borrado manual.

También puedes revisar publicaciones, estadísticas y encuestas como Admin. Correo demo se guarda en .local/mail; activar esa preferencia no contacta SMTP ni reenvía historial. La retención se aplica únicamente por mantenimiento autorizado, no por botón del CMS.

Para la defensa, crea un Gestor ficticio nuevo y asígnale Noticias/Encuestas; sigue el flujo de COMO_PROBAR_EN_VSCODE.md. No muestres contraseñas ni .env en capturas.
