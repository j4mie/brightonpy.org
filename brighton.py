from flask import Flask, render_template, Markup, abort
import datetime
import os
import yaml
import markdown

app = Flask(__name__)
app.config.from_pyfile('settings.py')

def format_datetime(datetime_object, format):
    """Format a datetime object for display, used in Jinja2 templates"""
    return datetime_object.strftime(format)

def get_page(directory, file):
    """Load and parse a page from the filesystem. Returns the page, or None if not found"""
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), directory, str(file)))
    try:
        file_contents = open(path).read()
        file_contents = unicode(file_contents, 'utf-8')
    except:
        return None
    data, text = file_contents.split('---\n', 1)
    page = yaml.load(data)
    page['content'] = Markup(markdown.markdown(text))
    page['path'] = file
    return page

def get_meeting(path):
    """Get a meeting from the filesystem"""
    meeting = get_page(app.config['MEETINGS_DIR'], path)
    if meeting is not None:
        meeting['datetime'] = datetime.datetime.strptime(meeting['datetime'], '%Y-%m-%d %H:%M')
    return meeting

def get_meetings():
    """Return a list of all meetings"""
    files = os.listdir(os.path.abspath(os.path.join(os.path.dirname(__file__), app.config['MEETINGS_DIR'])))
    meetings = filter(lambda meeting: meeting is not None, [get_meeting(file) for file in files])
    return sorted(meetings, key=lambda item: item['datetime'])

@app.route('/')
def index():
    meeting_list = get_meetings()
    now = datetime.datetime.now()
    future_meetings = [meeting for meeting in meeting_list if meeting['datetime'] > now]
    return render_template('homepage.html', future_meeting_list=future_meetings)

@app.route('/archive/')
def archive():
    meeting_list = get_meetings()
    now = datetime.datetime.now()
    past_meetings = [meeting for meeting in meeting_list if meeting['datetime'] < now]
    return render_template('archive.html', past_meeting_list=past_meetings)

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

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# Add jinja filters
app.jinja_env.filters['datetimeformat'] = format_datetime

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
