#  #### ##     ## ########   #######  ########  ######## 
#   ##  ###   ### ##     ## ##     ## ##     ##    ##    
#   ##  #### #### ##     ## ##     ## ##     ##    ##    
#   ##  ## ### ## ########  ##     ## ########     ##    
#   ##  ##     ## ##        ##     ## ##   ##      ##    
#   ##  ##     ## ##        ##     ## ##    ##     ##    
#  #### ##     ## ##         #######  ##     ##    ##    

import os
from flask import Flask, request, render_template, session, url_for, redirect, flash, g
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
# Array String conversion
import requests

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

CATEGORY_NAME = ['General', 'Guitar', 'Keyboard', 'Bass', 'Stand', 'Cable', 'Console', 'Mixer', 'Mic', 'Amp']



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
	application = db.relationship('Application', backref='applicant')

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

	def printCategory(self):
		return CATEGORY_NAME[self.category]


	def __repr__(self):
		return '<Equipment > %r' %(self.name)

class Item(db.Model):
	__tablename__ = 'item'
	id = db.Column(db.Integer, primary_key=True)
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
		self.purchase_date = purchase_date
		self.category = e.category

	def printStatus(self):
		if self.status == 0:
			return 'Available'
		if (self.status == 1):
			return 'Borrowed'
		else:
			return 'Unavailable'

	def __repr__(self):
		reprs = (self.name, self.id)
		return '<Item %r>' %(reprs,)


class ItemApp(db.Model):
	__tablename__ = 'itemapp'
	aid = db.Column(db.Integer, db.ForeignKey('application.id', ondelete='CASCADE'), primary_key = True)
	iid = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key = True)
	items = db.relationship('Item', backref='item_app')

	def __init__(self, iid, aid):
		self.aid = aid
		self.iid = iid

	def __repr__(self):
		reprs = (self.iid, self.aid)
		return '<ItemApp %r>' %(reprs,)

class Application(db.Model):
	__tablename__ = 'application'
	id = db.Column(db.Integer, primary_key = True)
	uid = db.Column(db.Integer, db.ForeignKey('user.id'))
	timestamp = db.Column(db.DateTime)
	borrow_time = db.Column(db.DateTime)
	return_time = db.Column(db.DateTime)
	approval = db.relationship('Approval', uselist = False, backref='application')
	item_app = db.relationship('ItemApp', backref='application', passive_deletes=True)

	def __init__(self, uid, borrow_time, return_time):
		# error check for invalid iids
		self.uid = uid
		self.borrow_time = borrow_time
		self.return_time = return_time
		self.timestamp = datetime.utcnow()

	# check if application is approved
	def isApproved(self):
		if self.approval is not None:
			return True
		else:
			return False

	def getItems(self):
		itemapp = self.item_app
		items = []
		for ia in itemapp:
			items.append(ia.items)
		return items

	def displayTimestamp(self):
		return self.timestamp.strftime('%Y-%m-%d %H:%M:%S')

	def __repr__(self):
		return '<Application %r>' %(self.id)

class Approval(db.Model):
	__tablename__ = 'approval'
	aid = db.Column(db.Integer, db.ForeignKey('application.id'), nullable = False, primary_key=True)
	approved_by = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable = False)
	approved_time = db.Column(db.DateTime)

	def __init__(self, aid, approved_by):
		self.aid = aid
		self.approved_by = approved_by
		self.approved_time = datetime.utcnow()

	def displayApprovedTime(self):
		return self.approved_time.strftime('%Y-%m-%d %H:%M:%S')

	def __repr__(self):
		return '<Approval %r>' %(self.aid)






#   ######   #######  ##    ## ######## ########   #######  ##       ##       ######## ########  
#  ##    ## ##     ## ###   ##    ##    ##     ## ##     ## ##       ##       ##       ##     ## 
#  ##       ##     ## ####  ##    ##    ##     ## ##     ## ##       ##       ##       ##     ## 
#  ##       ##     ## ## ## ##    ##    ########  ##     ## ##       ##       ######   ########  
#  ##       ##     ## ##  ####    ##    ##   ##   ##     ## ##       ##       ##       ##   ##   
#  ##    ## ##     ## ##   ###    ##    ##    ##  ##     ## ##       ##       ##       ##    ##  
#   ######   #######  ##    ##    ##    ##     ##  #######  ######## ######## ######## ##     ##

# ITEM
def createItem(json):
	i = Item(json['name'], json['category'], json['purchase_date'])
	db.session.add(i)
	db.session.commit()
	return i

def deleteItem(id):
	i = Item.query.get(id)
	if i is not None:
		db.session.delete(i)
		db.session.commit()

def editItem(id, json):
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

def itemIfAvailable(id, borrow_time, return_time):
	i = Item.query.get(id)
	item_app = i.item_app
	for ia in item_app:
		app = ia.application
		if app is not None:
			after = (borrow_time - app.return_time).days > 0 and (borrow_time - app.borrow_time).days > 0
			before = (app.borrow_time - return_time).days > 0 and (app.borrow_time - borrow_time).days > 0
			if not (before or after):
				return False
	return True

