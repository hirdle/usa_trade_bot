from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import  Column, Integer, String, Boolean, Date
import datetime

def get_now_date():
    return datetime.datetime.now().date()
    
# строка подключения
sqlite_database = "sqlite:///app.db"
  
# создаем движок SqlAlchemy
engine = create_engine(sqlite_database)
#создаем базовый класс для моделей
Base = declarative_base()
  
import pysondb as db
database_json = db.getDb("channels.json")

def add_data_channel(id_discord, id_telegram, name, link):
    database_json.add({"id_discord": id_discord, "id_telegram":id_telegram, 'name':name, 'link':link})

def delete_data_channel(id_discord):
    active_channel = database_json.getByQuery({"id_discord":id_discord})[0]
    database_json.deleteById(active_channel['id'])

def get_data_channels():
    all_channels = database_json.getAll()
    return all_channels

def get_text_channels(mode=0):

    all_text_channels = "Нет активных чатов."

    all_list_channels = get_data_channels()
    
    if all_list_channels != 0:

        all_text_channels = ""
        for channel in all_list_channels:
            if mode == 1:
                all_text_channels += "Имя: {0}\nСсылка: {1}\n".format(channel['name'], channel['link'])
            else:
                all_text_channels += "Имя: {0} Id: <code>{1}</code>\nСсылка: {2}\n".format(channel['name'], channel['id_discord'], channel['link'])
    
    return all_text_channels


class User(Base):
    __tablename__ = "user"

    #    userid
    #    profileid
    #    is_subscrition
    #    next_billing_date
  
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    profile_id = Column(Integer)
    registration_date = Column(Date)
    is_subscrition = Column(Boolean)
    next_billing_date = Column(Date)

Base.metadata.create_all(bind=engine)


def get_all_users():
    with Session(autoflush=False, bind=engine) as db:

        users = db.query(User).all()

        for user in users:
            user.is_trial = False
            if user.next_billing_date > get_now_date() and user.is_subscrition == False:
                user.is_trial = True
        
        return users

def get_active_subs_users():
    with Session(autoflush=False, bind=engine) as db:

        all_active_users = db.query(User).filter(User.next_billing_date > get_now_date()).all()

        return all_active_users


def get_current_user(user_id):
    with Session(autoflush=False, bind=engine) as db:

        try:

            user = db.query(User).filter(User.profile_id==user_id).first()

            user.is_trial = False

            if user.next_billing_date > get_now_date() and user.is_subscrition == False:
                user.is_trial = True

            return user

        except:
            return None

def add_user(user_name, user_id):

    if get_current_user(user_id=user_id) == None:

        with Session(autoflush=False, bind=engine) as db:
            date_now = get_now_date()
            next_billing_date = date_now + datetime.timedelta(days=2)

            user = User(name=user_name, profile_id=user_id, registration_date=date_now, is_subscrition=False, next_billing_date=next_billing_date)
            db.add(user)    
            db.commit()

def add_subc_user(user_id, time_delta):
    with Session(autoflush=False, bind=engine) as db:

        current_user = db.query(User).filter(User.profile_id==user_id).first()

        if (current_user != None):

            date_now = get_now_date()

            if date_now < current_user.next_billing_date:
                next_billing_date = current_user.next_billing_date + datetime.timedelta(days=time_delta)
            else:
                next_billing_date = date_now + datetime.timedelta(days=time_delta)

            current_user.next_billing_date = next_billing_date
            current_user.is_subscrition = True
    
            db.commit() 

            return next_billing_date

