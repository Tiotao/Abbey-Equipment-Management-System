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
# Array String conversion
import ast

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
app.debug = DEBUG
app.secret_key = SECRET_KEY
app.port = PORT
app.host = '0.0.0.0'
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

#DATABASE

db = SQLAlchemy(app)
db.session.execute('PRAGMA foreign_keys=ON;')
db.session.commit()

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
	approval = db.relationship('Approval', backref='approver')

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
	items = db.relationship('Item', backref='equipment')

	def __init__(self, name, category):
		self.name = name
		self.category = category

	def numOfItems(self):
		return len(self.items)

	def availableItems(self):
		available_items = []
		for i in self.items:
			if i.status == STATUS['available']:
				available_items.append(i)
		return available_items

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
	iids = db.Column(db.String(120), nullable = False, default = '[]')
	timestamp = db.Column(db.DateTime)
	borrow_time = db.Column(db.DateTime)
	return_time = db.Column(db.DateTime)
	approval = db.relationship('Approval', uselist = False, backref='application')

	def __init__(self, uid, iids, borrow_time, return_time):
		# error check for invalid iids
		if iidsIfValid(iids):
			self.uid = uid
			self.iids = iids
			self.borrow_time = borrow_time
			self.return_time = return_time
			self.timestamp = datetime.utcnow()
		else:
			return 'Invalid iids'

	# check if iids is valid
	def iidsIfValid(self, iids):
		items_id_array = ast.literal_eval(iids)
		for i in items_id_array:
			if Item.query.filter_by(id=i).first() is None:
				return False
		return True

	# get list of items being borrowed
	def getItems(self):
		items_id_array = ast.literal_eval(self.iids)
		items_array = []
		for i in items_id_array:
			item = Item.query.filter_by(id=i).first()
			items_array.append(item)
		return items_array

	def __repr__(self):
		return '<Application %r>' %(self.id)

class Approval(db.Model):
	__tablename__ = 'record'
	id = db.Column(db.Integer, primary_key = True)
	aid = db.Column(db.Integer, db.ForeignKey('application.id'), nullable = False)
	approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable = False)
	approved_time = db.Column(db.DateTime)

	def __init__(self, aid, approved_by, approved_time):
		self.aid = aid
		self.approved_by = approved_by
		self.approved_time = approved_time

	def __repr__(self):
		return '<Approval %r>' %(self.id)






#   ######   #######  ##    ## ######## ########   #######  ##       ##       ######## ########  
#  ##    ## ##     ## ###   ##    ##    ##     ## ##     ## ##       ##       ##       ##     ## 
#  ##       ##     ## ####  ##    ##    ##     ## ##     ## ##       ##       ##       ##     ## 
#  ##       ##     ## ## ## ##    ##    ########  ##     ## ##       ##       ######   ########  
#  ##       ##     ## ##  ####    ##    ##   ##   ##     ## ##       ##       ##       ##   ##   
#  ##    ## ##     ## ##   ###    ##    ##    ##  ##     ## ##       ##       ##       ##    ##  
#   ######   #######  ##    ##    ##    ##     ##  #######  ######## ######## ######## ##     ##

#ITEM
def createItem(json):
	i = Item(json['name'], json['category'], json['purchase_date'])
	db.session.add(i)
	db.session.commit()
	return Item.query.filter_by(name=json['name']).first()

def deleteItem(id):
	i = Item.query.get(id)
	if i is not None:
		db.session.delete(i)
		db.session.commit()

def EditItem(id, json):
	i = Item.query.get(id)
	if i is not None:
		i.name = json['name']
		i.category = json['category']
		i.purchase_date = json['purchase_date']
		db.session.commit()

def copyItem(id):
	i = Item.query.get(id)
	if i is not None:
		duplicate = Item(i.name, i.category, i.purchase_date)
		db.session.add(duplicate)
		db.session.commit()

def changeItemStatus(id, status):
	i = Item.query.get(id)
	if i is not None:
		i.status = status
		db.session.commit()

#User

# json for application making
# {
# 	'uid' : 1
#	'items': '[1, 2, 3]',
# 	'borrow_time': datetime.(2013, 10, 28, 13, 12, 45, 931000),
# 	'return_time': datetime.(2013, 10, 28, 13, 12, 45, 931000)
# }

def makeApplication(json):
	a = Application(json['uid'], json['items'], json['borrow_time'], json['return_time'])
	if a == 'Invalid iids':
		return a
	else:
		db.session.add(a)
		db.session.commit()
		a = Application.query.\
			filter_by(iids = json['iids'], uid = json['uid']).first()
		return a

#

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


# u = User('yiwen', 'tiotaocn@gmail.com')
# a = Admin('yike', 'yiwen@nus.edu.sg', 'admin@tembusupac.org')
# db.session.add(a)
# db.session.add(u)
# db.session.commit()

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

# a0 = Application(1, '[1, 2]', datetime.utcnow(), datetime.utcnow())
# db.session.add(a0)
# db.session.commit()

# r0 = Record(aid=1, approved_by=2, approved_time=datetime.utcnow())
# db.session.add(r0)
# db.session.commit()

# r0 = Record(aid=1, approved_by=5, approved_time=datetime.utcnow())
# db.session.add(r0)
# db.session.commit()


print User.query.all()
print Equipment.query.all()
print Item.query.all()
print Application.query.all()
print Application.query.all()[0].approval
print Record.query.all()
print Admin.query.all()[0].approved_record[0].application
# db.session.execute('PRAGMA foreign_keys=ON;')
# db.session.commit()
#app.run(debug=True)


