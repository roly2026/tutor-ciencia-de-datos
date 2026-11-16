-- Ejecutar una vez en Supabase > SQL Editor.
-- (Si ya ejecutaste la versión anterior: drop table if exists mensajes, intentos, estudiantes cascade;
--  y luego ejecuta este script.)

-- Un registro por intento de evaluación (incluye los intentos que fallaron por error técnico).
create table if not exists intentos (
  id                bigint generated always as identity primary key,
  fecha_hora_lima   timestamp not null default (now() at time zone 'America/Lima'),
  codigo            text      not null,            -- código de estudiante
  id_sesion         uuid      not null,            -- una sesión = un ingreso a la app
  n_registro_sesion int       not null,            -- 1, 2, 3... dentro de la sesión
  tema              text      not null,            -- Clasificación | Regresión
  dimension         text      not null,            -- Interpretación | Representación | Cálculo | Análisis | Argumentación
  tiempo_resp_seg   int,                           -- desde que vio la pregunta hasta que pulsó Evaluar
  veredicto         text      not null,            -- Logrado | En proceso | Inicial | Error técnico
  puntaje           numeric(3,1),                  -- 0 a 2 (null si hubo error técnico)
  long_respuesta    int       not null,            -- caracteres de la respuesta
  modelo            text,                          -- modelo Gemini usado
  error_tecnico     text,                          -- mensaje de error si falló la evaluación
  enunciado         text      not null,            -- caso: contexto + datos numéricos
  pedido            text      not null,            -- la pregunta que se le pide al estudiante
  respuesta         text      not null,            -- respuesta del estudiante
  clave             text      not null,            -- solución de referencia
  unique (id_sesion, n_registro_sesion)
);

-- Conversaciones con el tutor (opcional, útil para analizar el uso de pistas).
create table if not exists mensajes (
  id              bigint generated always as identity primary key,
  fecha_hora_lima timestamp not null default (now() at time zone 'America/Lima'),
  codigo          text not null,
  id_sesion       uuid not null,
  tema            text,
  dimension       text,
  rol             text not null check (rol in ('estudiante','tutor')),
  contenido       text not null,
  nivel_pista     int
);

-- Lista opcional de códigos habilitados. Si la tabla está VACÍA, cualquier código puede ingresar.
-- Si tiene filas, solo ingresan esos códigos.
create table if not exists codigos_habilitados (codigo text primary key);

create index if not exists idx_intentos_codigo on intentos (codigo, id desc);
create index if not exists idx_mensajes_codigo on mensajes (codigo, id);

-- Seguridad: RLS activado y sin políticas => solo la service_role key (servidor) puede leer/escribir.
alter table intentos            enable row level security;
alter table mensajes            enable row level security;
alter table codigos_habilitados enable row level security;

-- Vista para el docente.
create or replace view resumen_docente as
select codigo, tema, dimension,
       count(*) filter (where error_tecnico is null)                         as intentos,
       round(avg(puntaje / 2.0) * 100, 1)                                    as logro_pct,
       round(avg(tiempo_resp_seg))                                           as tiempo_prom_seg,
       count(*) filter (where error_tecnico is not null)                     as errores_tecnicos
from intentos
group by codigo, tema, dimension;
