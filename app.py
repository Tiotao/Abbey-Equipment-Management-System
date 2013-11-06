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
import ast
from flask.ext.openid import OpenID
from flask.ext.login import login_user, logout_user, current_user, login_required, LoginManager


#   ######   #######  ##    ##  ######  ########    ###    ##    ## ######## 
#  ##    ## ##     ## ###   ## ##    ##    ##      ## ##   ###   ##    ##    
#  ##       ##     ## ####  ## ##          ##     ##   ##  ####  ##    ##    
#  ##       ##     ## ## ## ##  ######     ##    ##     ## ## ## ##    ##    
#  ##       ##     ## ##  ####       ##    ##    ######### ##  ####    ##    
#  ##    ## ##     ## ##   ### ##    ##    ##    ##     ## ##   ###    ##    
#   ######   #######  ##    ##  ######     ##    ##     ## ##    ##    ##    

#APP

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
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

#LOGIN
oid = OpenID(os.path.join(basedir, 'tmp'))
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

#DATABASE

db = SQLAlchemy(app)


STATUS = {
	'available': 0,
	'borrowed' : 1,
	'unavailable': 2,
	'deleted': 3
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

USER_STATUS = {
	'normal': 0,
	'deleted': 1
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
	status = db.Column(db.SmallInteger, nullable=False, default = USER_STATUS['normal'])

	def __init__(self, name, email):
		self.name = name
		self.email = email


	def isDeleted(self):
		boolean = (self.status == USER_STATUS['deleted'])
		return boolean
	
	def is_active(self):
		return not(self.isDeleted())

	def get_id(self):
		return self.id

	def is_authenticated(self):
		return True

	def is_anonymous(self):
		return False

	def isAdmin(self):
		return Admin.query.get(self.id) != None

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

	def availableItemsId(self):
		iids = []
		for i in self.availableItems():
			iids.append(i.id)
		return iids

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
		if (self.status == 2):
			return 'Unavailable'
		else:
			return 'Deleted'

	def __repr__(self):
		reprs = (self.equipment.name, self.id)
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
	i = changeItemStatus(id, STATUS['deleted'])
	return i

def editItem(id, json):
	i = Item.query.get(id)
	if i is not None:
		i.equipment.name = json['name']
		i.equipment.category = json['category']
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

	# {
	# 	'Mic': {
	# 			'SM57': [1,2,3],
	# 			'SM58': [5,6,7],
	# 	},

	# 	'General: {


	# 	}


	# }

	json = {}

	for Cat in CATEGORY_NAME:
		
		cat = Cat.lower()
		equipments = Equipment.query.filter(Equipment.category == CATEGORY[cat]).all()
		if len(equipments)>0:
			json[Cat] = {}
			for e in equipments:
				# to check if it is avalaible within timeframe
				iids = e.availableItemsId()
				available_iids = []
				for id in iids:
					if itemIfAvailable(id, borrow_time, return_time):
						available_iids.append(id)
				if len(available_iids) > 0:
					json[Cat][e.name] = available_iids

	for c in json.items():
		if c[1] == {}:
			del json[c[0]]

	return json



# APPLICATION

# json for application making
# {
# 	'uid' : 1,
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

def getUserApplication(uid):
	a = User.query.get(uid).application
	return a

def getUserPendingApplication(uid):
	apps = getUserApplication(uid)
	pending_apps = []
	for a in apps:
		if a.approval is None:
			pending_apps.append(a)
	return pending_apps

def getUserApprovedApplication(uid):
	apps = getUserApplication(uid)
	approved_apps = []
	for a in apps:
		if a.approval is not None:
			approved_apps.append(a)
	return approved_apps

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


#USER

def createUser(name, email):
	u = User(name, email)
	if u is not None:
		db.session.add(u)
		db.session.commit()
	return u

def deleteUser(id):
	u = User.query.get(id)
	if u is not None:
		u.status=USER_STATUS['deleted']
		db.session.commit()
	return u

def editUser(id, json):
	u = User.query.get(id)
	if u is not None:
		u.name = json['name']
		db.session.commit()
	return u


#LOGIN

@login_manager.user_loader
def load_user(id):
	return User.query.get(id)

@app.before_request
def before_request():
	g.user = current_user

#  ##     ## #### ######## ##      ## 
#  ##     ##  ##  ##       ##  ##  ## 
#  ##     ##  ##  ##       ##  ##  ## 
#  ##     ##  ##  ######   ##  ##  ## 
#   ##   ##   ##  ##       ##  ##  ## 
#    ## ##    ##  ##       ##  ##  ## 
#     ###    #### ########  ###  ###  


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
	if g.user is not None and g.user.is_authenticated():
		login_user(g.user)
		return redirect(oid.get_next_url())
	if request.method == 'POST':
		openid = request.form.get('openid')
		if openid:
			return oid.try_login(openid, ask_for=['email', 'fullname','nickname'])
	return render_template('login.html', next=oid.get_next_url(), error=oid.fetch_error())

@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    print resp.email
    print resp.identity_url
    user = User.query.filter_by(email=resp.email).first()
    print user
    if user is not None:
        flash(u'Successfully signed in')
        login_user(user)
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
	if g.user is not None and g.user.is_authenticated():
		return redirect(url_for('index'))
	if request.method == 'POST':
		name = request.form['name']
		email = request.form['email']
		if not name:
			flash(u'Error: you have to provide a name')
		elif '@' not in email:
			flash(u'Error: you have to enter a valid email address')
		else:
			flash(u'Profile successfully created')
			createUser(name, email)
			return redirect(oid.get_next_url())
	return render_template('create_profile.html', next_url=oid.get_next_url())

@app.route('/logout')
@login_required
def logout():
    session.pop('openid', None)
    logout_user()
    return redirect(oid.get_next_url())

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
	uid = g.user.id
	pending_application = getUserPendingApplication(uid)
	approved_application = getUserApprovedApplication(uid)

	return render_template("index.html", approved_application = approved_application, pending_application = pending_application)

@app.route('/application/step1', methods=['GET', 'POST'])
@login_required
def make_application_step1():
	return render_template("application_step1.html")

@app.route('/application/step2', methods=['GET', 'POST'])
@login_required
def make_application_step2():
	borrow_time = request.form['borrow_time']
	return_time = request.form['return_time']
	borrow_time_object = datetime.strptime(borrow_time, '%d/%m/%Y')
	session['br_time'] = borrow_time_object

	return_time_object = datetime.strptime(return_time, '%d/%m/%Y')
	session['re_time'] = return_time_object
	available_items = availabeItems(borrow_time_object, return_time_object)
	return render_template("application_step2.html", available_items=available_items, borrow_time = borrow_time_object, return_time = return_time_object)

@app.route('/application/step3', methods=['GET', 'POST'])
@login_required
def make_application_step3():

	
	selected_items = []
	selected = request.form

	items = {}

	for key in selected.keys():
		for value in selected.getlist(key):
			value = ast.literal_eval(value)
			if len(value) > 0:
				items[key] = len(value)
				selected_items.extend(value)
	

	print items

	app_json = {
		'uid': g.user.id,
		'items': selected_items,
		'borrow_time': session['br_time'],
		'return_time': session['re_time']
	}

	user_name = User.query.get(app_json['uid']).name

	session['app'] = app_json

	return render_template("application_step3.html", application = app_json, items = items, user_name=user_name)


@app.route('/application/make', methods=['GET', 'POST'])
@login_required
def make_application():
	app_json = session['app']
	application = makeApplication(app_json)
	id = application.id
	return redirect("/application/"+str(id))

@app.route('/application/<id>', methods = ['GET', 'POST'])
@login_required
def application_info(id):
	application = getApplication(id)

	return render_template("application.html", application = application)

@app.route('/application/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_application(id):
	deleteApplication(id)
	return redirect(request.referrer or url_for('index'))

@app.route('/application/<id>/approve', methods=['GET', 'POST'])
@login_required
def approve_application(id):
	approveApplication(g.user.id, id)
	return redirect(request.referrer or url_for('application_info', id = id))

@app.route('/application/<id>/disapprove', methods=['GET', 'POST'])
@login_required
def disapprove_application(id):
	disapproveApplication(id)
	return redirect(request.referrer or url_for('application_info', id = id))

@app.route('/admin/', methods=['GET', 'POST'])
@login_required
def admin():
	if not g.user.isAdmin():
		return redirect(url_for('not_authorized'))
	else:
		all_applications = Application.query.all()
		all_items = Item.query.filter(Item.status < 2)
		all_users = User.query.filter(User.status == 0)
		return render_template("admin.html", all_users = all_users, all_applications = all_applications, all_items = all_items, category=CATEGORY, category_name=CATEGORY_NAME)

@app.route('/admin/item_status=<status>, item=<id>', methods=['GET', 'POST'])
@login_required
def item_status(id, status):
	changeItemStatus(id, status)
	return redirect(request.referrer)

@app.route('/item/add', methods=['GET', 'POST'])
@login_required
def add_item():
	name = request.form['name']
	category = int(request.form['category'])
	purchase_date = request.form['purchase_date']
	purchase_date_object = datetime.strptime(purchase_date, '%d/%m/%Y')
	json = {
		"name": name,
		"category": category,
		"purchase_date": purchase_date_object
	}
	i = createItem(json)
	return redirect(request.referrer)

@app.route('/item/<id>/delete', methods=['GET', 'POST'])
@login_required
def delete_item(id):
	deleteItem(id)
	return redirect(request.referrer)



@app.route('/item/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(id):
	name = request.form['name_edit']
	category = int(request.form['category_edit'])
	purchase_date = request.form['purchase_date_edit']
	purchase_date_object = datetime.strptime(purchase_date, '%d/%m/%Y')
	json = {
		"name": name,
		"category": category,
		"purchase_date": purchase_date_object
	}
	editItem(id, json)
	return redirect(request.referrer)

@app.route('/user/<id>', methods=['GET','POST'])
@login_required
def user_info(id):
	user = User.query.get(id)
	return render_template('user.html', user = user)


@app.route('/user/<id>/delete', methods=['GET','POST'])
@login_required
def user_delete(id):
	deleteUser(id)
	return redirect(request.referrer)

@app.route('/user/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
	name = request.form['name_edit']
	json = {
		"name": name,
	}
	editItem(id, json)
	return redirect(request.referrer)	

@app.route('/error/not_authorized')
@login_required
def not_authorized():
	return render_template('not_authorized.html')

@app.route('/create_admin')
@login_required
def create_admin():
	a = Admin('admin', 'tiotaocn@gmail.com', 'abbey@tembusupac.org')
	db.session.add(a)
	db.session.commit()
	return redirect(url_for('index'))

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

#  ########  ##     ## ##    ## 
#  ##     ## ##     ## ###   ## 
#  ##     ## ##     ## ####  ## 
#  ########  ##     ## ## ## ## 
#  ##   ##   ##     ## ##  #### 
#  ##    ##  ##     ## ##   ### 
#  ##     ##  #######  ##    ## 

#app.run(debug=True)
