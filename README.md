# Flask-Music-Mangement-System
A music management system where users can upload songs of their choice, create playlists and play music with the help of a simple HTML play button.
### Prerequisites
    Python 3.0,flask module
    mysql
  
### Packages required:
    flask
    passlib
    flask_mail
    flask_mysqldb
    wtforms
    bs4
    youtube-dl(Install using 'sudo pip3 install --upgrade youtube-dl'  )
    
### Installing Packages
    * Do pip3 install -r requirements.txt

### Import sql table
    * Create Database named as my_music in my_music.
    * mysql -u root -p my_music < table.sql

### How to Run app:
    * Clone the repo to your local machine.
    * Install the above given packages.
    * Replace the app.config['MYSQL_PASSWORD']='Enter your sqlpassword'( line 21 in app.py) with you sql password.
    
    *Import the table.sql using above steps.
    * Then do python3 app.py.
    * open http://127.0.0.1:5000/ in Your local browser.
    
### Features
     * Login
     * Register 
     * Play songs using HTML music player.
     * Create Private  playlists.
     * Upload songs into database using Youtube watchID. 
     * Search songs by Name,artist name, album and band
   
 

   
   
  
 
 
   

