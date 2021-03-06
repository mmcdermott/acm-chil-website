# pylint: disable=global-statement,redefined-outer-name
import argparse
import csv
import glob
import json
import os

import yaml
from flask import Flask, jsonify, redirect, render_template, send_from_directory
from flask_frozen import Freezer
from flaskext.markdown import Markdown

site_data = {}
by_uid = {}


def main(site_data_path):
    global site_data, extra_files
    extra_files = ["index.md"]
    # Load all for your sitedata one time.
    for f in glob.glob(site_data_path + "/*"):
        extra_files.append(f)
        name, typ = f.split("/")[-1].split(".")
        if typ == "json":
            site_data[name] = json.load(open(f))
        elif typ in {"csv", "tsv"}:
            site_data[name] = list(csv.DictReader(open(f)))
        elif typ == "yml":
            site_data[name] = yaml.load(open(f).read(), Loader=yaml.SafeLoader)

    for typ in ["papers", "speakers", "tutorials", "workshops", "dss"]:
        by_uid[typ] = {}
        for p in site_data[typ]:
            by_uid[typ][p["UID"]] = p

    print("Data Successfully Loaded")
    return extra_files


# ------------- SERVER CODE -------------------->

app = Flask(__name__)
app.config.from_object(__name__)
freezer = Freezer(app)
markdown = Markdown(app)

# MAIN PAGES


def _data():
    data = {}
    data["config"] = site_data["config"]
    return data


@app.route("/")
def index():
    return redirect("/index.html")


# REDIRECTS TO SUPPORT EARLIER LINKS

@app.route("/agenda")
def agenda():
    return redirect("/calendar.html", code=302)


@app.route("/toc")
def toc():
    return redirect("/papers.html", code=302)


@app.route("/keynote")
def keynote():
    return redirect("/calendar.html", code=302)


@app.route("/registration")
def registration():
    return redirect("/register.html", code=302)


@app.route("/acm-chil-track-1-cfp")
def track1():
    return redirect("/call_papers.html", code=302)


@app.route("/acm-chil-track-2-cfp")
def track2():
    return redirect("/call_papers.html", code=302)


@app.route("/acm-chil-track-3-cfp")
def track3():
    return redirect("/call_papers.html", code=302)


@app.route("/acm-chil-track-4-cfp")
def track4():
    return redirect("/call_papers.html", code=302)


@app.route("/call-for-tutorials")
def call_tutorials():
    return redirect("/call_papers.html", code=302)


@app.route("/doctoral-consortium-call-for-phd-students")
def call_doctoral():
    return redirect("/call_papers.html", code=302)


@app.route("/financial-support")
def financial_support():
    return redirect("/register.html#tab-support", code=302)


@app.route("/acm-chil-2020-sponsorship-policy")
def sponsorship_policy():
    return redirect("/sponsor.html", code=302)


@app.route("/organizing-committees")
def organizing_committee():
    return redirect("/committee.html", code=302)


@app.route("/reviewers")
def reviewers():
    return redirect("/committee.html#tab-reviewers", code=302)


@app.route("/faqs")
def faqs():
    return redirect("/about.html", code=302)


# TOP LEVEL PAGES


@app.route("/index.html")
def home():
    data = _data()
    data["index"] = open("index.md").read()
    return render_template("index.html", **data)


@app.route("/about.html")
def about():
    data = _data()
    data["FAQ"] = site_data["faq"]["FAQ"]
    return render_template("about.html", **data)


@app.route("/papers.html")
def papers():
    data = _data()
    data["papers"] = site_data["papers"]
    return render_template("papers.html", **data)


@app.route("/committee.html")
def committee():
    data = _data()
    data["committee"] = site_data["committee"]["committee"]
    return render_template("committee.html", **data)


@app.route("/sponsor.html")
def sponsor():
    data = _data()
    return render_template("sponsor.html", **data)


@app.route("/register.html")
def register():
    data = _data()
    return render_template("register.html", **data)


@app.route("/call_papers.html")
def callpapers():
    data = _data()
    return render_template("callpapers.html", **data)


@app.route("/paper_vis.html")
def paper_vis():
    data = _data()
    return render_template("papers_vis.html", **data)


@app.route("/calendar.html")
def schedule():
    data = _data()
    # Hacky hardcoding of days
    data["thu"] = {
        "speakers": [x for x in site_data['speakers'] if x['day'] == 'thu'],
        "schedule": site_data['daytoview']['thursday'],
        "highlighted": [
            format_paper(by_uid["papers"][h["UID"]]) for h in site_data["highlighted"]
        ],
    }
    data["fri"] = {
        "speakers": [x for x in site_data['speakers'] if x['day'] == 'fri'],
        "schedule": site_data['daytoview']['friday'],
        "highlighted": [
            format_paper(by_uid["papers"][h["UID"]]) for h in site_data["highlighted"]
        ],
    }
    data["speakers"] = [x for x in site_data['speakers']]
    data["workshops"] = [
        format_workshop(workshop) for workshop in site_data["workshops"]
    ]
    data["tutorials"] = [
        format_workshop(tutorial) for tutorial in site_data["tutorials"]
    ]
    data["dss"] = [
        format_workshop(ds) for ds in site_data["dss"]
    ]
    data["preview"] = site_data["preview"]
    return render_template("schedule.html", **data)


