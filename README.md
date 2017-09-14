PDF Grader, a tool for grading pdf's
====================================

Setup
-----

Clone this repository

    git clone git@github.com:psmit/pdf_grader.git

Make a virtual environment and install bottle

    cd pdf_grader
    virtualenv -p python3 env_py3
    env_py3/bin/pip install bottle
    
Basic usage
-----------

Copy the skeleton file for the exercise to a grades file:

    cp ex1_skeleton ex1_grades

Download all submission from MyCourses (look for the button 'Download all submissions'). Unzip the resulting file in the directory `ex1`. After that, you can start the grading system by typing:

    env_py3/bin/python pdf_grader.py ex1_grades ex1

Now it will tell you the url where you can find the grader. Switching between students automatically saves the text you have written, or click manually save. For every action, there is a backup writting in the pdf_grader directory, you can see those with `ls -al`. The latest version is always in the normal file "ex1_grades".

When you are ready, you can e.g. write a summary of the points:

    env_py3/bin/python summary.py ex1_grades

And when you are really convinced you are ready you can download from MyCourses the "Grading worksheet" on the page Grading. You can fill it by running:

    env_py3/bin/python fill_grading_worksheet.py ex1_grades Grades.csv

After that you can upload filled grading worksheet to mycourses.


