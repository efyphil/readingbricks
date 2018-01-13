"""
This is the script that launches Flask app.

@author: Nikolay Lysenko
"""


import os
import sqlite3
from functools import reduce

from flask import Flask, render_template, url_for
from flask_misaka import Misaka, markdown
from markupsafe import Markup


app = Flask(__name__)
markdown_preprocessor = Misaka()
markdown_preprocessor.init_app(app)


@app.route('/')
def index() -> str:
    """
    Render home page.
    """
    lines_in_html = ['<h2>На данный момент доступны следующие метки:</h2>\n']
    rel_path_to_tags = '../../supplementary/counts_of_tags.tsv'
    abs_path_to_tags = os.path.dirname(__file__) + '/' + rel_path_to_tags
    tags_with_counts = []
    with open(abs_path_to_tags, 'r') as source_file:
        for line in source_file:
            tags_with_counts.append(line.split('\t'))
    home_url = url_for('index', _external=True)
    link_names = [tag.capitalize().replace('_', ' ') +
                  ' (число заметок: {})'.format(count.strip())
                  for (tag, count) in tags_with_counts]
    links_to_tags = [
        f'<p><a href={home_url}tags/{tag}>{name}</a></p>\n'
        for (tag, counts), name in zip(tags_with_counts, link_names)
    ]
    lines_in_html.extend(links_to_tags)
    content_in_html = Markup(''.join(lines_in_html))
    title = "Главная"
    content_with_css = render_template('regular_page.html', **locals())
    content_with_css = content_with_css.replace('</p>\n\n<ul>', '</p>\n<ul>')
    return content_with_css


def convert_note_from_markdown_to_html(note_title: str) -> Markup:
    """
    Convert note stored as a Markdown file into string with HTML.
    """
    rel_requested_path = f'markdown_notes/{note_title}.md'
    abs_requested_path = os.path.dirname(__file__) + '/' + rel_requested_path
    if not os.path.isfile(abs_requested_path):
        return page_not_found(note_title)
    with open(abs_requested_path, 'r') as source_file:
        content_in_markdown = ''.join(source_file.read())
    content_in_html = markdown_preprocessor.render(
        content_in_markdown,
        math=True, math_explicit=True, no_intra_emphasis=True
    )
    return content_in_html


@app.route('/notes/<note_title>')
def page_with_note(note_title: str) -> str:
    """
    Render in HTML a page with exactly one note.
    """
    content_in_html = convert_note_from_markdown_to_html(note_title)
    title = note_title
    content_with_css = render_template('regular_page.html', **locals())
    content_with_css = content_with_css.replace('</p>\n\n<ul>', '</p>\n<ul>')
    return content_with_css


@app.route('/tags/<tag>')
def page_for_tag(tag: str) -> str:
    """
    Render in HTML a page with all notes that have the specified tag.
    """
    relative_path_to_db = 'tag_to_notes.db'
    absolute_path_to_db = os.path.dirname(__file__) + '/' + relative_path_to_db
    try:
        conn = sqlite3.connect(absolute_path_to_db)
        cur = conn.cursor()
        cur.execute(f"SELECT note_title FROM {tag}")
        query_result = cur.fetchall()
        note_titles = [x[0] for x in query_result]
    except sqlite3.OperationalError:
        return page_not_found(tag)
    notes_content = []
    for note_title in note_titles:
        notes_content.append(convert_note_from_markdown_to_html(note_title))
    content_in_html = reduce(lambda x, y: x + y, notes_content)
    title = tag.capitalize().replace('_', ' ')
    content_with_css = render_template('regular_page.html', **locals())
    content_with_css = content_with_css.replace('</p>\n\n<ul>', '</p>\n<ul>')
    return content_with_css


@app.errorhandler(404)
def page_not_found(_) -> str:
    return render_template('404.html'), 404


app.run(debug=True)
