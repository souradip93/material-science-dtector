# material-science-dtector

Steps to install :-

1. Run the setup.sh bash file
    `./setup.sh`
    
2. Install science parser application
    `./scienceparse.sh`
    
3. Run science parse application
     `java -Xmx6g -jar science-parse-server-assembly-2.0.3.jar`
     
4. Run the webserver
     `python manage.py runserver 0.0.0.0:1993`
     
     
Open http://localhost:1993 in your browser.
