drop table if exists letters;
create table letters (
  id integer primary key autoincrement,
  line varchar(30),
  x integer,
  y integer,
  width integer,
  height integer,
  charac varchar(1)
);

drop table if exists blobs;
create table blobs (
  id integer primary key autoincrement,
  line varchar(30),
  x integer,
  y integer,
  width integer,
  height integer
);

drop table if exists lines;
create table lines (
  id integer primary key autoincrement,
  bon varchar(30),
  x integer,
  y integer,
  width integer,
  height integer
);