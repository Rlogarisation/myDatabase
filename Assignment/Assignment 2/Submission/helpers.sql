-- COMP3311 21T3 Ass2 ... extra database definitions
-- add any views or functions you need into this file
-- note: it must load without error into a freshly created mymyunsw database
-- you must submit this even if you add nothing to it

create or replace function
	transcript(_zid integer) 
	returns setof transcriptrecord
as $$
declare 
	r transcriptrecord;
begin 
	for r in 
		select s.code, t.code as term, s.name, ce.mark as mark, ce.grade, s.uoc
		from people ppl
		join course_enrolments ce on ppl.id = ce.student
		join courses c on ce.course = c.id
		join subjects s on c.subject = s.id
		join terms t on c.term = t.id
		where ppl.id = _zid
		order by t.id, s.code
	loop
		if (r.mark is Null) then
			r.mark := 0;
		end if;
		return next r;
	end loop;
	return;
end;
$$ language plpgsql;
