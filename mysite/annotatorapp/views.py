from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from . import models, forms, codeforline
from .models import Sentences, WordOptions, Wordsinsentence, User, Noun, Indeclinables, Verbs, Exsentences
from .tables import WordOptionsTable, SentencesTable, WordsinsentenceTable
import json
from django_datatables_view.base_datatable_view import BaseDatatableView
import random


# renders response for index page
def index(request):
    return render(request, 'annotatorapp/index.html', {})


# returns an HttpResponse object with that rendered text.
def lineview(request):
    return render(request, 'annotatorapp/index.html', {})


# Combines annotatorapp/tables.html with the given context tabledata and returns an HttpResponse object with that rendered text.
# data is collected from the tables structure specified in tables.py
def wordtableview(request):
    tabledata = WordOptionsTable(WordOptions.objects.all())
    return render(request, 'annotatorapp/tables.html', {'tabledata': tabledata})


# Combines annotatorapp/tables.html with the given context tabledata and returns an HttpResponse object with that rendered text.
# data is collected from the tables structure specified in tables.py
def sentenceview(request):
    tabledata = SentencesTable(Sentences.objects.all())
    return render(request, 'annotatorapp/tables.html', {'tabledata': tabledata})


# Combines the template with the context and returns an HttpResponse object with that rendered text.
# data is collected from the tables structure specified in tables.py
def wordsinsentenceview(request):
    tabledata = WordsinsentenceTable(Wordsinsentence.objects.all())
    return render(request, 'annotatorapp/tables.html', {'tabledata': tabledata})

#renders a list consisting of lines and ids
def xsentenceview(request):
    l = [0,20,40,60,80,100,120,140,160,180]
    r = random.choice(l)
    ids = Exsentences.objects.values('xsent_id')[r:r+20]
    line = Exsentences.objects.values('line')[r:r+20]
    chunks = Exsentences.objects.values('chunks')[r:r+20]
    lemmas = Exsentences.objects.values('lemmas')[r:r+20]
    morph_cng = Exsentences.objects.values('morph_cng')[r:r+20]
    lists = zip(ids,line,chunks,lemmas,morph_cng)
    return render(request, 'annotatorapp/exsent.html', {'lists':lists})

# for rendering response  upon obtaining saved word data (present as Draggable operators) from the database
def get_dragdata(request):
    if request.is_ajax():
        if request.method == 'POST':
            sent_id = json.loads(request.POST['sentid'])
            Sentence1 = Sentences.objects.get(id=sent_id)
            wordsdata = WordOptions.objects.all().filter(sentence=Sentence1)
            data = codeforline.getsentwordtree(sent_id);
            print(data)
            return HttpResponse(data)
    else:
        raise Http404


# for rendering response upon saving the current selected data to database
def save_dragdata(request):
    if request.is_ajax():
        if request.method == 'POST':
            wp = json.loads(request.POST['wp'])
            wc = json.loads(request.POST['wc'])
            wr = json.loads(request.POST['wr'])
            sent_id = json.loads(request.POST['sentid'])
            Sentence1 = Sentences.objects.get(id=sent_id)
            wordsdata = WordOptions.objects.all().filter(sentence=Sentence1)
            for w in wordsdata:
                try:
                    w.isSelected = False
                    w.isEliminated = True
                    w.parent = -1
                    w.relation = ''
                    w.children = ''
                    w.save()
                except Exception as e:
                    print("wordsdata updated in ajex save_dragdata:selection elimination ")
                    print(e)
            for i in wp:
                try:
                    w = WordOptions.objects.get(id=i)
                    w.parent = int(wp[i])
                    w.isSelected = True
                    w.isEliminated = False
                    w.save()
                except Exception as e:
                    print("Wordsinsentencenot updated in ajex save_dragdata:wp ")
                    print(e)
            for i in wr:
                try:
                    w = WordOptions.objects.get(id=i)
                    w.relation = wr[i]
                    w.isSelected = True
                    w.isEliminated = False
                    w.save()
                except Exception as e:
                    print("Wordsinsentencenot updated in ajex save_dragdata:wr ")
                    print(e)
            for i in wc:
                try:
                    w = WordOptions.objects.get(id=i)
                    w.children = w.children + wc[i]
                    w.isSelected = True
                    w.isEliminated = False
                    w.save()
                except Exception as e:
                    print("Wordsinsentencenot updated in ajex save_dragdata:wc ")
                    print(e)
            return HttpResponse("Success!")
    else:
        raise Http404

