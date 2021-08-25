import random
from datetime import datetime
from re import sub
from flask import *
from flask_bootstrap import Bootstrap
import time


#baza podatata
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from jinja2.utils import F
from werkzeug.wrappers import response

#blockchain
from blockchain import Blockchain

app = Flask(__name__)
Bootstrap(app)
app.config["SECRET_KEY"] = "APP_SECRET_KEY"

#instanca blockchain-a
blockchain = Blockchain()

#kreiranje instace baze
cred = credentials.Certificate("firebase-sd.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fir-admin-e68e5-default-rtdb.europe-west1.firebasedatabase.app/'
})

@app.route("/")
def index():
    #preuzimamo promenljivu pocetak izbora
    ref = db.reference('Izbori').child('info')
    data = ref.get()
    started = data['started']
    if started  == 1:
        return redirect("/register")
    else:
        return redirect("/results")

# Display blockchain in json format
@app.route('/get_chain', methods=['GET'])
def display_chain():
    return render_template("chain.html", chain=blockchain.chain)

@app.route('/valid_block', methods=['GET','POST'])
def mine_block():
    valid = blockchain.chain_valid(blockchain.chain)
    return 'Blockchain valid ? : ' + str(valid)

@app.route("/register/", methods=["GET", "POST"])
def register():
    if "user" in session and session["user"]:
        if session["user"]["status"] == "komisija":
            return redirect("/novi_token")
        elif session["user"]["status"] == "admin":
            return redirect("/admin")

    if request.method == "POST":
        uname = request.form['uname']
        psw = request.form['psw']
       #print(uname + " -> " + psw)\
        found = False

        if uname == "admin" and psw == "admin":
            session["user"] = {
                    "username": uname,
                    "status": "admin"
                }
            return redirect("/admin")

        ref = db.reference('Izbori')
       # print(ref.child('komisija').get())
        dic = ref.child('komisija').get()
        for key, val in dic.items():
            if val['uname'] == uname and val['psw'] == psw:
                found = True
                session["user"] = {
                    "username": uname,
                    "status": "komisija"
                }
                break 

        if found == True:
            return redirect('/novi_token') 
        else:
            poruka = "* Uneti podaci nisu validni"
            return render_template("log.html", poruka=poruka)
    else:
        poruka = ""  
        return render_template("log.html", poruka=poruka)
  
@app.route("/glasanje", methods=["GET", "POST"])
def vote():
    if "token" not in session or session["token"] != 1:
        return redirect("/unos_tokena")

    ## Preuzimanje niz kandidata i slanje u html
    ref = db.reference('Izbori')
    data = ref.child('kandidati').get() 

    if request.method == "POST":
       
        izabrano = request.form['kand']

        if izabrano == "Изаберите жељеног кандидата":
            return render_template("glasanje.html", kandidati=data)

        previous_block = blockchain.print_previous_block()        
        previous_hash = blockchain.hash(previous_block)
        if "id" not in session or session["id"] == None:
            proof = 1
        else:
            proof = session["id"]
        block = blockchain.create_block(proof, previous_hash, izabrano)

        #mozda bi bilo cool da se stampa u js
        print(block)

        session["token"] = 0
        session["id"] = None

        return redirect("/unos_tokena")
    else: 
        return render_template("glasanje.html", kandidati=data)

@app.route('/novi_token', methods=['GET','POST'])
def novi_token():
    if "user" not in session or not session["user"] or session["user"]["status"] != "komisija":
        return redirect("/register")

    #provera dali je glasanje pocelo
    ref = db.reference('Izbori').child('info')
    data = ref.get()
    started = data['started']
    if started != 1:
        return "<div style=\"text-align: center; margin-top: 150px; font-family: Stencil Std, fantasy;\"><h1>Glasanje je završeno</h1><a href=\"/logout\">povratak</a></div>"


    print(session["user"]["status"])

    if request.method == "POST":
        blk = request.form['blk']
        # ovde isto da se preuzvima token
        token =  random.randint(1000, 10000)
        exists = False

        #provera dali licna karta je iskoriscena
        ref = db.reference('Izbori')
        data = ref.child('blk').get()
        #print(data)
        for key, val in data.items():
            if val == blk:
                exists = True
                break

        if exists == False:
            #upis uportebljenog tokena i licne karte
            ref = db.reference('Izbori')
            sub_ref = ref.child('tokeni')
            sub_ref.push(token)

            sub_ref = ref.child('blk')
            sub_ref.push(blk)
            return redirect("/prikaz_tokena/" + str(token))
        else:
            poruka = "* Uneseni broj licne karte je vec upotrebljen!"
            return render_template('generisanjeTokena.html', poruka=poruka)
    else:
        poruka = ""
        return render_template('generisanjeTokena.html', poruka=poruka)

@app.route('/prikaz_tokena/<int:token>')
def prikaz_token(token):
    return render_template('resultat.html', token=token)

