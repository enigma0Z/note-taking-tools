#!/usr/bin/env python3

import math
import re
import os
import sys
from datetime import datetime, timedelta
from typing import Text
from argparse import ArgumentParser

FIND_MAX = 14
TODO_START = '<!-- [TODO_START] -->'
TODO_END = '<!-- [TODO_END] -->'

TODO_ITEM_RE = re.compile(
    r'^(?P<indent> *)(?P<bullet>\* )?(?P<checkbox>\[.\])? *(?P<text>.*)$')

INDENT_STR = '  '
INDENT_LEN = len(INDENT_STR)

REPORT_FILE_STRFTIME="daily/%Y/%m/%d/daily.md"
REPORT_FORMAT = '''
# {date}

## TODO

{start}

{todo}

{end}

---
'''.strip()


class FindException(Exception):
    pass


class TodoException(Exception):
    pass


class BulletItem:
    def __init__(self, indent, text):
        self.indent = indent
        self.text = text
        self.sub_items = []

    def add_sub_item(self, point):
        self.sub_items.append(point)

    def get_sub_item_lines(self):
        return [str(item) for item in self.sub_items]

    def __str__(self):
        lines = [
            "{indent}* {text}".format(
                indent=self.indent*'  ',
                text=self.text
            )
        ]

        lines.extend(self.get_sub_item_lines())

        return '\n'.join(lines)

    def __repr__(self):
        return self.__str__()


class TodoItem(BulletItem):
    def __init__(self, indent, text, completed):
        super().__init__(indent, text)
        self.completed = completed

    def get_checkbox(self):
        if self.completed:
            return '[X]'
        else:
            return '[ ]'

    def __str__(self):
        lines = [
            "{indent}* {checkbox} {text}".format(
                indent=self.indent*INDENT_STR,
                checkbox=self.get_checkbox(),
                text=self.text
            )
        ]

        lines.extend(self.get_sub_item_lines())

        return '\n'.join(lines)


def get_previous_todo():
    """
    Get the todo section from the given markdown file
    """

    todo_lines = []
    in_todo = False

    try:
        filename = find_previous()
        with open(filename, 'r') as daily_file:
            for line in daily_file:
                line = line[0:-1]
                if line.strip() == TODO_START:
                    in_todo = True
                    continue

                if line.strip() == TODO_END:
                    in_todo = False
                    continue

                if in_todo and line != '':
                    todo_lines.append(line)

    except FindException:
        pass

    return todo_lines


def parse_todo(lines):
    todo_items = []
    for line in lines:
        match = re.match(TODO_ITEM_RE, line)
        if(match):
            # print(match.groups())
            if match.group('bullet'):
                item = None
                if (match.group('checkbox')):
                    item = TodoItem(
                        indent=math.floor(
                            len(match.group('indent')) / INDENT_LEN),
                        text=match.group('text'),
                        completed=match.group('checkbox') != '[ ]'
                    )
                else:
                    item = BulletItem(
                        indent=math.floor(
                            len(match.group('indent')) / INDENT_LEN),
                        text=match.group('text')
                    )

                if todo_items != [] and item.indent == todo_items[-1].indent +1:
                    todo_items[-1].add_sub_item(item)
                else:
                    todo_items.append(item)
            else:
                indent = math.floor(len(match.group('indent')) / INDENT_LEN)
                if todo_items != [] and indent > todo_items[-1].indent:
                    todo_items[-1].text += ' ' + match.group('text')

    return todo_items


def get_next_todo(todo_items):
    """
    Print a todo section out
    """

    return '\n'.join([
        str(item) for item in todo_items
        if isinstance(item, TodoItem) and not item.completed
    ])


def find_previous():
    """
    Find the previous daily file up to a max number of days to look back on
    """
    today = datetime.now()
    for i in range(1, FIND_MAX):
        day_check = (today - timedelta(days=i)
                     ).strftime(REPORT_FILE_STRFTIME)
        if os.path.exists(day_check):
            return day_check
    else:
        raise FindException('Could not find a previous daily file')

def get_daily_report():
    return REPORT_FORMAT.format(
        date=datetime.now().strftime('%B %e, %Y'),
        start=TODO_START,
        todo=get_next_todo(parse_todo(get_previous_todo())),
        end=TODO_END
    )

if __name__ == '__main__':

    parser = ArgumentParser()

    parser.add_argument(
        '-w', '--write-file',
        action='store_true'
    )

    parser.add_argument(
        '-b', '--base-dir',
    )

    opts = parser.parse_args(sys.argv[1:])

    if opts.base_dir: REPORT_FILE_STRFTIME = os.path.join(opts.base_dir, REPORT_FILE_STRFTIME)

    if opts.write_file:
        report_dir, report_file = os.path.split(datetime.now().strftime(REPORT_FILE_STRFTIME))
        if (not os.path.exists(os.path.join(report_dir, report_file))):
            if (not os.path.exists(report_dir)): os.makedirs(report_dir)

            with open(os.path.join(report_dir, report_file), 'w') as output_file:
                output_file.write(get_daily_report())

        else:
            print('Daily file for today has already been generated', file=sys.stderr)
            sys.exit(1)
    else:
        print(get_daily_report())
