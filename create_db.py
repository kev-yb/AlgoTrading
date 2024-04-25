import sqlite3, config

connection = sqlite3.connect(config.DB_FILE)
cursor = connection.cursor()

# creates stock table with stock prices
cursor.execute("""
    CREATE TABLE if not exists stock (
               id integer primary key,
               symbol text not null unique,
               name text not null,
               exchange text not null,
               shortable boolean not null
    )
""")

cursor.execute("""
    CREATE TABLE if not exists stock_price (
               id integer primary key,
               stock_id integer,
               date not null,
               open not null,
               high not null,
               low not null,
               close not null,
               volume not null,
               sma_20,
               sma_50,
               rsi_14,
               foreign key (stock_id) references stock (id)    
    )
""")

cursor.execute('''
    CREATE TABLE if not exists stock_price_minute (
    id integer primary key,
    stock_id integer,
    datetime not null,
    open not null,
    high not null,
    low not null,
    close not null,
    volume not null,
    lower not null,
    middle not null,
    upper not null,
    foreign key (stock_id) references stock (id)   
    )     
''')


# creates strategy table with stock_strategies
cursor.execute('''
    CREATE TABLE if not exists strategy (
        id integer primary key,
        name not null
    )
''')

cursor.execute('''
    CREATE TABLE if not exists stock_strategy (
        stock_id integer not null,
        strategy_id integer not null,
        foreign key (stock_id) references stock (id),
        foreign key (strategy_id) references strategy (id)
    )
''')

strategies = ['opening_range_breakout', 'opening_range_breakdown']

for strategy in strategies:
    cursor.execute('''
                   INSERT INTO strategy (name) VALUES (?)
                   ''', (strategy,))


connection.commit()
