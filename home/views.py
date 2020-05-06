from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.views.decorators.csrf import csrf_exempt

import sys
sys.path.append('pytorch_lstmcrf-master/')
sys.path.append('pytorch_lstmcrf-master/create_dataset/')
sys.path.append('pytorch_lstmcrf-master/ner_predictor/')

import subprocess
import os
import uuid
import sys
import json
import urllib
import shlex
from datetime import datetime
from threading import Thread
import logging


from create_dataset import CreateDataset
from predict_instances import NERPredictor, read_parse_write
from final_results_ import predict, read_txt
from create_test_ import persection_conversion


logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

session_files = 'static/session_files/'
model_path = 'pytorch_lstmcrf-master/all_mimicking_model_part2/all_mimicking_model_part2.tar.gz'

logger.info('Loading')
model = NERPredictor(model_path, cuda_device="cpu")

print = logger.info

@csrf_exempt
def home(request):
    return render(request, 'home.html')

def create_test(pdfjson, parsed_json_filepath, mat=False):
    fname = (parsed_json_filepath.split('/'))[-1]

    fout = open(session_files+fname+'.test', 'w')
    fout.write(pdfjson)
    fout.close()

    labels = []
    lines = []

    create_data = CreateDataset(False,True,True)
    create_data.processFile(parsed_json_filepath, labels, lines)

    processed_file = session_files + fname + '.prepdfprocessed'
    if mat:
        processed_file = session_files + fname + '.pdfprocessed'

    fout = open(processed_file, 'w')
    create_data.tagLabels(labels, lines, fout)
    fout.close()

    if not mat:
        persection_conversion(processed_file, session_files + fname + '.pdfprocessed')

def predict_instances(processed_pdf, file, mat=False):
    with open(processed_pdf) as f:
        sentences = []
        labels = []
        sections = []

        sentence = ''
        label = []
        for line in f:
            line = line.strip()
            if line=='':
                if sentence.strip()!='':
                    sentences.append(' '.join(sentence.strip().split()[1:]))
                    labels.append(label[1:])
                    sections.append(label[0])
                    
                sentence = ''
                label = []
            else:
                sentence += line.split()[0]+' '
                label.append(line.split()[1])
                
        if sentence.strip()!='':
            sentences.append(' '.join(sentence.strip().split()[1:]))
            labels.append(label[1:])
            sections.append(label[0])

        # print(sentences[0])
        prediction = None
        if mat:
            prediction = mat_model.predict(sentences)
        else:
            prediction = model.predict(sentences)

        y_pred=[]
        y_true=[]

        logger.info(file)
        fout = open(file, 'w')
        for i,words in enumerate(sentences):
            words = words.split()
            fout.write('section '+sections[i]+'\n')
            for j,word in enumerate(words):
                if prediction[i][j].startswith('S-'):
                    prediction[i][j] = 'B-'+prediction[i][j][2:]
                if prediction[i][j].startswith('E-'):
                    prediction[i][j] = 'I-'+prediction[i][j][2:]
                if "Material" in prediction[i][j]:
                    prediction[i][j] = prediction[i][j][:2] + "MATERIAL"
                if "Material" in labels[i][j]:
                    labels[i][j] = labels[i][j][:2] + "MATERIAL"

                y_pred.append(prediction[i][j])
                y_true.append(labels[i][j])
                fout.write(word+' '+prediction[i][j]+' '+labels[i][j]+'\n')
            fout.write('\n')
        fout.close()


def merge_method(predictions):
    methods = list(predictions["METHOD"].keys())
    methods_ = []
    methods.sort(key = lambda x : len(x))
    for i in range(len(methods)):
        invalid = False
        for j in range(i+1, len(methods)):
            if methods[i].lower() in methods[j].lower():
                 invalid = True
                 break
        if invalid:
            methods_.append(methods[i])
    
    for method in methods_:
        del predictions["METHOD"][method]

    if len(predictions["METHOD"]) == 0:
        del predictions["METHOD"]

def final_results(file):

    sentences, sections, labels, insts = read_txt(file=file)
    _,predictions, values_s, values_p, _ = predict(sentences, file, insts, False, True, False, False)
    
    if "METHOD" in predictions:   
        merge_method(predictions)

    output = {"predictions":{}, "parameter_lines" : [], "structure_lines" : []}
    for label in predictions:
        output["predictions"][label] = list(predictions[label].keys())

    output["parameter_lines"] = values_p
    output["structure_lines"] = values_s
    return output