@app.route('/unos_tokena', methods=['GET','POST'])
def unos_tokena():
    #provera dali je glasanje pocelo
    ref = db.reference('Izbori').child('info')
    data = ref.get()
    started = data['started']
    if started != 1:
        return "<div style=\"text-align: center; margin-top: 150px; font-family: Stencil Std, fantasy;\"><h1>Glasanje je završeno</h1><a href=\"/logout\">povratak</a></div>"

     #provera dali je glasanje online
    ref = db.reference('Izbori')
    data = ref.get()
    online = data['online']

    if online != 1:
        
        if request.method == 'POST':
            token = request.form['token'] 
            exists = False
            k = "ajde"

            #ovde se vrsi provera tokena
            ref = db.reference('Izbori')
            data = ref.child('tokeni').get()
            for key, val in data.items():
                if str(val) == str(token):
                    print("hehe")
                    exists = True
                    k = key

            if exists == True:
                ref.child('tokeni').child(k).delete()
                session["token"] = 1
                return redirect('/glasanje') 
            else:
                poruka = "* Uneti token nije validan!"
                return render_template('unosTokena.html', poruka=poruka)
        
        else:
            poruka = ""
            return render_template('unosTokena.html', poruka=poruka)
            
    else:
        if request.method == 'POST':
            inputBLK = request.form.get('blk')
            inputJMBG = request.form.get('jmbg')
            inp = {'blk': inputBLK,
                    'jmbg': inputJMBG}
            id = blockchain.hash(inp)
            valid = blockchain.valid_id(blockchain.chain, id)

            if valid == False:
                poruka = "* Uneseni podaci su vec korisceni ili nevalidni"
                return render_template("check.html", poruka=poruka)
            else:
                session["id"] = id
                session["token"] = 1
                return redirect("/glasanje")
        else:    
            poruka = ""
            return render_template("check.html", poruka=poruka)

@app.route('/results', methods=['GET'])
def show_results():
    #preuzimamo promenljivu pocetak izbora
    ref = db.reference('Izbori').child('info')
    data = ref.get()
    started = data['started']
    if started  == 1:
        return "<div style=\"text-align: center; margin-top: 150px; font-family: Stencil Std, fantasy;\"><h1>glasanje je u toku</h1><a href=\"/logout\">povratak</a></div>"


    chain = blockchain.chain
    #recnik koji ce sadrzati kolko glasova ima koja partija
    results = {}
    a = {}
    results['all'] = a

    #preuzimanje imena kandidata
    data = db.reference('Izbori').child('kandidati').get()
    for i in range(len(data)):
        results['all'][data[i]] = 0

    #racunanje glasova
    print(results)
    for block in chain:
        #print(block)
        for key in results['all']:
            if key == block['chosen']:
                results['all'][key] += 1
    
    #provera pobednika
    max = float('-inf')
    pobenik = ""
    for key in results['all']:
            if results['all'][key] > max:
                max = results['all'][key] 
                pobenik = key
    results['pobednik'] = pobenik

    #return str(results)
    return render_template('proba.html', res=results)    

@app.route('/admin', methods=['GET', 'POST'])
def to_admin():
    if "user" not in session or not session["user"] or session["user"]["status"] != "admin":
        return redirect("/register")
    
    #preuzimamo promenljivu pocetak izbora
    ref = db.reference('Izbori').child('info')
    data = ref.get()
    started = data['started']
    '''
    tm = data['date']
    now = datetime.now()
    print(tm[15:16])
    if int(now.strftime("%M")) >= tm[15:16]:
        print("ajdeeee")
    '''
    
    if request.method == "POST":
        textareaKandidati = request.form.get('voting-options')
        inputUser = request.form.get('user')
        inputPass = request.form.get('code')

        if textareaKandidati != None:
            ref = db.reference('Izbori').child('kandidati')
            
            options = []
            for i in textareaKandidati.split("\n"):
                options.append(i.strip())

            ref.set(options)
            return render_template("admin.html", data=data)

        elif inputUser != None and inputPass != None:
            ref = db.reference('Izbori').child('komisija')
            user = {}
            user['uname'] = inputUser
            user['psw'] = inputPass

            ref.push(user)
            return render_template("admin.html", data=data)
        else:

            if started == 0 or started == 3:
                now = datetime.now()
                m = int(now.strftime("%M"))
                s = now.strftime("%S")
                m = m + 1
                
                dt_string = now.strftime("%m/%d/%Y, %H:")
                dt_string = dt_string + str(m) + ":" + s
                print(dt_string)
                rec = {"started": 1,
                        "date": dt_string}
                ref.set(rec)
            else:
                rec = {"started": 0,
                        "date": "nema nista, ...."}
                ref.set(rec)
            #return render_template('admin.html', data=data)
            return redirect("/admin")
        
        #return render_template('admin.html')
        return "hehe admine"
    else:
        return render_template('admin.html', data=data)
    
@app.route("/logout")
def logout():
    session["user"] = None
    return redirect("/register")
    
if __name__ == "__main__":
    app.run(debug=True) 