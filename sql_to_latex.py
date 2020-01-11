#!/usr/bin/env python3.7
import re
import sys

schema_name = "mydb"


class Table():
    def __init__(self, name):
        self.name = name
        self.name_escaped = name.replace('_', R"\_")
        self.pk = name + "_ID"
        self.fields = []

    def add_field(self, field):
        self.fields.append(field)

    def __repr__(self):
        return f"name: {self.name}, attrs: {self.fields}\n"


class Attribute():
    def __init__(self, name, null, a_type):
        self.name = name
        self.name_escaped = name.replace('_', R"\_")
        self.null = null
        self.a_type = a_type
        self.fks = []

    def __repr__(self):
        return f"name: {self.name}, nullable: {self.null}, {self.a_type}"


def extract_tables(file_contents):
    regex = re.compile(
        fr'(?<=EXISTS `{schema_name}`.)`(.*)` \(([\S\s]*?)(?=\n  PRIMARY KEY)[\S\s]*?(CONSTRAINT|[\S\s]*?;)')

    return re.finditer(regex, file_contents)


def extract_foreign_keys(constraints):
    regex = re.compile(r'FOREIGN KEY \(`(.*)\)')
    return re.finditer(regex, constraints)


def extract_attributes(lines):
    regex = re.compile(r'`(.*)`\ (.*?)\ (.*),')
    return re.finditer(regex, lines)


def read_file(path):
    with open(path, "r") as file:
        return file.read()


def wrap_in_code(string):
    return R"\code{" + string + "}"


def create_primary_key_comment(table):
    return f"""Tabeli \\code{{{table.name_escaped}}} Primary Key. Surrogaatvõti, mis omistatakse uue kirje lisamisel võttes senise maksimaalse ID väärtuse tabelis \\code{{{table.name_escaped}}} ja liites sellel ühe. See on peidetud võti, mida ei näidata kasutajale kunagi. """


def create_foreign_key_comment(table, fk_name):
    return f"Välisvõti, mis seob tabeli \\code{{{table.name_escaped}}} tabeliga \\code{{{fk_name}}}."


def create_latex_table(table):
    top = R"\begin{table}[H]"
    caption_label = f"\\caption{{Tabel: \\code{{{table.name_escaped}}}}}\n\\label{{tab:{table.name}}}"
    header = R"""
\begin{tabularx}{\textwidth}{|l|l|l|X|}
\hline
\textbf{Veeru nimi} & \textbf{Tüüp} & \textbf{NULL?} & \textbf{Semantika} \\ \hline"""

    rows = []
    for field in table.fields:
        row = []
        row.append(wrap_in_code(field.name_escaped))
        row.append(wrap_in_code(field.a_type))
        row.append(wrap_in_code(field.null))
        if f"{table.name.upper()}_ID" in field.name:
            row.append(create_primary_key_comment(table))
        elif "_ID" in field.name:
            row.append(create_foreign_key_comment(table, field.name_escaped))
        else:
            row.append("semantika siia")

        row = ' & '.join(row) + R"\\ \hline"
        rows.append(row)

    end = R"""
\end{tabularx}
\end{table}
    """

    result = top + '\n' + caption_label + '\n' + \
        header + '\n' + '\n'.join(rows) + end
    return result


if __name__ == "__main__":
    filepath = "./script.sql"
    if len(sys.argv) > 2:
        filepath = sys.argv[1]

    file_contents = read_file(filepath)
    tables = []

    for match in extract_tables(file_contents):
        table_name = match.group(1)
        attribute_lines = match.group(2)
        constraints = match.group(3)
        table = Table(table_name)

        attributes = extract_attributes(attribute_lines)
        for attribute in attributes:
            a_name = attribute.group(1)
            a_type = attribute.group(2)
            a_null = attribute.group(3).replace("AUTO_INCREMENT", "").strip()
            attr = Attribute(a_name, a_null, a_type)
            table.add_field(attr)
        tables.append(table)

    latex_tables = []
    for table in tables:
        latex_tables.append(create_latex_table(table))

    for latex_table in latex_tables:
        print(latex_table)
