from flask import Flask, render_template, Markup, abort
import datetime
import os
import yaml
import markdown
import settings

app = Flask(__name__)

def format_datetime(dt, format):
    """Format a datetime object for display"""
    return dt.strftime(format)

def get_page(directory, file):
    """Load and parse a page from the filesystem. Returns the page, or None if not found"""
    path = os.path.abspath(os.path.join(directory, str(file)))
    try:
        file_contents = open("%s/%s" % (directory, file)).read()
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
    meeting = get_page(settings.MEETINGS_DIR, path)
    if meeting is not None:
        meeting['date'] = datetime.datetime.strptime(path, '%Y-%m-%d')
    return meeting

def get_meetings():
    """Return a list of all meetings"""
    files = os.listdir(settings.MEETINGS_DIR)
    return filter(lambda meeting: meeting is not None, [get_meeting(file) for file in files])

@app.route('/')
def index():
    meeting_list = get_meetings()
    return render_template('homepage.html',
        meeting_list=meeting_list
    )

@app.route('/meetings/<date>')
def meeting(date):
    meeting = get_meeting(date)
    if meeting is None:
        abort(404)
    return render_template('meeting.html', meeting=meeting)

@app.route('/pages/<path>')
def page(path):
    page = get_page(settings.PAGES_DIR, path)
    if page is None:
        abort(404)
    return render_template('page.html', page=page)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# Add jinja filters
app.jinja_env.filters['datetimeformat'] = format_datetime

if __name__ == '__main__':
    app.run(debug=settings.DEBUG)
