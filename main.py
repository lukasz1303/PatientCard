from math import floor, log10

from fhirpy import SyncFHIRClient
from tkinter import *
import threading

HAPI_BASE_URL = "http://localhost:8080/baseR4"

client = SyncFHIRClient(HAPI_BASE_URL)

medicationRequests = client.resources("MedicationRequest")
patients_list = []

app = Tk()

frame = Frame(app)
frame.place(x=100, y=50)  # Position of where you would place your listbox

Lb = Listbox(frame, height=20, width=50)
Lb.pack(side="left", fill='y')

scrollbar = Scrollbar(frame, orient="vertical", command=Lb.yview)
scrollbar.config(command=Lb.yview)
scrollbar.pack(side="right", fill=Y)
Lb.config(yscrollcommand=scrollbar.set)


def load_patients():
    patients = client.resources("Patient")

    patients = patients.elements('name', 'gender', "birthDate", "id").fetch_all()
    for i in patients:
        name = ''.join([i for i in i['name'][0]['given'][0] if not i.isdigit()])
        surname = ''.join([i for i in i['name'][0]['family'] if not i.isdigit()])
        patients_dict = {'name': name,
                         'surname': surname,
                         'gender': i['gender'],
                         'birthDate': i['birthDate'],
                         'id': i['id']}
        patients_list.append(patients_dict)


def filter_patients_by_name(name):
    Lb.delete(0, 'end')
    for i in range(len(patients_list)):
        if name.lower() in (patients_list[i]['name'] + ' ' + patients_list[i]['surname']).lower():
            Lb.insert(i, patients_list[i]['name'] + ' ' + patients_list[i]['surname'] + ' ' + patients_list[i][
                'birthDate'] + ' ' * 100 + patients_list[i]['id'])


def get_observations(subject):
    observations = client.resources("Observation")
    subject = 'Patient/' + subject
    observation = observations.elements('subject', 'code', 'valueQuantity', 'effectiveDateTime').search(
        subject=subject).fetch_all()

    observation_list = []
    for i in observation:
        if 'valueQuantity' in i.keys():
            observation_dict = {'subject': i['subject'],
                                'display': i['code']['coding'][0]['display'],
                                'value': round(i['valueQuantity']['value'], -int(floor(log10(abs(i['valueQuantity']['value']))))+3),
                                'unit': i['valueQuantity']['unit'],
                                'effectiveDateTime': i['effectiveDateTime']}
        else:
            observation_dict = {'subject': i['subject'],
                                'display': i['code']['coding'][0]['display'],
                                'effectiveDateTime': i['effectiveDateTime']}
        observation_list.append(observation_dict)

    return observation_list


def get_medicationRequest(subject):
    subject = 'Patient/' + subject
    medicationRequest = medicationRequests.elements('medicationCodeableConcept', 'subject', 'authoredOn').search(
        subject=subject).fetch_all()

    medicationRequest_list = []
    for i in medicationRequest:
        medicationRequest_dict = {'medicationCodeableConcept': i['medicationCodeableConcept']['coding'][0]['display'],
                                  'authoredOn': i['authoredOn']}
        medicationRequest_list.append(medicationRequest_dict)

    return medicationRequest_list


def filterByDate(obs, med, Lb_obs, Lb_meds, s_day, s_month, s_year, e_day, e_month, e_year):
    Lb_obs.delete(0, 'end')
    Lb_meds.delete(0, 'end')
    prev = ''
    counter = 0
    s_date = (int(s_year), int(s_month), int(s_day))
    e_date = (int(e_year), int(e_month), int(e_day))
    for i in range(len(obs)):
        date = (int(obs[i]['effectiveDateTime'][:4]), int(obs[i]['effectiveDateTime'][5:7]),
                int(obs[i]['effectiveDateTime'][8:10]))
        if s_date <= date <= e_date:
            if obs[i]['effectiveDateTime'] != prev:
                date = obs[i]['effectiveDateTime'].replace('T', ' ')
                date = date[:-6]
                Lb_obs.insert(counter, date)
                counter += 1
                line = '    ' + obs[i]['display']
            else:
                line = '    ' + obs[i]['display']
            if 'value' in obs[i].keys():
                line += ': ' + str(obs[i]['value'])
            if 'unit' in obs[i].keys():
                if str(obs[i]['unit']) != '{score}':
                    line += ' ' + str(obs[i]['unit'])
            Lb_obs.insert(counter, line)
            counter += 1
            prev = obs[i]['effectiveDateTime']

    counter = 0
    for i in range(len(med)):
        date = (int(med[i]['authoredOn'][:4]), int(med[i]['authoredOn'][5:7]), int(med[i]['authoredOn'][8:10]))
        if s_date <= date <= e_date:
            if med[i]['authoredOn'] != prev:
                date = med[i]['authoredOn'].replace('T', ' ')
                date = date[:-6]
                Lb_meds.insert(counter, date)
                counter += 1
                line = '    ' + med[i]['medicationCodeableConcept']
            else:
                line = '    ' + med[i]['medicationCodeableConcept']
            Lb_meds.insert(counter, line)
            counter += 1
            prev = med[i]['authoredOn']


