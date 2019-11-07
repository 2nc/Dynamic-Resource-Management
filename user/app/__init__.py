from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql

pymysql.install_as_MySQLdb()
webapp = Flask(__name__)
webapp.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:12345678@alldata.c3fcxrbhjwar.us-east-1.rds.amazonaws.com/mydb?charset=utf8'
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(webapp)
count = 0

from app import main
from app import user_op
from app import user_op_data
from app import view
from app import suppression
from app import upload



