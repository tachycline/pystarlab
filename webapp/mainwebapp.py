from flask import Flask, render_template, request
import sys
sys.path.append("..")
import pystarlab

#Configuration
DEBUG = True 

app = Flask(__name__)
app.config.from_object(__name__)

command_list=[]
commands = pystarlab.starlab.COMMANDS
command_list=list(map(repr,command_list)) 

@app.route('/')
def starlab():
    return render_template('form.html', commands=commands)

@app.route('/post.html', methods=['POST'])
def create():
    model = request.form['make']
    if model == 'Sphere':
        cluster = pystarlab.Makesphere(n=500, R=3)
        return render_template('pretty.html', command_list)
    elif model == 'Cube':
        cluster = pystarlab.Makecube()
        return render_template('pretty.html', command_list)
    elif model == 'Plummer':
        cluster = pystarlab.Makeplummer(n=500)
        return render_template('pretty.html', command_list)
    elif model == 'King':
        cluster = pystarlab.Makeking(w=2, n=500)
        return render_template('pretty.html', command_list)
    
    

if __name__ == '__main__':
    app.run(host='0.0.0.0')
    
    
for x in commands:
    command_list.append()
    break
    
   