# Magnolia

Magnolia is a Django-based blogging engine

![Screenshot](https://raw.githubusercontent.com/iriscot/magnolia-blog/master/example.png)

# Features

- Rich-text post formatting using the block editor
- Posts tagging
- SEO-friendly URLs
- Searching of posts
- Drafts
- Featured posts
- RSS syndication
- Blog avatar and cover in the page header
- Social contacts
- Pagination

# Running 

Warning: the following guide is not suitable for production deployment.

0. Install python3 & pip.

1. Clone repo:
```
$ git clone https://github.com/iriscot/magnolia-blog 
$ cd magnolia-blog
```

2. Create and enter python environment:
```
$ python3 -m venv blog_env
$ source blog_env/bin/activate
```

3. Install dependencies:
```
$ python3 -m pip install requirements.txt
```

4. Set your database in `settings.py`.

5. Create & execute DB migrations:
```
$ python3 manage.py makemigrations blog
$ python3 manage.py migrate blog
```

6. Run the local server:
```
$ python3 ./manage.py runserver
```

7. Finally, point your browser to `127.0.0.1:8000` and enjoy :)

# Configuration

You can find config in `/Magnolia/settings.py`. Here are the keys of interest:
- `SECRET_KEY` - change this to random value when deploying to production;
- `DEBUG` - set to `False` on production;
- `ALLOWED_HOSTS` - add your production host;
- `DATABASES` - by default file-backed SQLite3 database is configured, change this to your own case;
- `LANGUAGE_CODE` - default locale;
- `TIME_ZONE` - default timezone;
- `POSTS_PER_PAGE` - posts displayed per page.

# Translation

Magnolia available on both English and Russian out of the box.
However, you can create your own translations.

Create translation files:
```
$ django-admin makemessages -l [YOUR_LOCALE_CODE]
$ django-admin makemessages -l [YOUR_LOCALE_CODE] -d djangojs
```