def showAll(obs, med, Lb_obs, Lb_meds):
    Lb_obs.delete(0, 'end')
    Lb_meds.delete(0, 'end')
    prev = ''
    counter = 0
    for i in range(len(obs)):

        if obs[i]['effectiveDateTime'] != prev:
            date = obs[i]['effectiveDateTime'].replace('T', ' ')
            date = date[:-6]
            Lb_obs.insert(counter, date)
            counter += 1
            line = '    ' + obs[i]['display']
        else:
            line = '    ' + obs[i]['display']
        if 'value' in obs[i].keys():
            line += ': ' + str(obs[i]['value'])
        if 'unit' in obs[i].keys():
            if str(obs[i]['unit']) != '{score}':
                line += ' ' + str(obs[i]['unit'])
        Lb_obs.insert(counter, line)
        counter += 1
        prev = obs[i]['effectiveDateTime']

    counter = 0
    for i in range(len(med)):
        if med[i]['authoredOn'] != prev:
            date = med[i]['authoredOn'].replace('T', ' ')
            date = date[:-6]
            Lb_meds.insert(counter, date)
            counter += 1
            line = '    ' + med[i]['medicationCodeableConcept']
        else:
            line = '    ' + med[i]['medicationCodeableConcept']
        Lb_meds.insert(counter, line)
        counter += 1
        prev = med[i]['authoredOn']


def show(e):
    global i
    lb_info = Lb.get(Lb.curselection())
    lb_data0 = lb_info.split(' ' * 100)
    lb_data = lb_data0[0].split(' ')
    lb_name = lb_data[0] + ' ' + lb_data[1]
    lb_id = lb_data0[1]

    card = Toplevel()
    card.grab_set()
    card.resizable(False, False)
    card.geometry("1000x600")
    card.title(lb_name)

    filter_label = Label(card, text="Filter by date", font=('serif', 9))
    filter_label.place(x=670, y=10)

    to_label = Label(card, text="----", font=('serif', 9))
    to_label.place(x=700, y=35)

    observations_label = Label(card, text="Observations: ", font=('serif', 9))
    observations_label.place(x=20, y=100)

    medications_label = Label(card, text="Medications: ", font=('serif', 9))
    medications_label.place(x=20, y=350)

    days = range(1, 32)
    choose_day = StringVar(card)
    choose_day.set(1)
    days_list = OptionMenu(card, choose_day, *days)
    days_list.config(width=3)
    days_list.place(x=500, y=30)

    months = range(1, 13)
    choose_month = StringVar(card)
    choose_month.set(1)
    months_list = OptionMenu(card, choose_month, *months)
    months_list.config(width=3)
    months_list.place(x=560, y=30)

    years = range(2022, 1899,-1)
    choose_year = StringVar(card)
    choose_year.set(1980)
    years_list = OptionMenu(card, choose_year, *years)
    years_list.config(width=3)
    years_list.place(x=620, y=30)

    choose_day2 = StringVar(card)
    choose_day2.set(1)
    days_list2 = OptionMenu(card, choose_day2, *days)
    days_list2.config(width=3)
    days_list2.place(x=740, y=30)

    choose_month2 = StringVar(card)
    choose_month2.set(1)
    months_list2 = OptionMenu(card, choose_month2, *months)
    months_list2.config(width=3)
    months_list2.place(x=800, y=30)

    choose_year2 = StringVar(card)
    choose_year2.set(2021)
    years_list2 = OptionMenu(card, choose_year2, *years)
    years_list2.config(width=3)
    years_list2.place(x=860, y=30)

    patient = {}
    for i in range(len(patients_list)):
        if lb_id == patients_list[i]['id']:
            patient = patients_list[i]
            break

    frame = Frame(card)
    frame.place(x=20, y=120)  # Position of where you would place your listbox

    Lb_obs = Listbox(frame, height=13, width=150)
    Lb_obs.pack(side="left", fill='y')

    scrollbar = Scrollbar(frame, orient="vertical", command=Lb_obs.yview)
    scrollbar.config(command=Lb_obs.yview)
    scrollbar.pack(side="right", fill=Y)
    Lb_obs.config(yscrollcommand=scrollbar.set)

    frame2 = Frame(card)
    frame2.place(x=20, y=370)  # Position of where you would place your listbox

    Lb_meds = Listbox(frame2, height=13, width=150)
    Lb_meds.pack(side="left", fill='y')

    scrollbar2 = Scrollbar(frame2, orient="vertical", command=Lb_meds.yview)
    scrollbar2.config(command=Lb_meds.yview)
    scrollbar2.pack(side="right", fill=Y)
    Lb_meds.config(yscrollcommand=scrollbar2.set)

    obs = get_observations(patients_list[i]['id'])
    med = get_medicationRequest(patients_list[i]['id'])
    prev = ''
    counter = 0
    for i in range(len(obs)):
        if obs[i]['effectiveDateTime'] != prev:
            date = obs[i]['effectiveDateTime'].replace('T', ' ')
            date = date[:-6]
            Lb_obs.insert(counter, date)
            counter += 1
            line = '    ' + obs[i]['display']
        else:
            line = '    ' + obs[i]['display']
        if 'value' in obs[i].keys():
            line += ': ' + str(obs[i]['value'])
        if 'unit' in obs[i].keys():
            if str(obs[i]['unit']) != '{score}':
                line += ' ' + str(obs[i]['unit'])
        Lb_obs.insert(counter, line)
        counter += 1
        prev = obs[i]['effectiveDateTime']

    counter = 0
    for i in range(len(med)):
        if med[i]['authoredOn'] != prev:
            date = med[i]['authoredOn'].replace('T', ' ')
            date = date[:-6]
            Lb_meds.insert(counter, date)
            counter += 1
            line = '    ' + med[i]['medicationCodeableConcept']
        else:
            line = '    ' + med[i]['medicationCodeableConcept']
        Lb_meds.insert(counter, line)
        counter += 1
        prev = med[i]['authoredOn']

    Name_label = Label(card, text="Name: ", font=('serif', 9))
    Name_label.place(x=20, y=10)
    Gender_label = Label(card, text="Gender: ", font=('serif', 9))
    Gender_label.place(x=20, y=30)
    Birth_date_label = Label(card, text="Birth date: ", font=('serif', 9))
    Birth_date_label.place(x=20, y=50)
    Id_label = Label(card, text="Id: ", font=('serif', 9))
    Id_label.place(x=20, y=70)

    Name_value = Label(card, text=lb_name, font=('serif', 9))
    Name_value.place(x=100, y=10)
    Gender_value = Label(card, text=patient['gender'], font=('serif', 9))
    Gender_value.place(x=100, y=30)
    Birth_date_value = Label(card, text=patient['birthDate'], font=('serif', 9))
    Birth_date_value.place(x=100, y=50)
    Id_value = Label(card, text=lb_id, font=('serif', 9))
    Id_value.place(x=100, y=70)

    Button(card, command=lambda: threading.Thread(
        target=lambda: filterByDate(obs, med, Lb_obs, Lb_meds, choose_day.get(), choose_month.get(), choose_year.get(),
                                    choose_day2.get(), choose_month2.get(), choose_year2.get())).start(), text="Filter",
           height=1, width=10).place(x=600, y=70)

    Button(card, command=lambda: threading.Thread(target=lambda: showAll(obs, med, Lb_obs, Lb_meds)).start(),
           text="Show all", height=1, width=10).place(x=740, y=70)


