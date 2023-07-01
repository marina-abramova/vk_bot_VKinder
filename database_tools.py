import sqlalchemy
# import sqlalchemy as sqlalchemy
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

from config import DSN

# схема БД
metadata = MetaData()
Base = declarative_base()

class Viewed(Base):
    # def __init__(self, DSN):
    __tablename__ = 'viewed'
    profile_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    worksheet_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)

# добавление записи о просмотренном профиле в бд
def add_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        to_bd = Viewed(profile_id=profile_id, worksheet_id=worksheet_id)
        session.add(to_bd)
        session.commit()

# проверка наличия в БД информации о профиле
def check_user(engine, profile_id, worksheet_id):
    with Session(engine) as session:
        from_bd = session.query(Viewed).filter(
            Viewed.profile_id == profile_id,
            Viewed.worksheet_id == worksheet_id
        ).first()
    return True if from_bd else False


if __name__ == '__main__':
    engine = create_engine(DSN)
    Base.metadata.create_all(engine)

    # add_user(engine,1111,22222)

    res = check_user(engine,1111,22222)
    print(res)