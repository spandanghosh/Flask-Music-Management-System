from flask import Flask,render_template,flash,redirect,url_for,session,logging,request 
from flask_mail import Mail,Message
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,IntegerField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
import os

import requests
import youtube_dl

app=Flask(__name__)
app.secret_key='password123'
name1=""
usernname1=""
email1=""
password1=""
username2=""

app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']='password123'
app.config['MYSQL_DB']='my_music'
app.config['MYSQL_CURSORCLASS']='DictCursor'

app.config.from_pyfile('config.cfg')


s=URLSafeTimedSerializer('password123')

mysql=MySQL(app)


@app.route('/')
def index():
	return render_template('index.html')

@app.route('/Band/<idd>')
def Band(idd):
	cur=mysql.connection.cursor()
	cur.execute("SELECT *FROM band WHERE band_id=%s",[idd])
	Name=cur.fetchone()
	Name=Name['B_name']
	cur.execute("SELECT *FROM tracks WHERE band_id=%s",[idd])
	data=cur.fetchall()
	return render_template("Artist.html",Name=Name,data=data)

@app.route('/Artist/<idd>')
def Artist(idd):
	cur=mysql.connection.cursor()
	cur.execute("SELECT *FROM artists WHERE artist_id=%s",[idd])
	Name=cur.fetchone()
	Name=Name['A_name']
	cur.execute("SELECT *FROM tracks WHERE artist_id=%s",[idd])
	data=cur.fetchall()
	return render_template("Artist.html",Name=Name,data=data)


@app.route('/Album/<idd>')
def Album(idd):
	cur=mysql.connection.cursor()
	cur.execute("SELECT *FROM album WHERE album_id=%s",[idd])
	Name=cur.fetchone()
	Name=Name['album_name']
	cur.execute("SELECT *FROM tracks WHERE album_id=%s",[idd])
	data=cur.fetchall()
	return render_template("Album.html",Name=Name,data=data)


class RegisterForm(Form):
	name=StringField('Name',[validators.Length(min=1,max=50)])
	username=StringField('Username',[validators.Length(min=4,max=25)])
	email=StringField('Email',[validators.Length(min=6,max=50)])
	password=PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm',message='Password do not match')])
	confirm=PasswordField('Confirm your Password')

class SongUpload(Form):
	title=StringField('Title',[validators.Length(min=1,max=50)])
	artist=StringField('Artist',[validators.Length(min=4,max=25)])
	vid_id=StringField('Video ID',[validators.Length(min=6,max=1000)])
	album=StringField('Album (Type "-" if no album is there)',[validators.Length(min=1,max=75)])
	band=StringField('Band (Type "-" if no band is there)',[validators.Length(min=1,max=75)])

class Artist(Form):
	Name=StringField('Name',[validators.Length(min=1,max=50)])
	Role=StringField('Role',[validators.Length(min=4,max=25)])
	Band=StringField('Band (Type "-" if no band is there)',[validators.Length(min=0,max=50)])

class Album(Form):
	name=StringField('Name',[validators.Length(min=1,max=50)])
	year=StringField('Year',[validators.Length(min=4,max=25)])
	artist=StringField('Artists',[validators.Length(min=5,max=50)])
	band=StringField('Band (Type "-" if no band is there)',[validators.Length(min=1,max=50)])

class Band(Form):
	name=StringField('Name',[validators.Length(min=0,max=50)])
	nom=IntegerField('Number of Members')

class make_playlist(Form):
	title=StringField('Name',[validators.Length(min=1,max=25)])


	
@app.route('/register',methods=['GET','POST'])
def register():
	form =RegisterForm(request.form)
	if request.method=='POST' and form.validate():
		name=form.name.data
		email=form.email.data
		username=form.username.data
		password=sha256_crypt.encrypt(str(form.password.data))
		global usernname1,name1,email1,password1
		usernname1=username
		name1=name
		email1=email
		password1=password


		cur=mysql.connection.cursor()
		result=cur.execute("SELECT * FROM users WHERE username= %s",[username])
		result2=cur.execute("SELECT * FROM users WHERE email=%s",[email])
		if result>0:
			error='User name already exists,please try another user name'
			return render_template('register.html',form=form,error=error)
		if result2>0:
			error='Email already exists,please try another Email'
			return render_template('register.html',form=form,error=error)
		else:
			cur.execute("INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)",(name1,email1,usernname1,password1))
			mysql.connection.commit()
			cur.close()
			flash('Successfully verified','success')
			return redirect(url_for('login'))

	return render_template('register.html',form=form)




