-- OPCIONAL · para el docente. Ejecutar a mano en Supabase > SQL Editor (la app NO lo ejecuta).
-- Crea dos vistas para medir el grado de uso del chatbot y el logro de cada estudiante.
-- Son privadas: solo se leen desde el SQL Editor o con la conexión de la app, nunca desde la API pública.

-- 1) Una fila por estudiante: cuánto usa el chatbot
create or replace view public.resumen_uso as
select
    i.codigo,
    count(distinct i.id_sesion)                                         as sesiones,
    count(*)                                                            as intentos,
    count(*) filter (where i.veredicto <> 'Error técnico')              as evaluados,
    round(avg(i.puntaje), 2)                                            as puntaje_prom,
    round(avg(i.puntaje) / 2 * 100)                                     as logro_pct,
    round(sum(i.tiempo_resp_seg) / 60.0, 1)                             as minutos_respondiendo,
    (select count(*) from public.mensajes_tutor m
      where m.codigo = i.codigo and m.rol = 'estudiante')               as consultas_tutor,
    min(i.fecha_hora_lima)                                              as primer_uso,
    max(i.fecha_hora_lima)                                              as ultimo_uso
from public.intentos i
group by i.codigo;

-- 2) Una fila por estudiante, tema y dimensión/tipo: en qué rinde mejor o peor
create or replace view public.resumen_por_tema as
select
    codigo, tema, dimension,
    count(*)                              as intentos,
    round(avg(puntaje), 2)                as puntaje_prom,
    round(avg(puntaje) / 2 * 100)         as logro_pct
from public.intentos
where veredicto <> 'Error técnico'
group by codigo, tema, dimension;

-- Seguridad: que ni anon ni authenticated (la API pública de Supabase) puedan leerlas
alter view public.resumen_uso       set (security_invoker = true);
alter view public.resumen_por_tema  set (security_invoker = true);
revoke all on public.resumen_uso       from anon, authenticated;
revoke all on public.resumen_por_tema  from anon, authenticated;

-- Ejemplos de uso:
--   select * from public.resumen_uso order by ultimo_uso desc;
--   select * from public.resumen_por_tema where codigo = '100195380' order by tema, dimension;
