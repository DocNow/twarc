#!/usr/bin/env python

"""
A sample JSON to CSV program. Multivalued JSON properties are space delimited 
CSV columns. If you'd like it adjusted send a pull request!
"""

from twarc import json2csv

import os
import sys
import json
import codecs
import argparse
import fileinput

if sys.version_info[0] < 3:
    try:
        import unicodecsv as csv
    except ImportError:
        sys.exit("unicodecsv is required for python 2")
else:
    import csv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', help='write output to file instead of stdout')
    parser.add_argument('--split', '-s', help='if writing to file, split into multiple files with this many lines per '
                                              'file', type=int, default=0)
    parser.add_argument('--extra-field', '-e', help='extra fields to include. Provide a field name and a pointer to '
                                                    'the field. Example: -e verified user.verified',
                        nargs=2, action='append')
    parser.add_argument('--excel', '-x', help='create file compatible with Excel', action='store_true')
    parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
    args = parser.parse_args()

    file_count = 1
    csv_file = None
    if args.output:
        if args.split:
            csv_file = codecs.open(numbered_filepath(args.output, file_count), 'wb', 'utf-8')
            file_count += 1
        else:
            csv_file = codecs.open(args.output, 'wb', 'utf-8')
    else:
        csv_file = sys.stdout
    sheet = csv.writer(csv_file)

    extra_headings = []
    extra_fields = []
    if args.extra_field:
        for heading, field in args.extra_field:
            extra_headings.append(heading)
            extra_fields.append(field)

    sheet.writerow(get_headings(extra_headings=extra_headings))

    files = args.files if len(args.files) > 0 else ('-',)
    for count, line in enumerate(fileinput.input(files, openhook=fileinput.hook_encoded("utf-8"))):
        if args.split and count and count % args.split == 0:
            csv_file.close()
            csv_file = codecs.open(numbered_filepath(args.output, file_count), 'wb', 'utf-8')
            sheet = csv.writer(csv_file)
            sheet.writerow(get_headings(extra_headings=extra_headings))
            file_count += 1
        tweet = json.loads(line)
        sheet.writerow(get_row(tweet, extra_fields=extra_fields, excel=args.excel))


def numbered_filepath(filepath, num):
    path, ext = os.path.splitext(filepath)
    return os.path.join('{}-{:0>3}{}'.format(path, num, ext))


def get_headings(extra_headings=None):
    fields = json2csv.get_headings()
    if extra_headings:
        fields.extend(extra_headings)
    return fields


def get_row(t, extra_fields=None, excel=False):
    row = json2csv.get_row(t, excel=excel)
    if extra_fields:
        for field in extra_fields:
            row.append(extra_field(t, field))
    return row


def extra_field(t, field_str):
    obj = t
    for field in field_str.split('.'):
        if field in obj:
            obj = obj[field]
        else:
            return None
    return obj


if __name__ == "__main__":
    main()
