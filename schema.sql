drop table if exists annotations;
create table annotations (
  id integer primary key autoincrement,
  image varchar(30),
  x integer,
  y integer,
  width integer,
  height integer,
  label varchar(1)
);

drop table if exists blobs;
create table blobs (
  id integer primary key autoincrement,
  image varchar(30),
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