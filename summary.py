from argparse import ArgumentParser
from pdf_grader import read_data

__author__ = 'psmit'


def average(points):
    averages = []

    for i in range(len(points[0])):
        t = 0
        c = 0
        for j in range(len(points)):
            if points[j][i] is not "":
                t += float(points[j][i])
                c += 1

        averages.append("{:.2f}".format(t/c if c > 0 else 0.0))
    return averages


def main(grading_file):
    general, students = read_data(grading_file)

    print("Student\t{}\tTotal".format("\t".join(general['Questions'])))

    total_points = []

    for studentid, data in sorted(students.items()):
        total_point = 0
        points = []
        for question in general['Questions']:
            if question not in data:
                points.append("")
                continue
            point = data[question][0]
            if point is None:
                points.append("")
            else:
                points.append("{}".format(point))
                total_point += point
        points.append("{}".format(total_point))

        total_points.append(points)

        print("{}\t{}".format(studentid,"\t".join(points)))

    print()

    av_points = average(total_points)
    print("Avg.  \t{}".format("\t".join(av_points)))




if __name__ == "__main__":
    parser = ArgumentParser(description='Create summary')
    parser.add_argument("grading_data_file")
    args = parser.parse_args()

    main(args.grading_data_file)

