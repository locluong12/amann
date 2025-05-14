# database.py
from sqlalchemy import create_engine
import pymysql

def get_engine():
    return create_engine(
        "mysql+pymysql://admin:Luongloc1210@database-demo.cp2oiuwu4ba1.ap-southeast-2.rds.amazonaws.com:3306/warehouse"
    )
