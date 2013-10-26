#  #### ##     ## ########   #######  ########  ######## 
#   ##  ###   ### ##     ## ##     ## ##     ##    ##    
#   ##  #### #### ##     ## ##     ## ##     ##    ##    
#   ##  ## ### ## ########  ##     ## ########     ##    
#   ##  ##     ## ##        ##     ## ##   ##      ##    
#   ##  ##     ## ##        ##     ## ##    ##     ##    
#  #### ##     ## ##         #######  ##     ##    ##    

import os
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

#   ######   #######  ##    ##  ######  ########    ###    ##    ## ######## 
#  ##    ## ##     ## ###   ## ##    ##    ##      ## ##   ###   ##    ##    
#  ##       ##     ## ####  ## ##          ##     ##   ##  ####  ##    ##    
#  ##       ##     ## ## ## ##  ######     ##    ##     ## ## ## ##    ##    
#  ##       ##     ## ##  ####       ##    ##    ######### ##  ####    ##    
#  ##    ## ##     ## ##   ### ##    ##    ##    ##     ## ##   ###    ##    
#   ######   #######  ##    ##  ######     ##    ##     ## ##    ##    ##    

#APP
PORT = int(os.environ.get('PORT', 5000))
SECRET_KEY = 'youshallnotpass'
DEBUG = 'true'

#DATABASE


#   ######   #######  ##    ## ######## ####  ######   
#  ##    ## ##     ## ###   ## ##        ##  ##    ##  
#  ##       ##     ## ####  ## ##        ##  ##        
#  ##       ##     ## ## ## ## ######    ##  ##   #### 
#  ##       ##     ## ##  #### ##        ##  ##    ##  
#  ##    ## ##     ## ##   ### ##        ##  ##    ##  
#   ######   #######  ##    ## ##       ####  ######   

#APP

basedir = os.path.abspath(os.path.dirname(__file__))

if os.environ.get('DATABASE_URL') is None:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db') + '?check_same_thread=False'
else:
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']

SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_RECORD_QUERIES = True

app = Flask(__name__)
db = SQLAlchemy(app)
app.debug = DEBUG
app.secret_key = SECRET_KEY
app.port = PORT
app.host = '0.0.0.0'
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

#DATABASE

STATUS = {
	'available': 0,
	'borrowed' : 1,
	'unavailable': 2,
}

CATEGORY = {
	'general': 0,
	'guitar': 1,
	'keyboard': 2,
	'bass': 3,
	'stand': 4,
	'cable': 5,
	'console': 6,
	'mixer': 7,
	'mic': 8,
	'amp': 9
}





#  ##     ##  #######  ########  ######## ##       
#  ###   ### ##     ## ##     ## ##       ##       
#  #### #### ##     ## ##     ## ##       ##       
#  ## ### ## ##     ## ##     ## ######   ##       
#  ##     ## ##     ## ##     ## ##       ##       
#  ##     ## ##     ## ##     ## ##       ##       
#  ##     ##  #######  ########  ######## ########

class User(db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(64), unique = True, index = True)
	email = db.Column(db.String(120), unique = True, index = True)
	type = db.Column(db.String(50))

	def __init__(self, name, email):
		self.name = name
		self.email = email


	__mapper_args__ = {
		'polymorphic_identity': 'user',
		'polymorphic_on':type,
	}

	__table_args__ = (db.UniqueConstraint('name'), db.UniqueConstraint('email'))

	def __repr__(self):
		return '<User %r>' %(self.name)

class Admin(User):
	__tablename__ = 'admin'
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key = True)
	work_email = db.Column(db.String(120), unique = True, index = True)

	def __init__(self, name, email, work_email):
		super(Admin, self).__init__(name, email)
		self.work_email = work_email

	__mapper_args__ = {
		'polymorphic_identity': 'admin',
	}

	__table_args__ = (db.UniqueConstraint('work_email'), None)

	def __repr__(self):
		return '<Admin %r>' %(self.name)

