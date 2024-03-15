# importing some modules 
from flask import Flask , request , render_template
import sys
# import requests 
from bs4 import BeautifulSoup
import random
import time
import cloudscraper

# defining some variables
novel_cache = {}        # for cache
start = [int(time.time())]    # record the start time


# A function to cache the data for fast loading
def cache(url,novel,chapter):
    max_data = 2e1  # Max data which can be tored
    name = novel+'-'+chapter    # the identity of the data

    # del the data if the total data cross the max limit
    if(len(novel_cache)>=max_data):
        novel_cache.pop(novel_cache.keys()[0])
    
    # Loading the data if available in cache or else request it from data
    if(name in novel_cache):
        return novel_cache[name]
    else:
        '''
        Introfuction has different lay out,
        other then into has mode of 0 in default but for inro we has to pass a value in last
        '''
        if(chapter!='intro' and chapter!='0'):
            url = url+f'{novel}/chapter-{chapter}'
            return datas(url,name)
        else:
            name = novel  
            url = url+f'{novel}/' #changing the url since it usesa different 1
            print(url)
            return datas(url,name,1)
    
# A function to clean the cache memory if the total time passed is greter then 30 min
def cleaner():
    now = int(time.time()) # calculating present time
    limit = 30*60
    # checking wether the time exceeded its limit or not
    if(now-start[0]>=limit):
        novel_cache = {}
        start[0] = now
        print('clear')
# The Function to pulling data
def datas(url,name,mode=0):
    print(url)
    scraper = cloudscraper.create_scraper(
            interpreter="nodejs",
            delay=10,
            browser={
                "browser": "chrome",
                "platform": "ios",
                "desktop": False,
            },
            captcha={
                "provider": "2captcha",
                "api_key": "d9c0745e19f7dc2faa24776d4a73eb1d",
            },
        )

    data = scraper.get(url)  # Get the data from another server
    html = data.text        # the data
    soup = BeautifulSoup(html,'html.parser')    # the data as tag
    if(data.status_code == 200 and html != None and mode ==0):   # check the status
        # extract the needed text from the p tag 
        para = soup.find('div',id='chr-content').find_all('p')
        para1 = '<h1 style="padding:10px;">'+para.pop(0).text.strip() + '</h1>' 
        para = "</p><p style='font-weight:bold;font-style: italic;'>".join([p.text.strip() for p in para]) 
        requested_data =  para1 + para  
        novel_cache[name] = requested_data  # store the data in cache memo  

        cleaner()  # excecuding clean function which clean memo 
        return requested_data
    
    # If Intro Page needed
    elif(mode!=0 and html !=None):
        description = f'<div><b>Description</b><p><i>{soup.find('div',class_='desc-text').text.strip()}</i></p></div>'
        image = f'<div><img src={soup.find('div',class_='book').find('img')['src']}></div>'
        requested_data =  image +f'<div><h2>{name}</h2></div>'+description
        novel_cache[name] = requested_data    
        cleaner()
        return requested_data

    # If Your Entered name is invelid or not in our server
    elif(data.status_code == 404 or html == None):
        Error = f'Error {data.status_code} -> May be Our Server Dont Have This Novel <br> OR <br> Please Enter a velid Novel Name and Chapter Number <br> May be {name} is a invelid name if : is present then please remove it or give a space before and after it'
        cleaner()
        return Error
    else :
        cleaner()
        return f'Error {data.status_code}'

# the main app
app = Flask(__name__, template_folder='/code/Codes/projects/flask/Templets/')

# entery of the app
@app.route('/')
def main():
    return render_template('welcome.html')

# The novel reader page where all the novel where stored
@app.route('/novel',methods=['GET'])
def novel():
    # If user Sends GET request
    if request.method == 'GET':     
        # If user Enter some Valid novel_name and chapter then ensure entry
        if (request.args.get('novel_name') == '' and request.args.get('chapter_num') == '') or (request.args.get('novel_name') == None and request.args.get('chapter_num') == None):
            return 'Invelid Inputs'
        else:
            username = request .args.get('username')  # No use of User name just for fun
            # Make novel Name suitable for our server
            novel_name = request.args.get('novel_name').lower().split(' ')
            if(':' in novel_name):
                novel_name.pop(novel_name.index(':'))
            novel_name = '-'.join(novel_name)
            # The chapter User Want to see
            chapter_num = request.args.get('chapter_num')

            # Giving user name to user if they dont enter it , Just for fun
            if(username == None or username == ''):
                del username
                username = 'User' + str(int(random.uniform(0,1)*1e6))
            # Retuning the index.html file where user can read the novel
            return render_template('index.html',novel=novel_name,chapter=chapter_num,username=username)
    else:
        return 'Invelid Request'

# A server to where index.html send POST request
@app.route('/<novel_name>/scrape',methods=['POST'])
def scrap(novel_name):
    data = request.get_json()
    chapter = data.get('chapter_num')
    user_name = data.get('user_name')
    # returning the data But also caching it
    return cache(f'https://novelbin.me/novel-book/', novel_name , chapter)

# The App
if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=5000)

