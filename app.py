from flask import Flask, redirect, render_template, request, session, url_for
import os
import io
import random
import sqlite3 as sl
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = "unicorns.db"

app.secret_key = os.urandom(12)
app.debug = True

# our home page!
@app.route("/")
def home():
    filters = {
        "country": "Country",
        "city": "City",
        "industry": "Industry",
    }

    return render_template("home.html",
                           filters=filters,
                           )


# page we route to after requesting to view some data
@app.route("/unicorns/<filter_category>/<filter_selection>")
def filtered(filter_category, filter_selection):
    selections = {}
    if 'filter_selection' != 'None':
        selections = db_get_set_of(filter_category)

    save_figure(filter_category, filter_selection)

    return render_template("filtered.html", filter_category=filter_category, filter_selection=filter_selection,
                           project=False,
                           selections=selections,
                           image='None')


# on submit some filter category
@app.route("/submit_filter_category", methods=["POST"])
def submit_filter_category():
    session["filter_category"] = request.form["filter_category"]

    if 'filter_category' not in session or session["filter_category"] == "":
        return redirect(url_for("home"))

    return redirect(url_for("filtered", filter_category=session["filter_category"], filter_selection='None'))


# on submit some selection within category
@app.route("/submit_filter_selection", methods=["POST"])
def submit_filter_selection():
    session["filter_selection"] = request.form["filter_selection"]

    if 'filter_category' not in session or session["filter_category"] == "":
        return redirect(url_for("home"))

    if 'filter_selection' not in session or session["filter_selection"] == "":
        return redirect(url_for("home"))

    return redirect(url_for("filtered", filter_category=session["filter_category"],
                            filter_selection=session["filter_selection"]))


# save a matplotlib figure corresponding to the filter category and filter selection
@app.route("/fig/<filter_category>/<filter_selection>")
def save_figure(filter_category, filter_selection):
    fig = create_figure(filter_category, filter_selection)
    img = io.BytesIO()
    FigureCanvas(fig).print_png(img)
    fig.savefig("static/images/plot.png", format="png", dpi=400)
    return


# create the matplotlib figure with inputs
def create_figure(filter_category, filter_selection):
    df = db_create_dataframe(filter_category, filter_selection)
    df.sort_values(inplace=True, by='Year Joined')

    years_list = list(df["Year Joined"].unique())

    figure = Figure()
    ax = figure.add_subplot(1, 1, 1)

    filter_column_title = filter_category.capitalize()

    df_grouped_by_category = df.groupby(filter_column_title)

    if filter_selection == 'None':
        items = list(db_get_set_of(filter_column_title.lower()))
        colors = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                  for i in range(len(items))]

        i = 0
        for item in items:
            valuation_sum_by_year = [0.0 for x in range(0, len(years_list))]

            df_group_outer = df_grouped_by_category.get_group(item)
            df_grouped_by_year = df_group_outer.groupby("Year Joined")

            for year in years_list:
                groups = df_grouped_by_year.groups
                if year in groups:
                    df_group = df_grouped_by_year.get_group(year)
                    series = pd.to_numeric(df_group["Last Valuation (Billion $)"])
                    valuation_sum = series.sum()
                else:
                    valuation_sum = 0.0

                valuation_sum = float(valuation_sum)
                year_index = years_list.index(year)
                if year_index > 0:
                    valuation_sum_by_year[year_index] = float(valuation_sum) + float(
                        valuation_sum_by_year[year_index - 1])
                    valuation_sum_by_year[year_index] = float(valuation_sum_by_year[year_index])
                else:
                    valuation_sum_by_year[year_index] = float(valuation_sum)
                    valuation_sum_by_year[year_index] = float(valuation_sum_by_year[year_index])

            ax.plot(years_list, valuation_sum_by_year, color=colors[i], label=item, linewidth=0.4)
            i += 1

        ax.set(xlabel="Year", ylabel="Total Valuation of " + filter_category + "-Based Startups ($ Billions)")
    else:
        valuation_sum_by_year = [0.0 for x in range(0, len(years_list))]

        df_group_outer = df_grouped_by_category.get_group(filter_selection)
        df_grouped_by_year = df_group_outer.groupby("Year Joined")

        colors = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
                  for i in range(1)]
        color = colors[0]

        for year in years_list:
            groups = df_grouped_by_year.groups

            if year in groups:
                df_group = df_grouped_by_year.get_group(year)
                series = pd.to_numeric(df_group["Last Valuation (Billion $)"])
                valuation_sum = series.sum()
            else:
                valuation_sum = 0.0

            valuation_sum = float(valuation_sum)
            year_index = years_list.index(year)
            if year_index > 0:
                valuation_sum_by_year[year_index] = float(valuation_sum) + float(valuation_sum_by_year[year_index - 1])
                valuation_sum_by_year[year_index] = float(valuation_sum_by_year[year_index])
            else:
                valuation_sum_by_year[year_index] = float(valuation_sum)
                valuation_sum_by_year[year_index] = float(valuation_sum_by_year[year_index])

        ax.plot(years_list, valuation_sum_by_year, color=color, label=filter_selection)
        ax.set(xlabel="Year", ylabel="Total Valuation of " + filter_selection + "-Based Startups ($ Billions)")

    ax.legend(fontsize=5)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.FontSize = 5;
    return figure


# create a dataframe corresponding to the database
def db_create_dataframe(filter_category, filter_selection):
    conn = sl.connect(db)
    df = pd.read_sql_query("SELECT * FROM unicorns", conn)
    conn.close()
    pd.to_numeric(df["Last Valuation (Billion $)"])
    return df


# get the set of unique values in our database that are in some column
def db_get_set_of(column: str):
    column = column.lower()
    columns = db_get_column_titles()
    col_index = get_column_index(columns, column)

    conn = sl.connect(db)
    cx = conn.cursor()

    stmt = "SELECT * from unicorns"
    data = cx.execute(stmt)

    res_list = []
    for record in data:
        res_list.append(record[col_index])

    res_set = set(res_list)  # note the double round-brackets

    conn.close()
    return res_set


# get the index of a column in the array columns
def get_column_index(columns, column_name):
    if column_name in columns:
        return columns.index(column_name)
    return 0


# get the titles of columns in our database for querying
def db_get_column_titles():
    conn = sl.connect(db)
    cx = conn.cursor()

    column_stmt = "pragma table_info(unicorns)"
    column_data = cx.execute(column_stmt)
    header = []
    for col in column_data:
        header.append(col[1].lower())

    conn.close()
    return header


@app.route('/<path:path>')
def catch_all(path):
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.secret_key = os.urandom(12)
    app.debug = True
    app.run()
