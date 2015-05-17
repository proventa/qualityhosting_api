#!/usr/bin/python
import mechanize
import cookielib
import json
from urllib2 import HTTPError
from bs4 import BeautifulSoup
import urlparse

class QualityHosting(object):
  #Headers for all json requests
  json_headers = {'Content-Type':'application/json; charset=UTF-8','Accept':'application/json, text/javascript, */*; q=0.01','X-Requested-With':'XMLHttpRequest'}

  def __init__(self,base_url='https://customer.qualityhosting.de/'):
    self.base_url=base_url

    # Browser
    self.br = mechanize.Browser()

    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    self.br.set_cookiejar(cj)

    # Browser options
    self.br.set_handle_equiv(True)
    self.br.set_handle_gzip(False)
    self.br.set_handle_redirect(True)
    self.br.set_handle_referer(True)
    self.br.set_handle_robots(False)

    # Follows refresh 0 but not hangs on refresh > 0
    self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

    # User-Agent (this is cheating, ok?)
    self.br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

  def login(self, username, passwd):
    #get the login form
    r = self.br.open(self.base_url+'Login.aspx')

    #then login
    self.br.select_form(nr=0)
    self.br.form['ctl00$ContentPlaceHolder$Login1$UserName']=username
    self.br.form['ctl00$ContentPlaceHolder$Login1$Password']=passwd
    response = self.br.submit(name='ctl00$ContentPlaceHolder$Login1$LoginButton')

    # extract account ID
    for l in self.br.links(url_regex='ExchangeContainer.aspx'):
        url=urlparse.urlparse(l.url)
        qs=urlparse.parse_qs(url.query)
        self.account_id=qs['AccountId'][0]
    
    #set default containers
    exchange_containers = self.listExchangeContainers()
    self.setExchangeContainer(exchange_containers[0])

  def changeExchangePassword(self,userid,new_passwd):
    #get the form
    r = self.br.open(self.base_url+'Exchange/user_editpassword.aspx?AdUserId='+str(userid))

    #then submit
    self.br.select_form(nr=0)
    self.br.form['ctl00$ContentPlaceHolder$txtPassword']=new_passwd
    self.br.form['ctl00$ContentPlaceHolder$txtPassword2']=new_passwd
    r = self.br.submit(name='ctl00$ContentPlaceHolder$btnSavePassword')
    if 'successMessageDiv' in r.read():
        return True

    return False

  def deleteExchangeUser(self,userid):
    #get the form
    r = self.br.open(self.base_url+'Exchange/user_delete.aspx?AdUserId='+str(userid)+'&CancelationOption=deleteAllServices&EarlierChildDelete=False&DeleteUser=true')

    if 'errorMessageDiv' in r.read():
        return False

    return True


  def createExchangeUser(self,mail,first_name,last_name,new_passwd,container=None,price_list=None):
    if container is None:
        container=self.exchange_container

    mail_parts=mail.split('@')
    username=mail_parts[0]
    domain=mail_parts[1]
    #get the form
    r = self.br.open(self.base_url+'Exchange/user_add.aspx?ContainerId='+str(container))

    #then create user
    self.br.select_form(nr=0)
    self.br.form['ctl00$ContentPlaceHolder$txtUserName']=username
    self.br.find_control('ctl00_ContentPlaceHolder_drpDomain_ClientState').readonly = False
    self.br.form['ctl00_ContentPlaceHolder_drpDomain_ClientState']='{"value":"'+domain+'"}'
    self.br.form['ctl00$ContentPlaceHolder$txtGivenName']=first_name
    self.br.form['ctl00$ContentPlaceHolder$txtSurName']=last_name
    self.br.form['ctl00$ContentPlaceHolder$txtDisplayName']=last_name+', '+first_name
    self.br.form['ctl00$ContentPlaceHolder$txtPassword']=new_passwd
    self.br.form['ctl00$ContentPlaceHolder$txtPassword2']=new_passwd
    if price_list is None:
      self.br.find_control('ctl00$ContentPlaceHolder$lstPricing').items[0].selected=True
    else:
      self.br.form['ctl00$ContentPlaceHolder$lstPricing']=price_list
    self.br.find_control('ctl00$ContentPlaceHolder$chkAcceptAgreements').items[0].selected=True
    r = self.br.submit(name='ctl00$ContentPlaceHolder$btnAddUser')
    
    #check for result
    if 'errorMessageDiv' in r.read():
        return False

    return True

  def addMailToExchangeUser(self,user_id,mail,set_as_primary=True):
    mail_parts=mail.split('@')
    username=mail_parts[0]
    domain=mail_parts[1]
    #get the form
    r = self.br.open(self.base_url+'Exchange/user_emailaddresses.aspx?AdUserId='+str(user_id))

    #then create user
    self.br.select_form(nr=0)
    self.br.form['ctl00$ContentPlaceHolder$txtUserName']=username
    self.br.find_control('ctl00_ContentPlaceHolder_drpDomain_ClientState').readonly = False
    self.br.form['ctl00_ContentPlaceHolder_drpDomain_ClientState']='{"value":"'+domain+'"}'
    self.br.find_control('ctl00$ContentPlaceHolder$chkIsPrimaryAddress').items[0].selected=set_as_primary
    r = self.br.submit(name='ctl00$ContentPlaceHolder$btnAddEmailAddress')
    
    #check for result
    if 'errorMessageDiv' in r.read():
        return False

    return True

  def listExchangeUserMails(self,user_id):
    #get the form
    r = self.br.open(self.base_url+'Exchange/user_emailaddresses.aspx?AdUserId='+str(user_id))
    soup = BeautifulSoup(r.read())
    result={}
    for tr in soup.find(id="ctl00_ContentPlaceHolder_RadGridAdUserEmailAddresses_ctl00").find("tbody",recursive=False).find_all('tr'):
        tds=tr.find_all('td')
        result[str(tds[1].string)]=int(tds[0].string)
    return result

  def removeMailFromExchangeUser(self,user_id,mail_id):
    #get the form
    r = self.br.open(self.base_url+'Exchange/user_emailaddresses.aspx?DeleteEmail='+str(mail_id)+'&AdUserId='+str(user_id))

  def setPrimaryMailOfExchangeUser(self,user_id,mail_id):
    #get the form
    r = self.br.open(self.base_url+'Exchange/user_emailaddresses.aspx?SetPrimary='+str(mail_id)+'&AdUserId='+str(user_id))

  def listContainers(self,container_url):
    r = self.br.open(container_url+'?AccountId='+self.account_id)
    soup = BeautifulSoup(r.read())
    result=[]
    for tr in soup.find(id="ctl00_ContentPlaceHolder_RadGridAdContainer_ctl00").find("tbody",recursive=False).find_all('tr'):
        result.append(int(tr.td.contents[0]))
    return result
  
  def listExchangeContainers(self):
    return self.listContainers(self.base_url+'Exchange/ExchangeContainer.aspx')
      
  def setExchangeContainer(self,container):
    self.exchange_container=container

  def findExchangeUsersByMail(self,mail,max_count=10,offset=0,container=None):
    if container is None:
      container=self.exchange_container
    #search for the user
    params = {"startRowIndex":offset,"maximumRows":max_count,"sortExpression":[],"filterExpression":[{"FieldValue":mail,"ColumnUniqueName":"allfilter"}],"containerId":container}
    data = json.dumps(params)
    request = mechanize.Request(self.base_url+'WebServices/Exchange.asmx/GetAdUsersAndCount', data=data, headers=self.json_headers)
    response = self.br.open(request)

    users=json.loads(self.br.response().read())

    return users['d']['Data']

  def getExchangeUserId(self,mail):
    users = self.findExchangeUsersByMail(mail) 
    return users[0]['Id']

