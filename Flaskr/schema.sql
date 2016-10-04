from flask import Flask


drop table if exists entries;
create table entries(
    id integer primary key autoincrement,
    title text not tull,
    text text not null
);
