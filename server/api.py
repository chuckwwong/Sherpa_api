#!/usr/bin/env python3
import os, json, sys, shutil
from src import findFlows, makeEvals, sherpa
from flask import Flask, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
cors = CORS(app,origins=['http://localhost:*'])
# Create a directory in a known location to save files to.
uploads_dir = 'uploads'
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
ALLOWED_EXTENSIONS = {'json'}
if app.debug:
    print(os.getcwd())


def allowed_file(filename):
    '''
    Helper Function to make uploaded filenames secure
    '''
    return '.' in filename and \
        filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def ret_json(success=True,status=200,sess=None,flows=None,links=None,switch=None,msg=None):
    '''
    Helper Function to format json response output
    '''
    retDict = {}
    retDict['success'] = success
    if sess:
        retDict['session'] = sess
    if flows:
        retDict['flows'] = flows
    if links:
        retDict['links'] = links
    if switch:
        retDict['switches'] = switch
    if msg:
        retDict['message'] = msg
    
    return json.dumps(retDict),status,{'ContentType':'application/json'}

def get_sess_eval_out_path(request):
    '''
    This is a helper function for running experiment metric API calls
    to get the same session_name and evaluation name from user input and
    then return the file path for session, evaluation, and output generated
    '''
    if 'session_name' not in request.args:
        return ret_json(False,404,msg='file name not provided')
    # check if session exists in uploads folder
    sess = request.args["session_name"]
    session_n = os.path.join(uploads_dir,sess)
    if not os.path.exists(session_n):
        return ret_json(False,404,msg='Session does not exist')
    sess_file = os.path.join(session_n,'session.json')

    # create evaluation and output file path
    if "eval_name" not in request.args:
        return ret_json(False,404,msg='evaluation name not provided')
    eval_n = request.args['eval_name']
    out_n = eval_n + '_out.json'
    eval_n = eval_n + '_eval.json'
    eval_file = os.path.join(session_n,"evals",eval_n)
    out_file = os.path.join(session_n,"results",out_n)

    return sess_file, eval_file, out_file


@app.route('/upload',methods=["POST"])
def upload_config():
    '''
    upload network configuration json files to server
    return flows and links that user can choose to evaluate.
    Updates to file is now atomic

    Requst Arguments:
        name:       name of the session
        mh:         the minimum number of hops
    File Arguments:
        topology:   user json input of network topology
        rules:      user json input of network rules
        nodeIPs:    user json input of network IPs
    output:
        sess:       name of the created session for identification
    '''
    #parameter check
    if 'name' not in request.args:
        return ret_json(False,404,msg='name argument missing')

    for i in ['topology','rules','nodeIPs']:
        if i not in request.files:
            return ret_json(False,404,msg=i+' file not found')

    # Create experiment session folder to store all files corresponding to the experiment
    exp_name = request.args['name']
    if 'mh' not in request.args:
        mh = 0
    else:
        mh = request.args['mh']
    if not (str.isdigit(mh) and int(mh) > -1):
        return ret_json(False,404,msg='minimum hop should be an positive integer')
    folder_n = exp_name+'_mh_'+str(mh)
    session_n = os.path.join(uploads_dir,folder_n)
    if os.path.exists(session_n):
        return ret_json(False,404,msg='Session already exists, pick another name')
    try:
        os.makedirs(session_n)
        # results folder to store experiment results
        os.makedirs(os.path.join(session_n,'results'))
        # evaluation folder to store old evaluations to be reused
        os.makedirs(os.path.join(session_n,'evals'))

        # store topology, rules, nodeIPs
        topology = request.files['topology']
        if topology and allowed_file(topology.filename):
            top_f_name = secure_filename(topology.filename)
            top_path = os.path.join(session_n,top_f_name)
            topology.save(top_path)

        rules = request.files['rules']
        if rules and allowed_file(rules.filename):
            rule_f_name = secure_filename(rules.filename)
            rule_path = os.path.join(session_n,rule_f_name)
            rules.save(rule_path)

        nodeIPs = request.files['nodeIPs']
        if nodeIPs and allowed_file(nodeIPs.filename):
            IP_f_name = secure_filename(nodeIPs.filename)
            IP_path = os.path.join(session_n,IP_f_name)
            nodeIPs.save(IP_path)
        ## run findFlows to get parse files
        sess_file = os.path.join(session_n,'session.json') 
        flows_file = os.path.join(session_n,'flows.json')
        switch_file = os.path.join(session_n,'switch.json')
        findFlows.findFlows(top_path,rule_path,IP_path,mh,flows_file,sess_file,switch_file)
        # create response json returning flows and rules of session
        return ret_json(sess=folder_n) 
    except:
        print("Error",sys.exc_info()[0])
        if os.path.exists(session_n):
            shutil.rmtree(session_n)
        return ret_json(False,status=500,msg=sys.exc_info()[0])


