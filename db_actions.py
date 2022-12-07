import sqlite3 as sl

db = 'unicorns.db'
csv = 'unicorns.csv'


def create_db(csv_filename):
    conn = sl.connect(db)
    cx = conn.cursor()

    columns = get_header(csv_filename)

    stmt_create_table = "CREATE TABLE IF NOT EXISTS unicorns(" + columns + ")"

    cx.execute(stmt_create_table)

    conn.commit()
    conn.close()


def store_data(csv_filename):
    conn = sl.connect(db)
    cx = conn.cursor()

    with open(csv_filename, 'r') as f:
        f.readline()  # consume header line

        lines = f.readlines()
        for line in lines:
            index = 0
            while True:  # handle removal of comma inside double quotes
                if "\"" in line[index:]:
                    iq = line[index:].index("\"") + index
                    iq_end = line[iq+1:].index("\"") + iq+1

                    if line[iq+1] == '[':
                        closing_bracket = line[index:].index("]") + index
                        index = closing_bracket + 1
                        break;

                    while "," in line[iq:iq_end+1]:
                        ic = line[iq:].index(",") + iq
                        line = line[:ic] + line[ic + 1:]
                        iq_end = line[iq+1:].index("\"") + iq+1

                    index = iq_end+1
                else:
                    break

            line = line.replace("\"", "")  # remove double quotes
            line = line.replace("'", "`")  # replace single quote with grave

            line = "'" + line

            index = 0
            while True:
                if "," in line[index:]:
                    ic = line[index:].index(",") + index
                    if "[" in line[index:] and line[index:].index("[") < ic-index:
                        index = line[index:].index("]") + index + 1
                        break;
                    line = line[:ic] + "','" + line[ic+1:]
                    index = ic + 2
                else:
                    break

            line = line[:-2]
            line += "'"

            stmt_insert_line = "INSERT OR IGNORE INTO unicorns VALUES(" + line + ")"
            cx.execute(stmt_insert_line)

    conn.commit()
    conn.close()


def get_header(csv_filename):
    with open(csv_filename, 'r') as f:
        header = f.readline().strip().split(',')

        for i in range(len(header)):
            header[i] = "\'" + header[i] + "\'"

        header = ", ".join(header)

    header = header[:header.rfind(',')]

    return header


def main():
    #  create_db(csv)
    #  store_data(csv)


if __name__ == '__main__':
    main()
