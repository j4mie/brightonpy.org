import os
import yaml
import logging
import datetime
import markdown
from urllib.parse import urljoin
from datetime import timedelta
from werkzeug import secure_filename
from werkzeug.contrib.atom import AtomFeed
from flask import Flask, render_template, Markup, abort, redirect, url_for, request

app = Flask(__name__)
app.config.from_pyfile('settings.py')


logger = logging.getLogger(__name__)

cache = {}


def get_page(directory, file):
    """Load and parse a page from the filesystem. Returns the page, or None if not found"""
    filename = secure_filename(file)

    if filename in cache:
        return cache[filename]

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), directory, filename))
    try:
        file_contents = open(path, encoding='utf-8').read()
    except:
        logger.exception("Failed to open file at path: %s", path)
        return None
    data, text = file_contents.split('---\n', 1)
    page = yaml.load(data)
    page['content'] = Markup(markdown.markdown(text))
    page['path'] = file

    cache[filename] = page
    return page


def get_meeting(path):
    """Get a meeting from the filesystem"""
    meeting = get_page(app.config['MEETINGS_DIR'], path)
    if meeting is not None:
        meeting = meeting.copy()
        meeting['datetime'] = datetime.datetime.strptime(meeting['datetime'], '%Y-%m-%d %H:%M')
    return meeting


def get_meetings():
    """Return a list of all meetings"""

    if 'meeting_list' in cache:
        return cache['meeting_list']

    files = os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), app.config['MEETINGS_DIR'])))
    meetings = filter(lambda meeting: meeting is not None, [get_meeting(file) for file in files])
    result = sorted(meetings, key=lambda item: item['datetime'])

    cache['meeting_list'] = result
    return result


def past_meetings():
    meeting_list = get_meetings()
    now = datetime.datetime.now()
    return [meeting for meeting in meeting_list if meeting['datetime'] < now]


def future_meetings():
    meeting_list = get_meetings()
    now = datetime.datetime.now()
    return [meeting for meeting in meeting_list if meeting['datetime'] > now]


@app.route('/')
def index():
    return render_template('homepage.html', future_meeting_list=future_meetings())


@app.route('/archive/')
def archive():
    """Legacy URL"""
    return redirect(url_for('meetings'))


@app.route('/meetings/')
def meetings():
    return render_template(
        'meetings.html',
        past_meeting_list=reversed(past_meetings()),
        future_meeting_list=future_meetings()
    )


@app.route('/meetings/<date>/')
def meeting(date):
    meeting = get_meeting(date)
    if meeting is None:
        abort(404)
    return render_template('meeting.html', meeting=meeting)


@app.route('/pages/<path>/')
def page(path):
    page = get_page(app.config['PAGES_DIR'], path)
    if page is None:
        abort(404)
    return render_template('page.html', page=page)


@app.route('/meetings.atom')
def feed():
    feed = AtomFeed('BrightonPy Events', feed_url=request.url, url=request.url_root)
    for meeting in reversed(get_meetings()):
        # A little hack
        date = meeting['datetime'] - timedelta(weeks=1)
        feed.add(
            meeting['title'],
            meeting['content'],
            author=meeting['speaker'],
            url=urljoin(request.url_root, url_for('meeting', date=meeting['path'])),
            updated=date,
            published=date
        )
    return feed.get_response()


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# Add jinja filters
@app.template_filter('datetimeformat')
def format_datetime(datetime_object, format):
    """Format a datetime object for display, used in Jinja2 templates"""
    return datetime_object.strftime(format)


@app.before_request
def redirect_from_epio():
    """Redirect www to naked domain"""
    if "www" in request.host:
        return redirect('http://brightonpy.org' + request.path, 301)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