@app.route('/load',methods=["GET"])
def load_config():
    '''
    load in configuration to use
    return flows and links that user can choose to evaluate
    
    Request Arguments:
        sess:       the session folder to be used
    output:
        session:    the session name
        flows:      the list of flows in this session with given mh
        links:      the list of links in this session with given mh

    '''
    if 'session_name' not in request.args:
        return ret_json(False,404,msg='file name not provided')
    # check if session exists in uploads folder
    sess = request.args["session_name"]
    session_n = os.path.join(uploads_dir,sess)
    if not os.path.exists(session_n):
        return ret_json(False,404,msg='Session does not exist')
    sess_file = os.path.join(session_n,'session.json')
    ## return flows and rules with the given configurations
    linksList, flowsDict, switchNodes = makeEvals.get_flows_rules(sess_file)
    # get session file and run makeEvals, and return the links and flows
    return ret_json(sess=sess,flows=flowsDict,links=linksList,switch=switchNodes)

@app.route('/sessions',methods=["GET"])
def get_sessions():
    '''
    get a list of all the configurations that were saved to file

    output:
        sessions:   list of all sessions created by the user
    '''
    configs = []
    configs = os.listdir(uploads_dir)
    for file in configs:
        # remove hidden files
        if file.startswith('.'):
            configs.remove(file)
    return json.dumps({'success':True,'sessions': configs}),200,{'ContentType':'application/json'}

@app.route('/sherpa',methods=["POST"])
def run_sherpa():
    '''
    run experiment with evaluation
    from selected links and flows to evaluate, run sherpa on

    Request Arguments:
        session_name: the session to pull previously uploaded data from
        eval_name:    name of user specified evaluation
    JSON Arguments:
        flows:        array of user selected flows to evaluate
        links:        array of user selected links to evaluate
    output:
        output file:  json output of experiment ran on evaluation
    '''
    sess_file, eval_file, out_file = get_sess_eval_out_path(request)

    # get selected flows and links array
    form_json = request.get_json()
    flows = form_json['flows']
    links = form_json['links']

    try:
        # run evalution on chosen flows and links
        makeEvals.make_Eval(sess_file,eval_file,flows,links)
        # run experiment from created evaluation
        sherpa.run_exp(eval_file,out_file)
        # fetch experiment file and return it
        return send_file(out_file,as_attachment=True)
    except:
        print("Error",sys.exc_info()[0])
        if os.path.exists(eval_file):
            shutil.rmtree(eval_file)
        if os.path.exists(out_file):
            shutil.rmtree(out_file)
        return ret_json(False,status=500,msg=sys.exc_info()[0])


@app.route('/switch',methods=["POST"])
def run_switch():
    '''
    run experiment with evaluation
    from selected switches to fail, which critical flows
    will fail

    Request Arguments:
        session_name: the session to pull previously uploaded data from
        eval_name:    name of user specified evaluation
    JSON Arguments:
        flows:        array of user selected flows to evaluate
        switch:        array of user selected links to evaluate
    output:
        output file:  json output of experiment ran on evaluation
    '''
    sess_file, eval_file, out_file = get_sess_eval_out_path(request)

    # get selected flows and switch array
    form_json = request.get_json()
    flows = form_json['flows']
    switches = form_json['switches']

    try:
        ## map selected switches to list of links
        links = makeEvals.switch2Link(sess_file,switches)
        # run evalution on chosen flows and links
        makeEvals.make_Eval(sess_file,eval_file,flows,links)
        # run experiment from created evaluation
        sherpa.run_exp(eval_file,out_file)
        # fetch experiment file and return it
        return send_file(out_file,as_attachment=True)
    except:
        print("Error",sys.exc_info()[0])
        if os.path.exists(eval_file):
            shutil.rmtree(eval_file)
        if os.path.exists(out_file):
            shutil.rmtree(out_file)
        return ret_json(False,status=500,msg=sys.exc_info()[0])

