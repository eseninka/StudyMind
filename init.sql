CREATE TABLE users (
    user_id       varchar(128) PRIMARY KEY,
    user_name     text,
    user_surname  text,
    user_username text,
    user_reg_date DATE DEFAULT CURRENT_DATE
);

create table user_tips (
    user_id   varchar(128) PRIMARY KEY,
    hours     int not null,
    subject   text not null,
    extra_day int not null,
    diag_date time
);

create table user_intent (
    user_id          text,
    intent_num       serial primary key,
    intent_name      text not null,
    intent_progress  int default 0,
    intent_create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    intent_deadline  date
);

create table user_tasks (
    user_id        text,
    task_num       serial primary key,
    task_name      text not null,
    task_create_at date DEFAULT CURRENT_DATE
);

alter table user_intent add column condition_intent boolean default '0';
alter table user_tasks add column del_tasks boolean default '0';