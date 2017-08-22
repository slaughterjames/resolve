#!/usr/bin/python
'''
Resolve v0.1 - Copyright 2017 James Slaughter,
This file is part of Resolve v0.1.

Resolve v0.1 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Resolve v0.1 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Resolve v0.1.  If not, see <http://www.gnu.org/licenses/>.
'''
#python import
import sys
import os
import datetime
import time
import httplib
import socket
import re
import smtplib

from email.mime.text import MIMEText
from termcolor import colored

#programmer generated imports
from controller import controller
from fileio import fileio

'''
ConfRead()
Function: - Reads in the resolve.conf config file and assigns some of the important
            variables
'''
def ConfRead():
        
    ret = 0
    intLen = 0
    FConf = fileio()
    try:
        #Conf file hardcoded here
    	FConf.ReadFile('/opt/resolve/resolve.conf')
    except:
        print colored('[x] Unable to read configuration file!  Terminating...', 'red', attrs=['bold'])
        return -1
    
    for line in FConf.fileobject:
        intLen = len(line)            
        if (CON.debug == True):
            print '[DEBUG]: ' + line
        if (line.find('domains') != -1):                
            CON.domains = line[8:intLen]            
        elif (line.find('recipients') != -1):                
            CON.recipients = line[11:intLen]
        elif (line.find('email') != -1):
            CON.email = line[6:intLen]
        elif (line.find('password') != -1):
            CON.password = line[9:intLen]
        elif (line.find('subject') != -1):
            CON.email_subject = line[8:intLen]        
        elif (line.find('maxsleeptime') != -1):
            CON.maxsleeptime = line[13:intLen]
        else:
            if (CON.debug == True): 
                print ''

    if (len(CON.email) < 3):
        print colored('[x] Please enter a valid sender e-mail address in the resolve.conf file.  Terminating...', 'red', attrs=['bold'])
        print ''
        return -1    

    if (len(CON.password) < 3):
        print colored ('[x] Please enter a valid sender e-mail password in the resolve.conf file.  Terminating...', 'red', attrs=['bold'])
        print ''
        return -1

    if (len(CON.domains) < 3):
        print colored('[x] Please enter a valid domains file in the resolve.conf file.  Terminating...', 'red', attrs=['bold'])
        print ''
        return -1

    if (len(CON.recipients) < 3):
        print colored('[x] Please enter a valid recipients file in the resolve.conf file.  Terminating...', 'red', attrs=['bold'])
        print ''
        return -1

    if (len(CON.email_subject) < 3):
        print '[-] No custom e-mail subject entered.  Using: "Resolve: Domain Alert"'
        CON.email_subject == 'Resolve: Domain Alert'            
        print ''

    try:
        # Read in our list of keywords
        with open(CON.domains.strip(),"r") as fd:
            file_contents = fd.read()
            CON.domains_list      = file_contents.splitlines()

    except:
        print colored('[x] Unable to read domains file: ' + CON.domains, 'red', attrs=['bold'])
        return -1

    try:

        # Read in our list of recipients
        with open(CON.recipients.strip(),"r") as fd:
            file_contents2 = fd.read()
            CON.recipient_list    = file_contents2.splitlines()

    except:
        print colored('[x] Unable to read recipients file: ' + CON.recipients, 'red', attrs=['bold'])
        return -1
         
    print '[*] Finished configuration successfully.\n'
            
    return 0

'''
Parse() 
Function: - Parses program arguments
'''
def Parse(args):        
    option = ''
                    
    print '[*] Arguments: \n'
    try:
        for i in range(len(args)):
            if args[i].startswith('--'):
                option = args[i][2:]                         

                if option == 'debug':
                    CON.debug = True
                    print option + ': ' + str(CON.debug)
        return 0
    except:
        print colored('[x] Unable to parse program arguments.  Terminating...', 'red', attrs=['bold'])
        return -1

'''
is_website_online() 
Function: - This function checks to see if a host name has a DNS entry by checking
            for socket info. If the website gets something in return, 
            we know it's available to DNS.
'''
def is_website_online(domain):
    try:
        data = socket.gethostbyname(domain)
        ip = repr(data)
        print '[*] Successfully resolved domain ' + domain + ' over DNS to ' + str(ip) + '...'
    except socket.gaierror:
        print colored('[x] Unable to contact ' + domain + ' via DNS Resolution.  This may be an indication of an issue...', 'red', attrs=['bold'])
        Email(domain, 'DNS Resolution')
        return False
    else:
        return True

'''
is_page_available() 
Function: - This function retreives the status code of a website by requesting
            HEAD data from the host. This means that it only requests the headers.
            If the host cannot be reached or something else goes wrong, it returns
            False.
'''
def is_page_available(domain):
  
    path="/"
    try:
        conn = httplib.HTTPConnection(domain)
        conn.request('HEAD', path)
        if re.match('^[23]\d\d$', str(conn.getresponse().status)):
            print '[*] Successfully contacted ' + domain + ' via HTTP...'
            return True
    except StandardError:
        print colored ('[x] Unable to contact ' + domain + ' via HTTP.  This may be an indication of an issue...', 'red', attrs=['bold'])
        Email(domain, 'HTTP')
        return False

'''
Email()
Function: - Sends the alert e-mail from the address specified
            in the configuration file to potentially several addresses
            specified in the "recipients.txt" file.
'''
def Email(domain, function): 

    email_body = 'Hello, we have been unable to contact ' + domain + ' via ' + function 

    for recipient_entry in CON.recipient_list:

        print "[-] Sending e-mail to: " + recipient_entry                          
           
        # Build the email message
        msg = MIMEText(email_body)
        msg['Subject'] = CON.email_subject.strip()
        msg['From']    = CON.email.strip()
        msg['To']      = recipient_entry
    
        server = smtplib.SMTP("smtp.gmail.com",587)
    
        server.ehlo()
        server.starttls()
        server.login(CON.email.strip(),CON.password.strip())
        server.sendmail(recipient_entry,recipient_entry,msg.as_string())
        server.quit()
    
        print "[*] Alert email sent!"

'''
Sleep()
Function: - Sleeps the program for a time specifed in the resolve.conf file
'''     
def Sleep(sleep_time):
    
    last_loop_time = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    print '\n[*] Last loop time: ' + last_loop_time
    print '[*] Sleeping for: ' + str(sleep_time) + ' seconds...\n'
    time.sleep(sleep_time)

'''
Terminate()
Function: - Attempts to exit the program cleanly when called  
'''     
def Terminate(exitcode):
    sys.exit(exitcode)

'''
This is the mainline section of the program and makes calls to the 
various other sections of the code
'''
if __name__ == '__main__':

    ret = 0 
    count = 0  

    CON = controller() 

    ret = Parse(sys.argv)
    if (ret != 0):
        #Usage()
        Terminate(ret) 

    ret = ConfRead()
    # Something bad happened...bail
    if (ret != 0):
        Terminate(ret)    


    # Now perform the main loop
    print '[-] Inititating main loop...\n'
    while True: 

        for domain in CON.domains_list:
            is_website_online(domain)
            is_page_available(domain)             
            
        Sleep(int(CON.maxsleeptime))

'''
END OF LINE
'''    
