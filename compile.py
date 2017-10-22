#!/usr/bin/env python

import argparse
import csv
import os
import json

import pandas as pd


"""  Available columns:

[u'Ability to design', u'Apply knowledge', u'Clear learning goals',
    u'Course ID', u'Course Name', u'Dept', u'Effective Communication',
    u'Enrollment', u'Ethical responsibility',
    u'Explain course requirements', u'Explains subject matter',
    u'Function on Teams', u'Global, etc. contexts', u'Hrs Per Week',
    u'Importance of subject', u'Instructor',
    u'Instructor provides Feedback to students',
    u'Interest in student learning', u'Knowledge Contemporary Issues',
    u'Life-long learning', u'Overall course', u'Overall teaching',
    u'Proj Instr 1. Motivation', u'Proj Instr 2. Guidance',
    u'Proj Instr 3. Knows next steps',
    u'Proj Instr 4. Instructor availability',
    u'Proj Instr 5. Overall Lead Effectiveness',
    u'Project 1. Draw on Skills', u'Project 2. Develop skills',
    u'Project 3. Demand on Time and Attn',
    u'Project 4. External Review Committee helpfulness',
    u'Project 5. Faculty Mgmt Satisfaction',
    u'Project 6. Group Worked Smoothly',
    u'Project 7. Effective learning experience', u'Project 8. Project Size',
    u'Project 9. General Rating', u'Realistic Constraints', u'Resp. Rate %',
    u'Responses', u'Section', u'Semester', u'Show respect for students',
    u'Solve Problems', u'Use skills', u'Year']
"""


def clean_column_name(colname):
    colname = colname.strip()
    return colname.rsplit(":", 1)[-1].strip(" 0123456789\t\n").lower()


def parse_evals_file(fname):
    """ Parse evaluations for a single college"""
    reader = csv.reader(open(fname))
    columns = []

    for row in reader:
        if row[0] == "Semester":  # parse column names
            columns = [clean_column_name(c) for c in row]
        elif not row[0]:  # year stats
            pass
        else:
            yield {c: row[i].strip() for i, c in enumerate(columns) if c}


def parse_evals_dir(dirname):
    for fname in os.listdir(dirname):
        if fname.endswith(".csv"):
            for record in parse_evals_file(os.path.join(dirname, fname)):
                yield record


def get_evals_json(src_data_dir):
    df = pd.DataFrame(
        parse_evals_dir(src_data_dir),
        columns=["course id", 'course name', 'dept', 'year', 'semester',
                 'section', 'instructor', 'hrs per week', 'responses']
    ).rename(columns={'course name': 'name', 'hrs per week': 'hrs'})
    df['responses'] = df['responses'].astype(int)
    df = df[pd.notnull(df['hrs']) & (df['hrs'] != "") & (df['responses'] > 10)]
    # clean up course name: "10701", "10-701", "F14-10-701"
    df['course id'] = df['course id'].map(
        lambda s: "".join(c for c in s if c.isdigit())[-5:])
    semesters = {'Spring': '-01', 'Summer': '-06', 'Fall': '-09'}
    df['date'] = df.apply(
        lambda row: row['year'] + semesters[row['semester']], axis=1)
    df['hrs'] = df['hrs'].astype(float)
    return df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Compile CSV exported from FCE into a machihne-readable "
                    "format")
    parser.add_argument('-s', '--source-dir', default="src", nargs="?",
                        help='Directory with exported files')
    parser.add_argument('-o', '--output', default="docs/fce.json", nargs="?",
                        type=argparse.FileType('w'),
                        help='Filename to export JSON data to')
    args = parser.parse_args()

    if not os.path.isdir(args.source_dir):
        parser.exit(1, "Provided source path is not a directory")

    df = get_evals_json(args.source_dir)
    hrs = df[
        ['course id', 'name', 'year', 'instructor', 'hrs', 'date']].sort_values(
        'date', ascending=False).groupby('course id').first()
    hrs.to_json(args.output, orient='index', double_precision=2)