# material-science-dtector

System preparation :-

1. Install anaconda (https://docs.anaconda.com/anaconda/install/linux/)

2. Create a python 3.7 conda environment
    `conda create --name webservertest python=3.7.3`
    
3. Activate the created environment
    `conda activate webservertest`

Steps to install :-

1. Run the setup.sh bash file
    `./setup.sh`
    
2. Run science parse application in background
     `nohup java -Xmx6g -jar science-parse-server-assembly-2.0.3.jar &`
     
3. Run the webserver
     `python manage.py runserver 0.0.0.0:1993`
     
     
Open http://localhost:1993 in your browser.
