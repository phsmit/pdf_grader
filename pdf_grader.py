from argparse import ArgumentParser
from os import listdir
from collections import OrderedDict
from bottle import Bottle, run, static_file, debug, request
import re

debug(True)

grader = Bottle()
pdf_directory = None

email_dict = {}

general_data = {}
student_data = {}

grading_data_file = None


def find_valid_students(pdf_directory, pdf_regex):
    if type(pdf_regex) == str:
        pdf_regex = re.compile(pdf_regex)
        for pdf in listdir(pdf_directory):
            m = pdf_regex.match(pdf)
            if m:
                yield m.group(1)


def write_data(general, students, filename):
    with open(filename, 'w') as f:
        print(general['Title'], file=f)
        print(",".join(general['Questions']), file=f)
        print(",".join(str(i) if i is not None else "" for i in general['MaxPoints']), file=f)

        for student, data in students.items():
            print("Student:{}:{}".format(student, data['EmailSent']), file=f)
            for k,v in data.items():
                if k.startswith("EmailSent"):
                    continue
                print("{}:{}:{}".format(k,str(v[0]) if v[0] is not None else "", v[1].replace("\r\n",r"\n")),file=f)


def read_data(filename):
    with open(filename) as f:
        general = OrderedDict()
        general['Title'] = f.readline().strip()
        general['Questions'] = f.readline().strip().split(',')
        general['MaxPoints'] = [int(i) if len(i) > 0 else None for i in f.readline().strip().split(',')]

        students = OrderedDict()
        student_data = OrderedDict()
        student_id = None
        for line in f:
            if len(line.strip()) < 1:
                continue
            if line.startswith("Student:"):
                if student_id is not None:
                    students[student_id] = student_data
                    student_data = OrderedDict()
                _, student_id, sent = line.split(':')
                student_data['EmailSent'] = bool(sent)
            else:
                question, points, description = line.split(':')
                student_data[question] = (int(points) if len(points) > 0 else None, description.replace(r"\n", "\r\n"))

    return general, students

@grader.route('/')
def indexpage():
    return static_file('index.html', root='./static')

@grader.get('/student/<studentid>')
def getstudentdata(studentid):
    if studentid not in student_data:
        student_data[studentid] = OrderedDict({'EmailSent': False})

    return student_data[studentid]

@grader.post('/student/<studentid>')
def poststudentdata(studentid):
    if studentid not in student_data:
        student_data[studentid] = OrderedDict({'EmailSent': False})

    for key in general_data['Questions']:
        points = request.forms.get('{}_points'.format(key), '').strip()
        desc = request.forms.get('{}_desc'.format(key), '').strip()

        if len(points) > 0 or len(desc):
            try:
                points = float(points)
            except ValueError:
                points = None
            student_data[studentid][key] = (points, desc)

@grader.route('/info')
def getinfo():
    return general_data
    # return [general_data, student_data]

@grader.route('/pdf/<filename>')
def pdfpage(filename):
    return static_file(filename, root=pdf_directory)

@grader.route('/save')
def save():
    write_data(general_data, student_data, grading_data_file)

if __name__ == "__main__":
    parser = ArgumentParser(description='Start grading session')
    parser.add_argument("grading_data_file")
    parser.add_argument("pdf_directory")
    parser.add_argument("student_email_list")
    parser.add_argument("pdf_regex", default=None, nargs='?')

    args = parser.parse_args()

    pdf_directory = args.pdf_directory
    # email_dict = read_student_email_list(args.student_email_list)
    general_data, student_data = read_data(args.grading_data_file)
    grading_data_file = args.grading_data_file

    pdf_regex = (args.pdf_regex if args.pdf_regex is not None else "{}_([0-9A-Za-z]+).pdf$".format(pdf_directory))

    general_data['StudentList'] = list(find_valid_students(pdf_directory, pdf_regex))

    run(grader, host="0.0.0.0", port=8080)