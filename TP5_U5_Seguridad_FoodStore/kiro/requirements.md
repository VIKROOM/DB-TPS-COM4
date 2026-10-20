# Kiro - Especificación TP U5 (Parte A)

## Requirements

1. Diseñar e implementar esquema de roles y permisos aplicando principio de mínimo privilegio para Food Store.
2. Incluir roles de grupo: rol_app_lectura, rol_app_escritura, rol_soporte, rol_reportes.
3. Incluir roles de login: app_web, admin_datos.
4. Aplicar al menos un permiso a nivel de columna sobre tabla usuario.
5. Utilizar ALTER DEFAULT PRIVILEGES para asegurar herencia a tablas futuras.
6. Verificar con \du y con consulta sobre information_schema.role_table_grants (ni más, ni menos).
7. Auditar roles.sql con OpenCode y registrar al menos un caso con corrección humana en BITACORA.md.
8. Documentar todo en Kiro (requirements + design).

## Design - Justificación por rol

| Rol | Tipo | Operación habilitada | Privilegios mínimos | Justificación (por qué esa operación y no otra) |
|---|---|---|---|---|
| rol_app_lectura | Grupo | Solo consulta (lectura) | SELECT sobre catálogos y vistas vigentes | Necesita visualizar catálogo, productos, pedidos sin modificar datos. Evita permisos de escritura innecesarios. |
| rol_app_escritura | Grupo | Operaciones transaccionales acotadas | SELECT/INSERT/UPDATE necesarios para líneas/pedidos; privilegios acotados por objeto | Permite registrar pedidos manteniendo integridad. Se privilegia uso por SP antes que DML abierto. No incluye DELETE/TRUNCATE/DDL. |
| rol_soporte | Grupo | Soporte acotado a usuario | SELECT (columnas relevantes) + UPDATE (columna celular) sobre usuario | Permite atender incidencias sin acceder a campos sensibles innecesarios ni modificar otros datos. Mínimo indispensable. |
| rol_reportes | Grupo | Solo lectura para reportes | SELECT sobre vistas/resúmenes | Genera informes sin tocar datos transaccionales. Sin DML. |
| app_web | Login | Consumir aplicación web | Miembro de rol_app_lectura y rol_app_escritura según necesidad | Login de aplicación, sin SUPERUSER. Sigue principio de mínimo privilegio. |
| admin_datos | Login | Administración acotada con trazabilidad | Privilegios puntuales necesarios para mantenimiento; NO SUPERUSER | Requiere justificación y auditoría. Se evita otorgar ALL por defecto. |

## Criterios de aceptación

- Cada GRANT está justificado y acotado al objeto/columna requerido.
- Existe al menos 1 GRANT a nivel de columna sobre usuario.
- ALTER DEFAULT PRIVILEGES definido en esquema public.
- Verificación confirma que cada rol tiene exactamente los privilegios previstos.
- Evidencia registrada en BITACORA.md.