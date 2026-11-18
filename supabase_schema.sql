-- Ejecutar en Supabase > SQL Editor. Es seguro ejecutarlo más de una vez.
--
-- Si ya tenías las tablas de la versión anterior (solo pruebas), bórralas primero:
--   drop table if exists mensajes, intentos cascade;

-- =========================================================================
-- TABLA 1: evaluaciones  ->  cada respuesta que el estudiante envía a evaluar
--          (una fila por clic en "Evaluar"; también si falló la IA)
-- =========================================================================
create table if not exists evaluaciones (
  id                bigint generated always as identity primary key,
  -- quién y cuándo
  fecha_hora_lima   timestamp    not null default (now() at time zone 'America/Lima'),
  codigo            text         not null,                 -- código de estudiante
  id_sesion         uuid         not null,                 -- un ingreso a la app = una sesión
  n_registro_sesion int          not null,                 -- 1, 2, 3... dentro de la sesión
  -- qué pregunta
  id_pregunta       text         not null,                 -- P01 ... P30 (y las de teoría)
  variante          text         not null default 'modelo',-- 'modelo' o 'var-<semilla>'
  tema              text         not null,
  dimension         text         not null,
  -- cómo le fue
  tiempo_resp_seg   int,                                   -- desde que vio la pregunta hasta que pulsó Evaluar
  veredicto         text         not null,                 -- Logrado | En proceso | Inicial | Error técnico
  puntaje           numeric(3,1),                          -- null si hubo error técnico
  puntaje_max       numeric(3,1) not null default 2,
  long_respuesta    int          not null,                 -- caracteres de la respuesta
  modelo            text,                                  -- modelo Gemini que evaluó
  error_tecnico     text,                                  -- motivo si falló la evaluación
  -- textos largos (al final para que la tabla se lea bien)
  enunciado         text         not null,                 -- caso: contexto + datos numéricos
  pedido            text         not null,                 -- lo que se le pide al estudiante
  respuesta         text         not null,                 -- respuesta del estudiante
  clave             text         not null,                 -- solución de referencia
  unique (id_sesion, n_registro_sesion)
);

-- =========================================================================
-- TABLA 2: guias_tutor  ->  cada vez que el estudiante pide ayuda al tutor
--          (una fila por interacción: lo que preguntó + la guía que recibió)
-- =========================================================================
create table if not exists guias_tutor (
  id                bigint generated always as identity primary key,
  -- quién y cuándo
  fecha_hora_lima   timestamp    not null default (now() at time zone 'America/Lima'),
  codigo            text         not null,
  id_sesion         uuid         not null,
  n_registro_sesion int          not null,                 -- n.º de interacción con el tutor en la sesión
  -- sobre qué pregunta
  id_pregunta       text         not null,
  variante          text,                                  -- null si la app no la envía
  tema              text         not null,
  dimension         text         not null,
  -- qué tipo de ayuda
  tipo              text         not null check (tipo in ('pista', 'consulta')),  -- botón "Dame una pista" o chat libre
  nivel_pista       int,                                   -- 1 = pregunta guía, 2 = fórmula, 3 = ejemplo análogo
  modelo            text,
  long_guia         int          not null,                 -- caracteres de la respuesta del tutor
  -- textos
  consulta_estudiante text       not null,
  guia_tutor          text       not null
);

create index if not exists idx_evaluaciones_codigo   on evaluaciones (codigo, id desc);
create index if not exists idx_evaluaciones_pregunta on evaluaciones (id_pregunta);
create index if not exists idx_guias_tutor_codigo    on guias_tutor (codigo, id desc);
create index if not exists idx_guias_tutor_pregunta  on guias_tutor (id_sesion, id_pregunta);

-- Seguridad: RLS activado y sin políticas => la API pública no puede leer ni escribir;
-- la app entra con el usuario de la base de datos (postgres), que no está sujeto a RLS.
alter table evaluaciones enable row level security;
alter table guias_tutor  enable row level security;

-- Vista para el docente: por estudiante, tema y dimensión (logro, tiempo y ayuda pedida).
create or replace view resumen_docente as
with ev as (
  select codigo, tema, dimension,
         count(*) filter (where error_tecnico is null)                    as respuestas,
         round(avg(puntaje / nullif(puntaje_max, 0)) * 100, 1)            as logro_pct,
         round(avg(tiempo_resp_seg) filter (where error_tecnico is null)) as tiempo_prom_seg,
         count(*) filter (where error_tecnico is not null)                as errores_tecnicos
  from evaluaciones
  group by codigo, tema, dimension
), tu as (
  select codigo, tema, dimension,
         count(*)                                      as consultas_tutor,
         count(*) filter (where tipo = 'pista')        as pistas
  from guias_tutor
  group by codigo, tema, dimension
)
select ev.*, coalesce(tu.consultas_tutor, 0) as consultas_tutor, coalesce(tu.pistas, 0) as pistas
from ev left join tu using (codigo, tema, dimension);

-- OPCIONAL: restringir el ingreso a los códigos de tu curso.
-- Si esta tabla no existe o está vacía, entra cualquier código.
-- create table if not exists codigos_habilitados (codigo text primary key);
-- insert into codigos_habilitados values ('U2026001'), ('U2026002');