# @app.route("/workshops.html")
# def workshops():
#     data = _data()
#     data["workshops"] = [
#         format_workshop(workshop) for workshop in site_data["workshops"]
#     ]
#     return render_template("workshops.html", **data)


def extract_list_field(v, key):
    value = v.get(key, "")
    if isinstance(value, list):
        return value
    else:
        return value.split("|")


def format_paper(v):
    list_keys = ["authors", "keywords", "session"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["UID"],
        "forum": v["UID"],
        "content": {
            "title": v["title"],
            "authors": list_fields["authors"],
            "keywords": list_fields["keywords"],
            "abstract": v["abstract"],
            "TLDR": v["abstract"],
            "recs": [],
            "session": list_fields["session"],
            "pdf_url": v.get("pdf_url", ""),
            "acm_pdf_url": v.get("acm_pdf_url", ""),
            "acm_html_url": v.get("acm_html_url", ""),
        },
    }


def format_workshop(v):
    list_keys = ["authors"]
    list_fields = {}
    for key in list_keys:
        list_fields[key] = extract_list_field(v, key)

    return {
        "id": v["UID"],
        "title": v["title"],
        "organizers": list_fields["authors"],
        "abstract": v["abstract"],
    }


# ITEM PAGES


@app.route("/poster_<poster>.html")
def poster(poster):
    uid = poster
    v = by_uid["papers"][uid]
    data = _data()
    data["paper"] = format_paper(v)
    return render_template("poster.html", **data)


@app.route("/speaker_<speaker>.html")
def speaker(speaker):
    uid = speaker
    v = by_uid["speakers"][uid]
    data = _data()
    data["speaker"] = v
    return render_template("speaker.html", **data)


@app.route("/workshop_<workshop>.html")
def workshop(workshop):
    uid = workshop
    v = by_uid["workshops"][uid]
    data = _data()
    data["workshop"] = format_workshop(v)
    return render_template("workshop.html", **data)

@app.route("/tutorial_<tutorial>.html")
def tutorial(tutorial):
    uid = tutorial
    v = by_uid["tutorials"][uid]
    data = _data()
    data["tutorial"] = format_workshop(v)
    return render_template("tutorial.html", **data)

@app.route("/ds_<ds>.html")
def ds(ds):
    uid = ds
    v = by_uid["dss"][uid]
    data = _data()
    data["ds"] = format_workshop(v)
    return render_template("ds.html", **data)

@app.route("/chat.html")
def chat():
    data = _data()
    return render_template("chat.html", **data)


# FRONT END SERVING


@app.route("/papers.json")
def paper_json():
    json = []
    for v in site_data["papers"]:
        json.append(format_paper(v))
    return jsonify(json)


@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


@app.route("/serve_<path>.json")
def serve(path):
    return jsonify(site_data[path])


# --------------- DRIVER CODE -------------------------->
# Code to turn it all static


@freezer.register_generator
def generator():

    for paper in site_data["papers"]:
        yield "poster", {"poster": str(paper["UID"])}
    for speaker in site_data["speakers"]:
        yield "speaker", {"speaker": str(speaker["UID"])}
    for workshop in site_data["workshops"]:
        yield "workshop", {"workshop": str(workshop["UID"])}
    for tutorial in site_data["tutorials"]:
        yield "tutorial", {"tutorial": str(tutorial["UID"])}
    for ds in site_data["dss"]:
        yield "ds", {"ds": str(ds["UID"])}

    for key in site_data:
        yield "serve", {"path": key}


def parse_arguments():
    parser = argparse.ArgumentParser(description="MiniConf Portal Command Line")

    parser.add_argument(
        "--build",
        action="store_true",
        default=False,
        help="Convert the site to static assets",
    )

    parser.add_argument(
        "-b",
        action="store_true",
        default=False,
        dest="build",
        help="Convert the site to static assets",
    )

    parser.add_argument("path", help="Pass the JSON data path and run the server")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse_arguments()

    site_data_path = args.path
    extra_files = main(site_data_path)

    if args.build:
        freezer.freeze()
    else:
        debug_val = False
        if os.getenv("FLASK_DEBUG") == "True":
            debug_val = True

        app.run(port=5000, debug=debug_val, extra_files=extra_files)