@app.route('/critf_link',methods=["POST"])
def critf_link():
    '''
    run experiment with evaluation for the metric,
    the probability that a specific flow will fail due to
    randomly failing links in L, given independent failure rate r,
    in time epoch T

    Request Arguments:
        session_name: the session to pull previously uploaded data from
        eval_name:    name of user specified evaluation
    JSON Arguments:
        flow(s):      array of user selected flows to evaluate.
                        For now, assume only a single flow
        links:        array of user selected links to evaluate
        failure_rate: failure rate of links
        time:         time epoch in which the controller is down
                        and the links are failing randomly and
                        independently.
        tolerance:    the upper bound of probability, where during
                        calculation, if the tolerance percent is exceeded,
                        the metric will stop and return the probability
                        with {tolerance}% as an upperbound.
    output:
        output file:  json output of experiment ran on evaluation
    '''
    sess_file, eval_file, out_file = get_sess_eval_out_path(request)

    form_json = request.get_json()
    flows = form_json['flows']
    links = form_json['links']
    f_rate = form_json['failure_rate']
    time = form_json['time']
    tolerate = form_json['tolerance']

    # create parameter dictionary
    param = {'failure_rate':f_rate,'time':time,'tolerance':tolerate}

    try:
        ## create evaluation file to be stored in 
        makeEvals.make_Eval(sess_file,eval_file,flows,links,param,type_m="link")
        ## from evaluation file run sherpa to generate the metric
        sherpa.run_critf(eval_file,out_file)
        ## return the output from the experiment
        return send_file(out_file,as_attachment=True)
    except:
        print("Error",sys.exc_info()[0])
        if os.path.exists(eval_file):
            shutil.rmtree(eval_file)
        if os.path.exists(out_file):
            shutil.rmtree(out_file)
        return ret_json(False,status=500,msg=sys.exc_info()[0])

@app.route('/critf_switch',methods=["POST"])
def critf_switch():

    sess_file, eval_file, out_file = get_sess_eval_out_path(request)

    form_json = request.get_json()
    flows = form_json['flows']
    switches = form_json['switches']
    f_rate = form_json['failure_rate']
    time = form_json['time']
    tolerate = form_json['tolerance']

    # create parameter dictionary
    param = {'failure_rate':f_rate,'time':time,'tolerance':tolerate}

    try:
        ## create evaluation file to be stored in 
        makeEvals.make_Eval(sess_file,eval_file,flows,links=switches,param=param,type_m="switch")

        sherpa.run_critf(eval_file,out_file,type_m="switch")
        return send_file(out_file,as_attachment=True)
    except:
        print("Error",sys.exc_info()[0])
        if os.path.exists(eval_file):
            shutil.rmtree(eval_file)
        if os.path.exists(out_file):
            shutil.rmtree(out_file)
        return ret_json(False,status=500,msg=sys.exc_info()[0])

@app.route('/critf_neigh',methods=["POST"])
def critf_neigh():

    sess_file, eval_file, out_file = get_sess_eval_out_path(request)

    form_json = request.get_json()
    #flows = form_json['flows']
    switches = form_json['switches']
    f_rate = form_json['failure_rate']
    time = form_json['time']
    hops = form_json['hops']
    tolerate = form_json['tolerance']

    # create parameter dictionary
    param = {'failure_rate':f_rate,'time':time,'hops':hops,'tolerance':tolerate}

    try:
        ## create evaluation file to be stored in 
        makeEvals.make_Eval(sess_file,eval_file,flows=None,links=switches,param=param,type_m="neigh")
        ## from evaluation file, run sherpa neighborhood
        sherpa.run_critf(eval_file,out_file,type_m="neigh")
        return send_file(out_file,as_attachment=True)
    except:
        print("Error",sys.exc_info()[0])
        if os.path.exists(eval_file):
            shutil.rmtree(eval_file)
        if os.path.exists(out_file):
            shutil.rmtree(out_file)
        return ret_json(False,status=500,msg=sys.exc_info()[0])

@app.route('/evals',methods=["GET"])
def get_evals():
    '''
    To be made in the next step.
    This Api will get list of all evaluations corresponding to
    this session.

    Request Arguments:
        session_name: name of the session upload
    output:
        evaluations:  list of the evaluations that were previously created
    '''
    if 'session_name' not in request.args:
        return ret_json(False,404,msg='file name not provided')
    # check if session exists in uploads folder
    sess = request.args["session_name"]
    session_n = os.path.join(uploads_dir,sess)
    if not os.path.exists(session_n):
        return ret_json(False,404,msg='Session does not exist')
    eval_fol_p = os.path.join(session_n,'evals')
    if not os.path.exists(eval_fol_p):
        return ret_json(False,404,msg='Evalution Folder does not exist')

    evals = []
    for file in os.listdir(eval_fol_p):
        # only add evaluation files to return response
        if file.endswith('_eval.json'):
            evals.append(file)
    return json.dumps({'success':True,'evaluations': evals}),501,{'ContentType':'application/json'}

@app.route('/rm_sess',methods=["DELETE"])
def rm_sess():
    '''
    To be made in the next step.
    This API will allow users to remove old evalutions
    from the eval folder
    '''
    try:
        if 'session_name' not in request.args:
            return ret_json(False,400,msg='file name not provided')
        # check if session exists in uploads folder
        sess = request.args["session_name"]
        session_n = os.path.join(uploads_dir,sess)
        if not os.path.exists(session_n):
            return ret_json(False,400,msg='Session does not exist')
        ## delete the folder
        shutil.rmtree(session_n)
        # 
        return ret_json(True,status=200)
    except:
        return ret_json(False,status=500,msg=sys.exc_info()[0])


if __name__ == '__main__':
    app.run(debug=True)