#login
@app.route('/login',methods=['GET','POST'])
def login():
	if request.method=='POST':
		username=request.form['username']

		password_candidate=request.form['password']

		cur=mysql.connection.cursor()

		result=cur.execute("SELECT * FROM users WHERE username= %s",[username])

		if result>0:
			data=cur.fetchone()
			password=data['password']

			if sha256_crypt.verify(password_candidate,password):
				session['logged_in']=True
				session['username']=username
				session['id']=data['id']

				flash('login successful','success')
				return redirect(url_for('dashboard'))
			else:
				error='wrong password'
			return render_template('login.html',error=error)
			cur.close()
		else:
			error='Email not found'
			return render_template('login.html',error=error)

	return render_template('login.html')

#to prevent using of app without login
def is_logged_in(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'logged_in' in session:
			return f(*args,**kwargs)
		else:
			flash('Unauthorised! Please login','danger')
			return redirect(url_for('login'))
	return wrap


@app.route('/dashboard')
@is_logged_in
def dashboard():
	cur=mysql.connection.cursor()
	msg=""
	return render_template('dashboard.html',msg=msg)
	cur.close()

#logout
@app.route('/logout')
def logout():
	session.clear()
	flash('you are now logged out','success')
	return redirect(url_for('login'))



@app.route('/upload', methods = ['GET','POST'])
@is_logged_in
def upload():
	form1 =SongUpload(request.form)
	if request.method=='POST' and form1.validate():
		title=form1.title.data
		artist=form1.artist.data
		vid_id=form1.vid_id.data
		album=form1.album.data
		band=form1.band.data

		


		cur=mysql.connection.cursor()
		result=cur.execute("SELECT * FROM tracks WHERE title= %s and artist_id=(SELECT artist_id FROM artists WHERE A_name=%s)",[title,artist])
		if result>0:
			error='Song already exists'
			return render_template('upload.html',form=form1,error=error)
		
		else:
			title1=title
			cur.execute("SELECT * FROM artists WHERE A_name=%s",[artist])
			artist1=cur.fetchone()
			cur.execute("SELECT * FROM band WHERE B_name=%s",[band])
			band1=cur.fetchone()
			cur.execute("SELECT * FROM album WHERE album_name=%s",[album])
			album1=cur.fetchone()
			os.system('youtube-dl --extract-audio --audio-format mp3 -o "new.mp3" https://www.youtube.com/watch?v='+vid_id)
			os.system("move *.mp3 ./static/music/")
			os.rename("static/music/new.mp3","static/music/"+title1+".mp3")
			link1="/static/music/"+title+".mp3"
			cur.execute("INSERT INTO tracks(title,artist_id,link,band_id,album_id,Vid_id) VALUES(%s,%s,%s,%s,%s,%s)",(title1,artist1['artist_id'],link1,band1['band_id'],album1['album_id'],vid_id))
			mysql.connection.commit()
			cur.close()
			flash('Successfully added','success')
			return redirect(url_for('upload'))

	return render_template('upload.html',form=form1)


@app.route('/AddArtist', methods = ['GET','POST'])
@is_logged_in
def AddArtist():
	form1 =Artist(request.form)
	if request.method=='POST' and form1.validate():
		Name=form1.Name.data
		Role=form1.Role.data
		Band=form1.Band.data
		
		cur=mysql.connection.cursor()
		result=cur.execute("SELECT * FROM artists WHERE A_name=%s",[Name])
		if result>0:
			error='Artist already exists'
			return render_template('add_artists.html',form=form1,error=error)
		
		else:
			name1=Name
			role1=Role
			cur.execute("SELECT * FROM band WHERE B_name=%s",[Band])
			data=cur.fetchone()
			band1=data['band_id']
			cur.execute("INSERT INTO artists(A_name,A_role,band_id) VALUES(%s,%s,%s)",(name1,role1,band1))
			mysql.connection.commit()
			cur.close()
			flash('Successfully added','success')
			return redirect(url_for('dashboard'))

	return render_template('add_artists.html',form=form1)

@app.route('/AddBand',methods=['GET','POST'])
@is_logged_in
def AddBand():
	form1 =Band(request.form)
	if request.method=='POST' and form1.validate():
		name=form1.name.data
		nom=form1.nom.data
		
		
		cur=mysql.connection.cursor()
		result=cur.execute("SELECT * FROM band WHERE B_name=%s",[name])
		if result>0:
			error='Band already exists'
			return render_template('add_band.html',form=form1,error=error)
		
		else:
			name1=name
			nom1=nom
			
			cur.execute("INSERT INTO band(B_name,NOM) VALUES(%s,%s)",(name1,nom1))
			mysql.connection.commit()
			cur.close()
			flash('Successfully added','success')
			return redirect(url_for('dashboard'))

	return render_template('add_band.html',form=form1)


@app.route('/AddAlbum',methods=['GET','POST'])
@is_logged_in
def AddAlbum():
	form1 =Album(request.form)
	if request.method=='POST' and form1.validate():
		name=form1.name.data
		year=form1.year.data
		artist=form1.artist.data
		band=form1.band.data
		
		cur=mysql.connection.cursor()
		result=cur.execute("SELECT * FROM album WHERE album_name=%s",[name])
		if result>0:
			error='Album already exists'
			return render_template('add_album.html',form=form1,error=error)
		
		else:
			name1=name
			year1=year
			cur.execute("SELECT band_id FROM band WHERE B_name=%s",[band])
			data=cur.fetchone()
			band1=data['band_id']
			cur.execute("SELECT artist_id FROM artists WHERE A_name=%s",[artist])
			data=cur.fetchone()
			artist1=data['artist_id']
			cur.execute("INSERT INTO album(album_name,Release_year,artist_id,band_id) VALUES(%s,%s,%s,%s)",(name1,year1,artist1,band1))
			mysql.connection.commit()
			cur.close()
			flash('Successfully added','success')
			return redirect(url_for('dashboard'))

	return render_template('add_album.html',form=form1)

@app.route('/play/<vid_id>')
@is_logged_in
def Play(vid_id):
	cur=mysql.connection.cursor()
	cur.execute("SELECT *FROM tracks WHERE Vid_id=%s",[vid_id] )
	data=cur.fetchone()
	Name=data['title']
	cur.execute("SELECT *FROM artists WHERE artist_id=%s",[data['artist_id']])
	data1=cur.fetchone()
	Art=data1['A_name']
	cur.execute("SELECT *FROM band WHERE band_id=%s",[data['band_id']])
	data2=cur.fetchone()
	band=data2['B_name']

	
	return render_template("Player.html",Name=Name,Art=Art,band=band)


@app.route('/Search')
@is_logged_in

def Search():
	return render_template("search.html")


@app.route('/SearchSong',methods=['GET','POST'])
@is_logged_in
def SearchSong():
	if request.method=="POST":
		song=request.form['song']
		song='%'+song+'%'
		cur=mysql.connection.cursor()
		cur.execute("SELECT * FROM tracks WHERE title LIKE %s ",[song])
		data=cur.fetchall()
		if(len(data)==0):
			flash("No Song as such found",'danger')
		else:
			return render_template('SearchSong.html',data=data)
	return render_template('SearchSong.html')


@app.route('/SearchBand',methods=['GET','POST'])
@is_logged_in
def SearchBand():
	if request.method=="POST":
		band=request.form['band']
		band='%'+band+'%'
		cur=mysql.connection.cursor()
		cur.execute("SELECT * FROM band WHERE B_name LIKE %s ",[band])
		data=cur.fetchall()
		if(len(data)==0):
			flash("No Band as such found",'danger')
		else:
			return render_template('SearchBand.html',data=data)
	return render_template('SearchBand.html')


@app.route('/SearchArtist',methods=['GET','POST'])
@is_logged_in
def SearchArtist():
	if request.method=="POST":
		artist=request.form['artist']
		artist='%'+artist+'%'
		cur=mysql.connection.cursor()
		cur.execute("SELECT * FROM artists WHERE A_name LIKE %s ",[artist])
		data=cur.fetchall()
		if(len(data)==0):
			flash("No artist as such found",'danger')
		else:
			return render_template('SearchArtist.html',data=data)
	return render_template('SearchArtist.html')


@app.route('/SearchAlbum',methods=['GET','POST'])
@is_logged_in
def SearchAlbum():
	if request.method=="POST":
		album=request.form['album']
		album='%'+album+'%'
		cur=mysql.connection.cursor()
		cur.execute("SELECT * FROM album WHERE Album_name LIKE %s ",[album])
		data=cur.fetchall()
		if(len(data)==0):
			flash("No album as such found",'danger')
		else:
			return render_template('SearchAlbum.html',data=data)
	return render_template('SearchAlbum.html')


@app.route('/playlists',methods=['GET','POSt'])
@is_logged_in
def playlist():
	cur=mysql.connection.cursor()
	username=session['username']
	cur.execute("SELECT * FROM users WHERE username = %s",[username])
	result=cur.fetchone()
	idd=result['id']
	cur.execute("SELECT*FROM playlist WHERE user_id=%s",[idd])
	result=cur.fetchall()
	if len(result)==0:
		msg="No playlist"
	else:
		msg="Your playlists"
	mysql.connection.commit()
	return render_template("playlist.html",msg1=msg,result=result)





@app.route('/create_playlist',methods=['GET','POST'])
@is_logged_in
def createplaylist():
	form=make_playlist(request.form)
	if request.method=='POST' and form.validate():
		title=form.title.data

		cur=mysql.connection.cursor()

		
		username=session['username']

		row=cur.execute("SELECT * FROM users WHERE username = %s",[username])
		result=cur.fetchone()
		idd=result['id']
		cur.execute("INSERT INTO playlist(title,user_id) VALUES (%s,%s)",([title],idd))
		mysql.connection.commit()
		cur.close()

		flash("Succesfully created",'success')

		return redirect(url_for('dashboard'))
	return render_template('add_playlist.html',form=form)

@app.route('/play_list/<play_id>',methods=['GET','POST'])
@is_logged_in
def play_list(play_id):
	cur=mysql.connection.cursor()
	username=session['username']
	cur.execute("SELECT * FROM users WHERE username = %s",[username])
	result=cur.fetchone()
	idd=result['id']
	cur.execute("SELECT*FROM playlist WHERE playlist_id=%s",[play_id])
	Name=cur.fetchone()
	Name=Name['title']
	cur.execute("SELECT *FROM tracks WHERE song_id IN(SELECT song_id FROM track_listing WHERE playlist_id=%s)",[play_id])
	data=cur.fetchall()
	P=play_id
	return render_template("play_list.html",Name=Name,play_id=P,data=data)

@app.route('/addplay/<play_id>',methods=['GET','POST'])
@is_logged_in
def add_play_list(play_id):
	P=play_id
	if request.method=="POST":
		song=request.form['song']
		song='%'+song+'%'
		cur=mysql.connection.cursor()
		cur.execute("SELECT * FROM tracks WHERE title LIKE %s ",[song])
		S=cur.fetchall()
		if(len(S)==0):
			flash("No Song as such found",'danger')
		return render_template("add_play_list.html",data=S,play_id=P)
	return render_template("add_play_list.html")

@app.route('/add/<play_id>/<Sid>',methods=['GET','POST'])
@is_logged_in
def add(play_id,Sid):
	cur=mysql.connection.cursor()
	check=cur.execute("SELECT *FROM track_listing WHERE playlist_id=%s AND song_id=%s",(play_id,Sid))
	if check==1:
		flash("Song already in playlist",'danger')
	else:
		cur.execute("INSERT into track_listing (playlist_id,song_id) VALUES(%s,%s)",(play_id,Sid))
		flash("Song successfully added to playlist",'success')
	P=play_id
	mysql.connection.commit()
	return redirect(url_for('add_play_list',play_id=P))
	return render_template('add_play_list.html')


if __name__=='__main__':
	
	app.run(debug=True)