def get_results(pdfjson, parsed_json_filepath):
    # client_id = str(uuid.uuid1())

    create_test(pdfjson, parsed_json_filepath)

    fname = (parsed_json_filepath.split('/'))[-1]
    predict_instances(session_files + fname + '.pdfprocessed', session_files + fname + '.pdf.prediction', False)
    output = final_results(session_files + fname + '.pdf.prediction')

    # predict_instances(session_files+client_id+'pdf_processed.pdf.txt', session_files+client_id+'.pdf.prediction', True)
    # output_mat_structure = final_results(session_files+client_id+'.pdf.prediction')

    result = {"parameter_lines":[], "structure_lines":[], "predictions":{}}
    # if 'MATERIAL' in output_mat_structure["predictions"]:
    #     result["predictions"]['MATERIAL'] = output_mat_structure["predictions"]['MATERIAL']

    # if 'STRUCTURE' in output_mat_structure["predictions"]:
    #     result["predictions"]['STRUCTURE'] = output_mat_structure["predictions"]['STRUCTURE']

    for each in output["predictions"]:
        # if each in ['MATERIAL', 'STRUCTURE']:
        #     continue
        result["predictions"][each] = output["predictions"][each]

    # result["structure_lines"] = output_mat_structure["structure_lines"]
    result["parameter_lines"] = output["parameter_lines"]
    result["structure_lines"] = output["structure_lines"]

    return result

def process_thread(results, file_path):
    index = file_path.index('static')
    file_path = file_path[index:]
    fname = file_path.split('/')[-1]
    subprocess.call("curl -s --noproxy \"*\" -H \"Content-type: application/pdf\" -F file=@\""+ file_path +"\" \"http://localhost:8080/v1\" > \"science/"+fname+".json\"", shell=True);
    results.append({"path":'science/'+fname+'.json', "fname":'.'.join(fname.split('.')[1:])})


@csrf_exempt
def memory(request):
    cmd = "nvidia-smi | awk '/Default/ {print $9}'"
    ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output = ps.communicate()[0]
    output = (output.decode('UTF-8')).strip()
    return HttpResponse(output);

@csrf_exempt
def submit(request):
    # try:
    body = json.loads(request.body)
    files = body["files"];
    # output = get_results(request.POST.get('pdftext'))
    parsed_json_file = files[0]
    output = get_results('\n'.join(open(files[0], 'r').readlines()), parsed_json_file)
    return JsonResponse(output, safe=False)
    # except Exception as e:
    #     print(e)
    #     print(sys.exc_info()[0])
    #     return HttpResponse(status=500)
    
@csrf_exempt
def upload2( request ):

    # The assumption here is that jQuery File Upload
    # has been configured to send files one at a time.
    # If multiple files can be uploaded simulatenously,
    # 'file' may be a list of files.

    try:
        file = request.FILES[u'files[]']

        result = []

        for filename, file in request.FILES.items():
            client_id = str(uuid.uuid1())
            name = request.FILES[filename].name
            size = request.FILES[filename].size
            url = session_files + client_id + "." + name
            thumbnailUrl = "static/img/thumbnail.png"

            fout = open(url, 'wb+')
            for line in file.chunks():
                fout.write(line)
            fout.close()

            result.append({"url":url, "name":name, "size":size, "thumbnailUrl": thumbnailUrl})

        # print(result)
        return JsonResponse({"files":result}, safe=False)

    except Exception as e:
        print(e)
        print(sys.exc_info()[0])
        return HttpResponse(status=500)

@csrf_exempt
def show_json(request):
    path = request.POST.get('path')
    out = ''
    with open(path) as f:
        for line in f:
            out += line.replace('\\n', ' ')
    return HttpResponse(out);

@csrf_exempt
def process(request):
    body = json.loads(request.body)
    results = []

    threads = []
    for file_path in body["paths"]:
        file_path = urllib.parse.unquote(file_path)
        t = Thread(target=process_thread, args=(results, file_path,))
        t.start()
        threads.append(t);

    for t in threads:
        t.join()
        
    return JsonResponse(results, safe=False)

@csrf_exempt
def upload(request):
    # print(request.FILES['file'].read())

    try:
        client_id = str(uuid.uuid1())
        fout = open(session_files+client_id + '.pdf', 'wb+')

        for line in request.FILES['file'].chunks():
            fout.write(line)
        fout.close()

        # subprocess.call("java -Xmx6g -Dhttp.proxyHost=172.16.2.30 -Dhttp.proxyPort=8080 -Dhttps.proxyHost=172.16.2.30 -Dhttps.proxyPort=8080 -jar ../../science-parse-cli-assembly-2.0.3.jar temp.pdf -o science/; sed -i 's/\\\\n/ /g' science/temp.pdf.json", shell=True)
        # subprocess.call("curl -s --noproxy \"*\" -H \"Content-type: application/pdf\" -F file=@\""+ session_files+client_id +".pdf\" \"http://localhost:8080/v1\" > science/"+client_id+".pdf.json; sed -i 's/\\\\n/ /g' science/"+client_id+".pdf.json", shell=True);
        subprocess.call("curl -s --noproxy \"*\" -H \"Content-type: application/pdf\" -F file=@\""+ session_files+client_id +".pdf\" \"http://localhost:8080/v1\" > science/"+client_id+".pdf.json", shell=True);

        
        out = ''
        with open('science/'+client_id+'.pdf.json') as f:
            for line in f:
                out += line.replace('\\n', ' ')
        return HttpResponse(out);

    except Exception as e:
        print(e)
        print(sys.exc_info()[0])
        return HttpResponse(status=500)