def sort_patients_list(sort):
    global patients_list
    if sort == 0:
        patients_list = sorted(patients_list, key=lambda k: k['name'])
    elif sort == 1:
        patients_list = sorted(patients_list, key=lambda k: k['surname'])
    else:
        patients_list = sorted(patients_list, key=lambda k: k['birthDate'])

    Lb.delete(0, 'end')
    for i in range(len(patients_list)):
        Lb.insert(i, patients_list[i]['name'] + ' ' + patients_list[i]['surname'] + ' ' + patients_list[i][
            'birthDate'] + ' ' * 100 + patients_list[i]['id'])


if __name__ == '__main__':

    load_patients()
    patients_list = sorted(patients_list, key=lambda k: k['name'])

    app.resizable(False, False)
    app.geometry("500x550")
    app.title("Patients cards")

    sorting = ["Name", 'Surname', 'Birth Date']
    choose = StringVar(app)
    choose.set(sorting[0])

    Label_card = Label(app, text="Patient cards", font=('serif', 16))
    Label_card.place(x=170, y=10)

    sort_list = OptionMenu(app, choose, *sorting)
    sort_list.config(width=12)
    sort_list.place(x=125, y=480)

    for i in range(len(patients_list)):
        Lb.insert(i, patients_list[i]['name'] + ' ' + patients_list[i]['surname'] + ' ' + patients_list[i][
            'birthDate'] + ' ' * 100 + patients_list[i]['id'])

    Name_label = Label(app, text="Filter by name:", font=('serif', 9))
    Name_label.place(x=150, y=380)

    name_entry = Entry(app, width=30)
    name_entry.insert(0, 'johnny')
    name_entry.place(x=150, y=400)

    Lb.bind('<Double-1>', show)

    Button(app, command=lambda: threading.Thread(target=lambda: filter_patients_by_name(name_entry.get())).start(),
           text="Filter", height=1, width=10).place(x=200, y=440)
    Button(app, command=lambda: sort_patients_list(sorting.index(choose.get())), text="Sort", height=1, width=10).place(
        x=260, y=481)

    app.mainloop()