def availabeItems(borrow_time, return_time):
	items = Item.query.filter(Item.status != STATUS['unavailable'])
	available_items = []
	for i in items:
		if itemIfAvailable(i.id, borrow_time, return_time):
			available_items.append(i)
	return available_items



# APPLICATION

# json for application making
# {
# 	'uid' : 1
#	'items': [1, 2, 3],
# 	'borrow_time': datetime.(2013, 10, 28, 13, 12, 45, 931000),
# 	'return_time': datetime.(2013, 10, 28, 13, 12, 45, 931000)
# }

def makeApplication(json):
	a = Application(json['uid'], json['borrow_time'], json['return_time'])
	db.session.add(a)
	db.session.commit()
	#create association table
	for i in json['items']:
		item_app = ItemApp(i, a.id)
		db.session.add(item_app)

	db.session.commit()	
	return a

def editApplication(id, json):
	a = Application.query.get(id)
	if a is not None:
		a.borrow_time = json['borrow_time']
		a.return_time = json['return_time']
		for r in a.item_app:
			db.session.delete(r)
		for i in json['items']:
			item_app = ItemApp(i, a.id)
			db.session.add(item_app)
		db.session.commit()
	return a

def deleteApplication(id):
	a = Application.query.get(id)
	disapproveApplication(id)
	if a is not None:
		for r in a.item_app:
			db.session.delete(r)
		db.session.delete(a)
		db.session.commit()

def getApplication(id):
	a = Application.query.get(id)
	return a

#APPROVAL
def approveApplication(admin_id, app_id):
	a = Approval(app_id, admin_id)
	db.session.add(a)
	db.session.commit()

def disapproveApplication(app_id):
	a = Application.query.get(app_id).approval
	if a is not None:
		db.session.delete(a)
		db.session.commit()



#  ##     ## #### ######## ##      ## 
#  ##     ##  ##  ##       ##  ##  ## 
#  ##     ##  ##  ##       ##  ##  ## 
#  ##     ##  ##  ######   ##  ##  ## 
#   ##   ##   ##  ##       ##  ##  ## 
#    ## ##    ##  ##       ##  ##  ## 
#     ###    #### ########  ###  ###  

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
	all_applications = Application.query.all()
	all_items = Item.query.all()
	return render_template("index.html", all_applications = all_applications, all_items = all_items)

@app.route('/application/step1', methods=['GET', 'POST'])
def make_application_step1():
	return render_template("application_step1.html")

@app.route('/application/step2', methods=['GET', 'POST'])
def make_application_step2():
	borrow_time = request.form['borrow_time']
	return_time = request.form['return_time']
	borrow_time_object = datetime.strptime(borrow_time, '%m/%d/%Y')
	session['br_time'] = borrow_time_object

	return_time_object = datetime.strptime(return_time, '%m/%d/%Y')
	session['re_time'] = return_time_object
	available_items = availabeItems(borrow_time_object, return_time_object)
	return render_template("application_step2.html", available_items=available_items, borrow_time = borrow_time_object, return_time = return_time_object)

@app.route('/application/step3', methods=['GET', 'POST'])
def make_application_step3():
	selected_items = request.form.getlist('selected_items')
	app_json = {
		'uid': 2,
		'items': selected_items,
		'borrow_time': session['br_time'],
		'return_time': session['re_time']
	}

	user_name = User.query.get(app_json['uid']).name

	item_name = []
	for i in selected_items:
		item_name.append(Item.query.get(i).equipment.name)

	session['app'] = app_json

	return render_template("application_step3.html", application = app_json, item_name = item_name, user_name=user_name)


@app.route('/application/make', methods=['GET', 'POST'])
def make_application():
	app_json = session['app']
	application = makeApplication(app_json)
	return render_template("application.html", application = application)

@app.route('/application/<id>', methods = ['GET', 'POST'])
def application_info(id):
	application = getApplication(id)
	return render_template("application.html", application = application)

@app.route('/application/<id>/delete', methods=['GET', 'POST'])
def delete_application(id):
	deleteApplication(id)
	return redirect(request.referrer or url_for('index'))

@app.route('/application/<id>/approve', methods=['GET', 'POST'])
def approve_application(id):
	approveApplication(2, id)
	return redirect(request.referrer or url_for('application_info', id = id))

@app.route('/application/<id>/disapprove', methods=['GET', 'POST'])
def disapprove_application(id):
	disapproveApplication(id)
	return redirect(request.referrer or url_for('application_info', id = id))

@app.route('/admin/', methods=['GET', 'POST'])
def admin():
	all_applications = Application.query.all()
	all_items = Item.query.all()
	return render_template("admin.html", all_applications = all_applications, all_items = all_items)

@app.route('/admin/item_status=<status>, item=<id>', methods=['GET', 'POST'])
def item_status(id, status):
	changeItemStatus(id, status)
	return redirect(request.referrer)


#  ########  ##     ## ##    ## 
#  ##     ## ##     ## ###   ## 
#  ##     ## ##     ## ####  ## 
#  ########  ##     ## ## ## ## 
#  ##   ##   ##     ## ##  #### 
#  ##    ##  ##     ## ##   ### 
#  ##     ##  #######  ##    ## 

app.run(debug=True)