#function that checks if input sentence is present in database otherwise sends request to SHR for data scrap.
#returns a dictionary and pandas dataframe with the data
def presentdataview(request):
    if request.method == "POST":
        Inputlineform = forms.inputlineform(request.POST)
        saveline = True
        if Inputlineform.is_valid():
            print('form is valid')
            try:
                Sentence = Sentences(
                    line=Inputlineform.cleaned_data['line'],
                    linetype=Inputlineform.cleaned_data['linetype'],
                )

                if not codeforline.checksent(Sentence):  # if new sentence appears
                    df = codeforline.getdatafromsite(Sentence)
                    if saveline:
                        Sentence.save()
                        codeforline.savedatafromsite(df, Sentence)
                        print("Adding Sentences data to Database \n\n")
                if codeforline.checksent(Sentence):
                    Sentence1 = Sentences.objects.get(line=Sentence.line, linetype=Sentence.linetype)
                    wordsdata = WordOptions.objects.all().filter(sentence=Sentence1)
                    words = Sentence1.line.split(' ')
                    chunknum = {}
                    c = 0
                    for word in words:
                        c = c + 1
                        chunknum[word] = c
                    sent_id = Sentence1.id
                    pos = 0
                    context = codeforline.contestofwordsdata(sent_id)
                    return render(request, 'annotatorapp/presentdata.html', context)
                else:
                    wordsdata = codeforline.worddataofsentence(df, Sentence)
                    return render(request, 'annotatorapp/presentdata.html',
                                  {'wordsdata': wordsdata, 'words': Sentence.line.split(' ')})
            except Exception as e:
                print("Sentence not inserted : ")
                print(e)
        Sentences1 = Sentences.objects.all()
        for s in Sentences1:
            sent_id = s.id
            break
        return render(request, 'annotatorapp/presentdata.html', {'sentid': sent_id})
    else:
        Sentence1 = Sentences.objects.get(id=request.session.get('sent_id'))
        wordsdata = WordOptions.objects.all().filter(sentence=Sentence1)
        words = Sentence1.line.split(' ')
        chunknum = {}
        c = 0
        for word in words:
            c = c + 1
            chunknum[word] = c
        sent_id = Sentence1.id
        pos = 0
        context = codeforline.contestofwordsdata(sent_id)
        return render(request, 'annotatorapp/presentdata.html', context)


def select_wordoptionview(request, sent_id, wordoption_id):
    wo = WordOptions.objects.get(id=wordoption_id)
    wo.isSelected = True
    request.session['sent_id'] = sent_id
    wo.save()
    return redirect('annotatorapp:presentdataview')


# for eliminating the conflicting segments
def eliminate_wordoptionview(request, sent_id, wordoption_id):
    wo = WordOptions.objects.get(id=wordoption_id)
    wo.isEliminated = True
    wo.save()
    request.session['sent_id'] = sent_id
    return redirect('annotatorapp:presentdataview')


# for resetting every selected segment back to the initial position
def reset_allselectionview(request, sent_id):
    # collecting required values
    Sentence1 = Sentences.objects.get(id=sent_id)
    wordsdata = WordOptions.objects.all().filter(sentence=Sentence1)
    # iterating through the collected values and initializing them
    for wo in wordsdata:
        wo.isSelected = False
        wo.isEliminated = False
        wo.parent = -1
        wo.relation = ''
        wo.children = ''
        wo.save()
    request.session['sent_id'] = sent_id
    return redirect('annotatorapp:presentdataview')


# rendering response for saving details of each data segment(flowchart data) clicked by user
def save_data_to_db(request):
    if request.is_ajax():
        if request.method == 'POST':
            # load the data to be saved into model
            it = json.loads(request.POST['it'])
            et = json.loads(request.POST['et'])
            cs = json.loads(request.POST['cs'])
            ss = json.loads(request.POST['ss'])
            user = User(savedSentence=ss, clickSequence=cs, init_time=it, end_time=et)
            user.save()
            return HttpResponse('Success')
    else:
        raise Http404

#used to retrieve autocomplete noun/verbs/indeclinables options
def get_form_data(request):
    if request.is_ajax():
        if request.method == 'POST':
            table_id = json.loads(request.POST['table_id'])
            if table_id == 'noun':
                data = Noun.objects.values_list('sh');
            elif table_id == 'verb':
                data = Verbs.objects.values_list('sh');
            elif table_id == 'ind':
                data = Indeclinables.objects.values_list('sh');
            return HttpResponse(data)
    else:
        raise Http404



