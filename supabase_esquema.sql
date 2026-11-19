-- Esquema del Preparador EF (Supabase / PostgreSQL).
-- base_datos.py lo ejecuta una vez al iniciar la app; también puedes pegarlo en el SQL Editor de Supabase.
-- Es idempotente: se puede ejecutar varias veces sin borrar datos.

-- 1) Intentos de los estudiantes (una fila por respuesta evaluada)
create table if not exists public.intentos (
    id                 bigint generated always as identity primary key,
    fecha_hora_lima    timestamp not null default (now() at time zone 'America/Lima'),
    codigo             text      not null,
    id_sesion          text      not null,
    n_registro_sesion  integer   not null,
    tema               text      not null,
    dimension          text      not null,
    tiempo_resp_seg    integer,
    veredicto          text,
    puntaje            numeric(4,2),
    long_respuesta     integer,
    modelo             text,
    error_tecnico      text,
    enunciado          text,      -- contexto del caso + datos mostrados al estudiante
    pedido             text,      -- lo que se le pide al estudiante
    respuesta          text,      -- lo que escribió el estudiante
    clave              text,      -- solución modelo de la pregunta (clave de respuestas)
    id_pregunta        text,      -- P01..P30, S01.., R01..
    variante           text       -- 'modelo', 'var-<semilla>' o 'teo'
);

-- Si la tabla ya existía de una versión anterior, agrega las columnas nuevas sin borrar datos
alter table public.intentos add column if not exists id_pregunta text;
alter table public.intentos add column if not exists variante    text;

create unique index if not exists intentos_sesion_registro_uk
    on public.intentos (id_sesion, n_registro_sesion);
create index if not exists intentos_codigo_fecha_idx
    on public.intentos (codigo, fecha_hora_lima desc);

-- 2) Conversaciones con el tutor (opcional, para analizar el uso de pistas)
create table if not exists public.mensajes_tutor (
    id               bigint generated always as identity primary key,
    fecha_hora_lima  timestamp not null default (now() at time zone 'America/Lima'),
    codigo           text not null,
    id_sesion        text not null,
    tema             text,
    dimension        text,
    id_pregunta      text,
    rol              text not null,      -- 'estudiante' | 'tutor'
    texto            text,
    nivel_pista      integer
);
create index if not exists mensajes_tutor_codigo_idx
    on public.mensajes_tutor (codigo, fecha_hora_lima desc);

-- 3) Códigos de acceso autorizados (opcional).
--    Si la tabla está vacía, la app acepta cualquier código con formato válido.
--    Si tiene filas, solo ingresan los códigos listados con activo = true.
create table if not exists public.codigos_acceso (
    codigo  text primary key,
    nombre  text,
    activo  boolean not null default true
);

-- Seguridad: la app se conecta con el usuario postgres (ignora RLS). Activar RLS sin políticas evita que
-- estas tablas se lean o escriban desde la API pública (anon key) de Supabase.
alter table public.intentos        enable row level security;
alter table public.mensajes_tutor  enable row level security;
alter table public.codigos_acceso  enable row level security;
