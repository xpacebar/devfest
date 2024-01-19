from datetime import datetime
import requests,json
import os, random, string
from functools import wraps
from flask import Flask,render_template,flash,redirect,request,url_for,make_response,session,abort
# from sqlalchemy.sql import text
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import and_, or_, desc
from pkg import app
# from pkg.forms import 
from pkg.models import db, User, Level, State,Lga,Donation,Breakout,UserRegistration


def get_hotels():
    # we want to connect tot the endpoint, get list of hotels and send to the template
    try:
        url = "http://127.0.0.1:3000/api/v1/listall"
        response = requests.get(url)
        data = response.json()
        return data
    except:
        return None

# without parameter
# def decorator(f):
#     def wrapper(*args, **kwargs):
#         f(*args, **kwargs) #we spice up function and call itf(*args, **kwargs)
#         pass
#     return wrapper


#login required decorator
def login_required(f):
    @wraps(f) #This ensure that the details about the original function f, that is being decorated is still available
    def check_login(*args, **kwargs):
        if session.get('useronline') != None:
            return f(*args, **kwargs)
        else:
            flash('You must be logged in to access this page',category='error')
            return redirect(url_for('login'))
    return check_login




@app.route("/")
def home_page():
    hotels = get_hotels()
    if session.get('useronline') != None:
        id = session.get('useronline')
        deets = User.query.get(id)
    else:
        deets = None
    return render_template('user/index.html', deets=deets,data=hotels)

@app.route('/donation/', methods=['GET', 'POST'])
@login_required
def donation():
    id = session.get('useronline')
    if request.method == 'GET':
        deets = User.query.get(id)
        return render_template('user/donations.html',deets=deets)
    else:
        fullname = request.form.get('fullname')
        email = request.form.get('email')
        amt = request.form.get('amt')
        ref = int(random.random() * 1000000000)
        session['ref'] = ref
        if fullname != "" and email != "" and amt != "":
            donate = Donation(donate_donor=fullname,donate_email=email,donate_amt = amt,donate_status='pending',donate_userid=id,donate_ref = ref)
            db.session.add(donate)
            db.session.commit()
            if donate.donate_id:
                return redirect('/confirm')
            else:
                flash('Please complete the form', message='error')
                return redirect('/donation/')
        else:
            flash('Please complete the form', message='error')
            return redirect('/donation/')



@app.route('/confirm', methods=['GET','POST'])
@login_required
def confirm():
    id = session.get('useronline')
    deets = User.query.get(id)
    ref = session.get('ref')
    #details of the donation will be avilabe throught session.get('ref)
    if ref:
        donation_deets = Donation.query.filter(Donation.donate_ref==ref).first()
        return render_template('user/confirm.html', deets=deets,donation_deets=donation_deets)
    else:
        flash('Please Start the transaction again')
        return redirect('/donation/')

@app.route('/topaystack',methods=['POST'])
@login_required
def topaystack():
    id = session.get('useronline')
    ref = session.get('ref')
    if ref:
        url = "https://api.paystack.co/transaction/initialize"
        headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_b1fa48c606232b998a4584438bf8a46e495039b7"}
        transaction_deets = Donation.query.filter(Donation.donate_ref == ref).first()
        data = {"email":transaction_deets.donate_email,"amount":transaction_deets.donate_amt * 100,"reference":ref}
        response = requests.post(url,headers=headers,data=json.dumps(data))
        rspjson = response.json()
        if rspjson and rspjson.get('status') == True:
            authurl = rspjson['data']['authorization_url']
            return redirect(authurl)
        else:
            flash('Start the payment process again')
            return redirect('/donation/')
    else:
        flash('Start the payment process again')
        return redirect('/donation/')


@app.route('/paylanding')
@login_required
def paylanding():
    id = session.get('useronline')
    trxref = request.args.get('trxref')
    if session.get('ref') != None and (str(trxref)) == str(session.get('ref')):
        url = "https://api.paystack.co/transaction/verify/"+str(session.get('ref'))
        headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_b1fa48c606232b998a4584438bf8a46e495039b7"}
        response = requests.get(url,headers=headers)
        rsp = response.json()
        return rsp
    else:
        return "start again"

@app.route("/dashboard")
@login_required
def user_dashboard():
    id = session.get('useronline')
    deets = User.query.get(id)
    return render_template('user/dashboard.html', deets=deets)


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('user/loginpage.html')
    else:
        # retrieve info
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        record = db.session.query(User).filter(User.user_email == email).first()
        if record:
            hashed_pwd = record.user_password #the one on the table in our database
            rsp = check_password_hash(hashed_pwd,pwd)
            if rsp:
                id = record.user_id
                session['useronline'] = id
                return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid Credential', category='error')
                return redirect('/login')
        else:
            flash('Invalid Credential', category='error')
            return redirect('/login')
        
