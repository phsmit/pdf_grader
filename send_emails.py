from argparse import ArgumentParser
from email.mime.text import MIMEText
from smtplib import SMTP_SSL
from download import mail_settings
from pdf_grader import read_data, write_data


def get_connection(settings):
    s = SMTP_SSL(settings['serversmtp'])
    s.starttls()
    s.login(settings['user'], settings['password'])
    return s


def format_message(general, data, settings):
    mime_message = MIMEText('\n'.join(data['a']), 'plain', 'iso-8859-1')
    mime_message['Subject'] = "{} - Results".format(general['Title'])
    mime_message['From'] = "{} <{}>".format(settings['name'], settings['email'])
    mime_message['To'] = data['EmailAddress']

    return mime_message


def send_message(email_from, emails_to, message, connection):
    connection.sendmail(email_from, emails_to, message.as_string())


def main(grading_file, email_file):
    general, students = read_data(grading_file)
    settings = mail_settings()

    connection = get_connection(settings)

    for line in open(email_file):
        studentid, email, name = line.split(None, 2)
        students[studentid]['EmailAddress'] = email

    for studentid, data in students.items():
        if data['EmailSent']:
            continue
        if not 'EmailAddress' in data:
            print("Email address missing for {}".format(studentid))
            continue
        for question in general['Questions']:
            if question not in data or (len(data['{}_points'.format(question)]) == 0 and len(data['{}_desc'.format(question)]) == 0):
                print("Question not complete for {}".format(studentid))
                continue

        # If we are here we try to send the message
        message = format_message(general, data, settings)

        try:
            send_message(settings['email'], [settings['email'], data['EmailAddress']], message, connection)
            students[studentid]['EmailSent'] = True
            write_data(general, students, grading_file)
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


