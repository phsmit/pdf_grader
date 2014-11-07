from argparse import ArgumentParser
from collections import OrderedDict
from configparser import ConfigParser
from email import message_from_bytes
from email.header import decode_header
from email.utils import parseaddr
from sys import stderr
from os import makedirs
from imaplib import IMAP4_SSL
from os.path import exists, expanduser, join
import re


def mail_settings(filename=expanduser("~/.config/mail.conf")):
    c = ConfigParser()
    try:
        with open(filename, encoding='utf-8') as fp:
            c.read_file(fp)
    except IOError as e:
        print(e.strerror, file=stderr)
        exit("""Please provide a configuration file ~/.config/mail.conf with
the following contents:

[credentials]
user=
password=
serverimap=
serversmtp=
name=
email=
 """)
    return c['credentials']


def print_imap_labels(settings):
    mail_conn = IMAP4_SSL(settings['serverimap'])
    mail_conn.login(settings['user'], settings['password'])
    mail_conn.select()

    typ, data = mail_conn.list()
    for label in data:
        print(label.decode().split()[-1].strip('"'), file=stderr)


def download_files(imap_label, pdf_directory, file_regex, settings):
    if type(file_regex) == str:
        file_regex = re.compile(file_regex)

    mail_conn = IMAP4_SSL(settings['serverimap'])
    mail_conn.login(settings['user'], settings['password'])
    mail_conn.select(imap_label)
    typ, data = mail_conn.search(None, 'ALL')
    for num in data[0].split():
        typ, data = mail_conn.fetch(num, '(RFC822)')
        message = message_from_bytes(data[0][1])

        if message.is_multipart():
            for part in message.get_payload():
                if part.get_content_type() == 'application/pdf':
                    fn = part.get_filename().lower()
                    m = file_regex.match(fn)
                    if not m:
                        print("Invalid filename for pdf in message from {}".format(message['From']))
                        break

                    if exists(join(pdf_directory, fn)):
                        break

                    print("Saving {}".format(fn))
                    with open(join(pdf_directory, fn), 'wb') as pdf_file:
                        pdf_file.write(part.get_payload(decode=True))
                    yield m.group(1), message['From']
                    break
            else:
                print("Message from {} had no valid pdf attachment".format(message['From']))

    mail_conn.logout()


if __name__ == "__main__":
    parser = ArgumentParser(description='Download pdf files from email server')
    parser.add_argument("imap_label", default=None, nargs='?',
                        help='Imap label to download pdfs from. If not given, '
                             'this script will print all labels')
    parser.add_argument("pdf_directory", default=None, nargs='?',
                        help='directory to put pdfs in. Defaults to last '
                             'part of imap label (split by /)')
    parser.add_argument("file_regex", default=None, nargs='?',
                        help='regex to validate filename and extract student '
                             'number. If not given, the regex '
                             '${last_part_imap_label}_([0-9A-Za-z]+).pdf$ is used')
    parser.add_argument("email_dict", default="email_list", nargs='?',
                        help="Filename to store student-number/email/name "
                             "pairs in. If exists, will be updated")
    args = parser.parse_args()

    imap_label = args.imap_label


    settings = mail_settings()

    if imap_label is None:
        print_imap_labels(settings)
        exit("Provide the imap label to download the assignments from. "
             "Preferably it ends in the assignment name, e.g. "
             "INBOX/exercises/ex1")

    pdf_directory = (args.pdf_directory if args.pdf_directory is not None
                     else imap_label.split('/')[-1])

    file_regex = (args.file_regex if args.file_regex is not None
                  else "{}_([0-9A-Za-z]+).pdf$".format(imap_label.split('/')[-1]))

    if not exists(pdf_directory):
        makedirs(pdf_directory)

    email_dict = OrderedDict()
    if exists(args.email_dict):
        for line in open(args.email_dict):
            student_number, email, name = line.strip().split(None,2)
            email_dict[student_number] = (email, name)

    for student_number, email in download_files(imap_label, pdf_directory, file_regex, settings):
        name, email_address = parseaddr(email)
        name, encoding = decode_header(name)[0]
        if encoding is not None:
            name = name.decode(encoding)
        print("{} {} {}".format(student_number, email_address, name))
        email_dict[student_number] = (email_address, name)

    with open(args.email_dict, 'w') as dict_file:
        for student_number, data in email_dict.items():
            print("{} {} {}".format(student_number, data[0], data[1]),
                  file=dict_file)
