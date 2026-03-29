from fastapi import FastAPI, Path, Query, Response
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    headquarters: str


class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = Field(default=None, index=True)

    team_id: int | None = Field(default=None, foreign_key="team.id")


hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")

engine = create_engine("sqlite:///database.db", echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def select_heroes():
    with Session(engine) as session:
        statement = select(Hero)
        results = session.exec(statement)
        heroes = results.all()
        print(heroes)


def select_heroes():
    with Session(engine) as session:
        statement = select(Hero).where(Hero.name == "Deadpond")
        results = session.exec(statement)
        for hero in results:
            print(hero)


def create_heroes():
    hero_1 = Hero(name="Deadpond", secret_name="Dive Wilson")

    with Session(engine) as session:
        session.add(hero_1)

        session.commit()


def update_heroes():
    with Session(engine) as session:
        statement = select(Hero).where(Hero.name == "Spider-Boy")  
        results = session.exec(statement)  
        hero = results.one()  
        print("Hero:", hero)  

        hero.age = 16  
        session.add(hero)  
        session.commit()  
        session.refresh(hero)  
        print("Updated hero:", hero)  


def delete_heroes():
    with Session(engine) as session:
        statement = select(Hero).where(Hero.name == "Spider-Youngster")
        results = session.exec(statement)
        hero = results.one()
        print("Hero: ", hero)

        session.delete(hero)
        session.commit()

        print("Deleted hero:", hero)