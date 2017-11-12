#!/usr/bin/env python2.7

"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver

To run locally:

    python server.py

Go to http://localhost:8111 in your browser.

A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, url_for,g, flash
import datetime
from sqlalchemy import exc
import psycopg2


tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@104.196.18.7/w4111
#
# For example, if you had username biliris and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://biliris:foobar@104.196.18.7/w4111"
#
DATABASEURI = "postgresql://se2444:1366@35.196.90.148/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
#engine.execute("""CREATE TABLE IF NOT EXISTS test (
 # id serial,
  #name text
#);""")
#engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#


@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like



  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT customerid,firstname, lastname, phone,email, street, city, state, country, zipcode FROM customer")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
# 
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")


# Example of adding new data to the database
@app.route('/addCustomer', methods=['GET','POST'])
def addCustomer():
  error = None
  if request.method == 'POST':
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    phone = request.form['phone']
    if(phone == ''):
      error = " Please enter phone"
      return render_template('addCustomer.html', error=error)
    if(phone != '' and not phone.isdigit()):
      error = " Please enter a numeric phone"
      return render_template('addCustomer.html', error=error)
    email = request.form['email']
    street = request.form['street']
    city = request.form['city']
    state = request.form['state']
    country = request.form['country']
    zipcode = request.form['zipcode']
    try:
       g.conn.execute("INSERT INTO customer(firstname, lastname, phone, email, street, city, state, country, zipcode) VALUES(%s, %s, %s, %s,%s,%s,%s,%s, %s)", (firstname,lastname,phone,email,street,city,state, country,zipcode))
    except Exception as e:
       if("customer_phone_key" in e.orig.args[0]):
          return render_template('addCustomer.html', error="Phone number already taken")
       else:
        pass
    finally:
      pass
   
    return redirect('/')
  return render_template('addCustomer.html')

@app.route('/pets', methods=['GET', 'POST'])
def pets():
  if request.method == 'GET':
    customerid = request.args.get('id')
    if(customerid):
      cursor = g.conn.execute("SELECT petid, petname, pettype, dob ,mob , yob FROM pet where customerid=%s",customerid)
      pets = []
      for result in cursor:
         pets.append(result)  # can also be accessed using result[0]
      cursor.close()
    context = dict(data = pets)
    return render_template("pets.html", **context)
  else:
    petname = request.form['petname']
    pettype = request.form['pettype']
    petdob = request.form['dob']
    petmob = request.form['mob']
    petyob = request.form['yob']
    petcustomerid = request.form['customerid']
    g.conn.execute("INSERT INTO Pet(customerid, petname, pettype, dob, mob, yob) VALUES(%s, %s, %s, %s,%s,%s)", (petcustomerid,petname,pettype,petdob,petmob,petyob))
    return redirect('/pets?id=',petcustomerid)
   # return redirect('/')

@app.route('/appointments', methods=['GET', 'POST'])
def appointments():
  if request.method == 'GET':
     physicians = []
     cursor = g.conn.execute('select physicianid, firstname from physician p inner join employee e on p.employeeid = e.employeeid')
     for result in cursor:
        physicians.append(result)  # can also be accessed using result[0]
     cursor.close()
     nurses = []
     cursor = g.conn.execute('select nurseid, firstname from nurse n inner join employee e on n.employeeid = e.employeeid')
     for result in cursor:
        nurses.append(result)  # can also be accessed using result[0]
     cursor.close()
     petid = request.args.get('id')
     appt = []
     if(petid):
      cursor = g.conn.execute('select firstname, lastname, appointmentdate from appointment a inner join physician p on a.physicianid = p.physicianid inner join employee e on p.employeeid = e.employeeid  where a.petid =%s', petid)
      for result in cursor:
          appt.append(result)
      cursor.close()
      context = {'physicians': physicians, 'nurses':nurses, 'data': appt}
  else:
    physicianid = request.form['Physician']
    nurseid = request.form['Nurse']
    day = request.form['moa']
    month = request.form['doa']
    year = request.form['yoa']
    hour = request.form['hoa']
    t = datetime.time(int(hour),0,0)
    d = datetime.datetime(year=int(year), month=int(month), day=int(day))
    dt = datetime.datetime.combine(d, t)
    petid = request.form['petid']
    cursor = g.conn.execute('insert into appointment(petid, physicianid, nurseid, appointmentdate) values(%s, %s, %s, %s)', petid, physicianid, nurseid, dt)
    r = '/appointments?id='
    r = r + petid
    return redirect(r)
  
  return render_template("appt.html", **context)

@app.route('/boarding', methods=['GET', 'POST'])
def boarding():
   if request.method == 'GET':
     staff = []
     cursor = g.conn.execute('select employeeid, firstname, lastname from employee where employeetype=%s', 'boardingstaff')
     for result in cursor:
        staff.append(result)  # can also be accessed using result[0]
     cursor.close()
     boardingtype = []
     cursor = g.conn.execute('SELECT e.enumlabel as boardingType FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname =%s', 'boardingtype')
     for result in cursor:
       boardingtype.append(result)  # can also be accessed using result[0]
     cursor.close()
     petid = request.args.get('id')
     boarding = []
     if(petid):
      cursor = g.conn.execute('select firstname, lastname, starttime, endtime, boardingtype from petboarding b inner join employee e on b.employeeid = e.employeeid where b.petid =%s', petid)
      for result in cursor:
          boarding.append(result)
      cursor.close()
      context = {'data': boarding, 'staff':staff, 'boardingtype':boardingtype}
   else:
    employeeid = request.form['Staff']
    day = request.form['moa']
    month = request.form['doa']
    year = request.form['yoa']
    starthour = request.form['hoas']
    endhour = request.form['hoae']
    starthour = datetime.time(int(starthour),0,0)
    endhour = datetime.time(int(endhour),0,0)
    d = datetime.datetime(year=int(year), month=int(month), day=int(day))
    startdt = datetime.datetime.combine(d, starthour)
    enddt = datetime.datetime.combine(d, endhour)
    petid = request.form['petid']
    boardingtype = request.form['BoardingType']
    try:
     cursor = g.conn.execute('insert into petboarding(petid, starttime, endtime, boardingtype, employeeid) values(%s, %s, %s, %s, %s)', petid, startdt, enddt, boardingtype, employeeid)
    except Exception as e:
       return redirect(url_for('boarding', id=petid, error="Appointment already taken"))
    finally:
      pass
    r = '/boarding?id='
    r = r + petid
    return redirect(r)
  
   return render_template("boarding.html", **context)
    


@app.route('/login', methods=['GET', 'POST'])
def login():
  error = None
  if request.method == 'POST': 
    if(request.form['username'] != 'admin' or request.form['password'] != 'password'):
      error = 'Invalid Credentials'
    else:
      return redirect(url_for('index'))
  return render_template('login.html', error=error)

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.debug = True
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
