import sys
from argparse import ArgumentParser
import csv
import datetime
from html import escape
from pdf_grader import read_data


def create_description_grade(general, student):
    tot_points = 0

    message = ""

    for i, question in enumerate(general['Questions']):
        if question not in student:
            continue
        points = student[question][0]
        description = student[question][1]
        max_points = general['MaxPoints'][i]

        if max_points is not None:
            message += "<h5>{}: {}/{} points</h5>".format(question, points, max_points)
            if len(description.strip()) > 0:
                message += "<p>"
                message += "<br />".join(escape(description.strip()).splitlines())
                message += "</p>"
        else:
            if points is not None or len(description.strip()) > 0:
                if points is None:
                    message += "<h5>{}</h5>".format(question)
                else:
                    message += "<h5>{}: {}</h5>".format(question, points)
                if len(description.strip()) > 0:
                    message += "<p>"
                    message += "<br />".join(escape(description.strip()).splitlines())
                    message += "</p>"

        if points is not None:
            tot_points += points

    return tot_points,message


def main(grad_file, grade_workbook):
    general, students = read_data(grad_file)

    new_grade_workbook = "{}.{}".format(grade_workbook, datetime.datetime.now().isoformat())

    with open(new_grade_workbook, 'w', newline='') as csv_out:
        grade_writer = csv.writer(csv_out)
        with open(grade_workbook, newline='') as csv_in:
            grade_reader = csv.reader(csv_in)
            for row in grade_reader:
                if not " " in row[0] or row[0].split(" ", 1)[1] not in students:
                    grade_writer.writerow(row)
                    if " " in row[0]:
                        print("{} in workbook not found in students".format(row[0].split(" ", 1)[1]), file=sys.stderr)
                else:
                    grade,feedback = create_description_grade(general, students[row[0].split(" ", 1)[1]])
                    row[5] = grade
                    row[11] = feedback
                    grade_writer.writerow(row)


if __name__ == "__main__":
    parser = ArgumentParser(description='Fill grading workbook')
    parser.add_argument("grading_data_file")
    parser.add_argument("grading_workbook")

    args = parser.parse_args()

    main(args.grading_data_file, args.grading_workbook)