class Equipment(db.Model):
	__tablename__ = 'equipment'
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(120), unique = True, index = True)
	category = db.Column(db.SmallInteger, nullable = False, default = CATEGORY['general'])

	def __init__(self, name, category):
		self.name = name
		self.category = category

	def __repr__(self):
		return '<Equipment > %r' %(self.name)


class Item(db.Model):
	__tablename__ = 'item'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(120), unique = True, index = True)
	eid = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
	purchase_date = db.Column(db.DateTime)
	status = db.Column(db.SmallInteger, nullable = False, default = STATUS['available'])

	def __init__(self, name, category, purchase_date):
		e = Equipment.query.filter_by(name=name).first()
		if e is None:
			db.session.add(Equipment(name, category))
			db.session.commit()
		e = Equipment.query.filter_by(name=name).first()
		self.eid = e.id
		self.name = e.name
		self.purchase_date = purchase_date
		self.category = e.category

	def __repr__(self):
		reprs = (self.name, self.id)
		return '<Item %r>' %(reprs,)


class Application(db.Model):
	__tablename__ = 'application'
	id = db.Column(db.Integer, primary_key = True)
	uid = db.Column(db.Integer, db.ForeignKey('user.id'))
	eid = db.Column(db.Integer, db.ForeignKey('equipment.id'))
	timestamp = db.Column(db.DateTime)
	borrow_time = db.Column(db.DateTime)
	return_time = db.Column(db.DateTime)
	type = db.Column(db.String(50))

	__mapper_args__ = {
		'polymorphic_identity': 'application',
		'polymorphic_on':type,
	}

	def __repr__(self):
		return '<Application %r>' %(self.id)

class Record(Application):
	__tablename__ = 'record'
	id = db.Column(db.Integer, db.ForeignKey('application.id'), primary_key = True)
	approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'))
	approved_time = db.Column(db.DateTime)

	__mapper_args__ = {
		'polymorphic_identity': 'record',
	}

	def __repr__(self):
		return '<Record %r>' %(self.id)






#   ######   #######  ##    ## ######## ########   #######  ##       ##       ######## ########  
#  ##    ## ##     ## ###   ##    ##    ##     ## ##     ## ##       ##       ##       ##     ## 
#  ##       ##     ## ####  ##    ##    ##     ## ##     ## ##       ##       ##       ##     ## 
#  ##       ##     ## ## ## ##    ##    ########  ##     ## ##       ##       ######   ########  
#  ##       ##     ## ##  ####    ##    ##   ##   ##     ## ##       ##       ##       ##   ##   
#  ##    ## ##     ## ##   ###    ##    ##    ##  ##     ## ##       ##       ##       ##    ##  
#   ######   #######  ##    ##    ##    ##     ##  #######  ######## ######## ######## ##     ##


#  ##     ## #### ######## ##      ## 
#  ##     ##  ##  ##       ##  ##  ## 
#  ##     ##  ##  ##       ##  ##  ## 
#  ##     ##  ##  ######   ##  ##  ## 
#   ##   ##   ##  ##       ##  ##  ## 
#    ## ##    ##  ##       ##  ##  ## 
#     ###    #### ########  ###  ###  

@app.route('/')
@app.route('/index')
def index():
	return 'Hello, World!'


#  ########  ##     ## ##    ## 
#  ##     ## ##     ## ###   ## 
#  ##     ## ##     ## ####  ## 
#  ########  ##     ## ## ## ## 
#  ##   ##   ##     ## ##  #### 
#  ##    ##  ##     ## ##   ### 
#  ##     ##  #######  ##    ## 



# e0 = Equipment('Chair', None)
# e1 = Equipment('YAMAHA', CATEGORY['amp'])
# db.session.add(e0)
# db.session.add(e1)
# db.session.commit()

# i0 = Item('SM57', CATEGORY['mic'], datetime.utcnow())
# i1 = Item('YAMAHA', CATEGORY['amp'], datetime.utcnow())
# db.session.add(i0)
# db.session.add(i1)
# db.session.commit()
print User.query.all()
print Equipment.query.all()
print Item.query.all()

app.run(debug=True)


