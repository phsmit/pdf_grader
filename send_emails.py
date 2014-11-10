from argparse import ArgumentParser
from email.mime.text import MIMEText
import getpass
from time import sleep
from random import randint
from smtplib import SMTP_SSL, SMTP
import textwrap
from download import mail_settings
from pdf_grader import read_data, write_data


def get_connection(settings, user, password):
    s = SMTP(settings['serversmtp'])
    s.starttls()
    s.login(user, password)
    return s

def create_message_body(general, data, studentid):
    tot_points = 0
    tot_max_points = 0
    message = "{} - Results\r\nStudent id: {}\r\n\r\n".format(general['Title'], studentid)

    for i, question in enumerate(general['Questions']):
        if question not in data:
            continue
        points = data[question][0]
        description = data[question][1]
        max_points = general['MaxPoints'][i]

        if max_points is not None:
            message += "{}: {}/{} points\r\n".format(question, points, max_points)
            for lines in description.splitlines():
                message += "\r\n".join("   "+s for s in textwrap.wrap(lines, 70) ) + "\r\n"
            message += "\r\n"
        else:
            if points is not None or len(description) > 0:
                if points is None:
                    message += "{}:\r\n".format(question)
                else:
                    message += "{}: {}\r\n".format(question, points)
                message += "\r\n".join("   "+s for s in textwrap.wrap(description, 70) )
                message += "\r\n"

        if points is not None:
            tot_points += points
        tot_max_points += max_points if max_points is not None else 0

    message += "\r\nTotal: {}/{} points".format(tot_points, tot_max_points)

    return message


def format_message(general, data, studentid, settings):
    mime_message = MIMEText(create_message_body(general, data, studentid), 'plain', 'iso-8859-1')
    mime_message['Subject'] = "{} - Results".format(general['Title'])
    mime_message['From'] = "{} <{}>".format(settings['name'], settings['email'])
    mime_message['To'] = data['EmailAddress']

    return mime_message


def send_message(email_from, emails_to, message, connection):
    connection.sendmail(email_from, emails_to, message.as_string())


def main(grading_file, email_file):
    general, students = read_data(grading_file)
    settings = mail_settings()

    user = input("Email username:")
    password = getpass.getpass()

    if password is None or len(password) < 4:
        print("Aborting, no password given")
        return

    for line in open(email_file):
        studentid, email, name = line.split(None, 2)
        students[studentid]['EmailAddress'] = email

    for studentid, data in students.items():
        # m = create_message_body(general, data, studentid)
        if data['EmailSent']:
            continue

        if not 'EmailAddress' in data:
            print("Email address missing for {}".format(studentid))
            continue

        message = format_message(general, data, studentid, settings)


        # If we are here we try to send the message
        try:
            connection = get_connection(settings, user, password)
            send_message(settings['email'], [settings['email'], data['EmailAddress']], message, connection)
            students[studentid]['EmailSent'] = True
            write_data(general, students, grading_file, ['EmailAddress'])
            print("Email sent to {}".format(studentid))
            connection.quit()
            sleep(randint(30,90))
        except Exception as e:
            print("Email for {} not sent: {}".format(studentid, e))



if __name__ == "__main__":
    parser = ArgumentParser(description='Send emails to all students that have '
                                        'not had an email yet and have data for '
                                        'all questions')
    parser.add_argument("grading_data_file")
    parser.add_argument("email_dict", default="email_list", nargs='?',
                        help="Filename with student-number/email/name "
                             "pairs")
    args = parser.parse_args()

    main(args.grading_data_file, args.email_dict)