@app.route('/profile', methods=['POST', 'GET'])
@login_required
def user_profile():
    id = session.get('useronline')
    if request.method == 'GET':
        deets = User.query.get(id)
        devs = db.session.query(Level).all()
        return render_template("user/profile.html", devs=devs,deets=deets)
    else:
        user = User.query.get_or_404(id)
        user.user_fname = request.form.get('fname')
        user.user_lname = request.form.get('lname')
        user.user_phone = request.form.get('phone')
        user.user_levelid  = request.form.get('level')
        db.session.commit()
        flash('Profile Updated Successfully',category="success")
        return redirect(url_for('user_profile'))
    
@app.route('/changedp', methods=['GET', 'POST'])
@login_required
def change_dp():
    id = session.get('useronline')
    deets = User.query.get(id)
    oldpix = deets.user_pix
    if request.method == 'GET':
        return render_template('user/changedp.html', deets=deets)
    # else:
    #     dp = request.files.get('dp')
    #     filename = dp.filename #empty if no file selected for upload
    #     ext = filename.split(".")
    #     allowed = ['jpg', 'png', 'jpeg']
    #     if ext[1].lower() in allowed:
    #         final_name = str(id)+filename
    #         dp.save(f'pkg/static/profile/{final_name}')
    #         return "done"
    #     else:
    #         flash('extension not allowed', category='error')
    #         return redirect(url_for('change_dp'))
    else:
        dp = request.files.get('dp')
        filename = dp.filename #empty if no file selected for upload
        
        if filename == "":
            flash('Please select a file', category='error')
            return redirect('/changedp')
        else:
            name,ext = os.path.splitext(filename)
            allowed = ['.jpg', '.png', '.jpeg']
            if ext.lower() in allowed:
                # final_name = random.sample(string.ascii_letters,10)
                final_name = int(random.random() * 1000000)
                final_name = str(final_name) + ext #we can't concatenate int and str
                dp.save(f'pkg/static/profile/{final_name}')
                user = db.session.query(User).get(id)
                user.user_pix = final_name
                db.session.commit()
                try:
                    os.remove(f'pkg/static/profile/{oldpix}')
                except:
                    pass
                flash('Profile picture added succesffuly',category='success')
                return redirect('/dashboard')
            else:
                flash('extension not allowed', category='error')
                return redirect(url_for('change_dp'))

@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'GET':
        return render_template('user/register.html')
    else:
        #retrieve form fields
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        state = request.form.get('state')
        lga = request.form.get('lga')
        email = request.form.get('email')
        pwd = request.form.get('pwd')
        hashed_pwd = generate_password_hash(pwd)
        if email != "" and state != "" and lga != "":
            user = User(user_fname=fname,
                        user_lname=lname,
                        user_email=email,
                        user_password=hashed_pwd,
                        user_stateid=state,
                        user_lgaid=lga)
            db.session.add(user)
            db.session.commit()
            id = user.user_id
            # log the user in and redirect to the dashboard
            session['useronline'] = id
            return redirect(url_for("user_dashboard"))
        else:
            flash("Some of the form fields are blank", category="error")
            return redirect(url_for('user_register'))

@app.route('/breakout/', methods=['POST','GET'])
@login_required
def breakout():
    id = session.get('useronline')
    deets = User.query.get(id)
    if request.method == 'GET':
        topics = Breakout.query.filter(Breakout.break_status==1,Breakout.break_level==deets.user_levelid).all()
        regtopics = [x.break_id for x in deets.myregistrations]
        return render_template('user/mybreakout.html', deets=deets,topics=topics,regtopics=regtopics)
    else:
        mytopics = request.form.getlist('topicid') #to get a list in a form where it is been used for dynamic display, it will return the picked items as a list
        if mytopics:
            #delete the user previous post using raw sql statement
            db.session.execute(db.text(f"DELETE FROM user_registration WHERE user_id={id}"))
            db.session.commit()
            for t in mytopics:
                user_reg = UserRegistration(user_id=id,break_id=t)
                db.session.add(user_reg)
            db.session.commit()
            flash('You registration was successful')
            return redirect('/dashboard')
        else:
            flash('You must choose a topic')
            return redirect('/breakout/')


@app.route('/logout')
def logout():
    if session.get("useronline") != None:
        session.pop('useronline',None)
    return redirect('/')

@app.route('/page/')
def page():
    states = State.query.all()
    return render_template('user/demo.html', states=states)

@app.route('/lga/post/')
def lga_post():
    # get the state id using request.form.get('state_id)
    # query your database
    pass