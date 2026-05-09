select index1 , blob1, count() 
from ipl_games where index1='2026-05-09' 
group by blob1, index1


select blob1, blob3, count() 
  from ipl_games
where index1 = '2026-05-09'
group by blob1, blob3
  order by blob1;

select blob1, blob3,blob4 from ipl_games
where index1='2026-05-09';

select blob1, blob3, blob4 from ipl_games
where index1='2026-05-09'
  and blob1 != 'page_visited';

select blob1, blob3, blob4 from ipl_games
where index1='2026-05-09'
  and blob1 = 'game_completed';
