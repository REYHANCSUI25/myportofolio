Name : Reyhan

NPM : 2506637086

Class : PBP KKI

Portfolio repo for PBP KKI, Odd Semester 2026/2027

## Overview

A personal portfolio website built with Django as the individual project of Platform-Based Programming (CSGE602022), Fasilkom UI. The portfolio section is **Education**: a page that lists, searches, adds, edits, stars and deletes entries without reloading, backed by a Django REST Framework API at `/api/v1/education/`. Four roles (visitor, regular user, Editor, owner) decide what each person can change. The same API also serves my Flutter app, [MyPortfolio Mobile](https://github.com/REYHANCSUI25/myportofolio_mobile), which logs in with a token.

Live site: https://muhammad-reyhan53-myportofolio.pws.cs.ui.ac.id

Built with Django 5.2, Django REST Framework 3.18, django-cors-headers, SQLite locally and PostgreSQL on PWS, WhiteNoise for static files, and plain JavaScript (Fetch API and the Popover API) on the page.

## Setup

1. `git clone https://github.com/REYHANCSUI25/myportofolio.git` then `cd myportofolio`
2. `python -m venv env`
3. Windows PowerShell: `env\Scripts\activate` (macOS/Linux: `source env/bin/activate`)
4. `pip install -r requirements.txt`
5. `python manage.py migrate`
6. `python manage.py createsuperuser` (this account becomes the portfolio owner)
7. `python manage.py runserver` and open http://127.0.0.1:8000/
8. Run the tests with `python manage.py test main`

No `.env` file is needed locally; the project defaults to SQLite when `PRODUCTION` is not set to `True`.

### Creating the Editor role (one-time, via Django Admin)

1. Log in as the superuser and open `/admin/`.
2. Authentication and Authorization > Groups > Add group.
3. Name it exactly `Editor`.
4. Under "Chosen permissions" add only `main | education | Can change education`, then Save.
5. Authentication and Authorization > Users > open the user > add the `Editor` group > Save.

The group must be created once per database, so repeat these steps on the deployed site's admin.

## Roles and Permissions

| Action | Visitor | Regular user | Editor | Owner (superuser) |
| --- | --- | --- | --- | --- |
| Read the Education page and API | Yes | Yes | Yes | Yes |
| Give or remove a star | Log in first (API: 401) | Yes | Yes | Yes |
| Edit an entry (`PUT`/`PATCH`) | Log in first (API: 401) | 403 | Yes | Yes |
| Create an entry (`POST`) | Log in first (API: 401) | 403 | 403 | Yes |
| Delete an entry (`DELETE`) | Log in first (API: 401) | 403 | 403 | Yes |

One set of Django model permissions (`main.add_education`, `main.change_education`, `main.delete_education`) drives all three layers: the HTML views, the API's `IsPortfolioOwnerOrEditorOrReadOnly` permission class, and the buttons the page draws. Superusers pass every permission check automatically, and the `Editor` group holds only `main.change_education`.

## REST API

Base path: `/api/v1/`. The API accepts two kinds of login, set as DRF's default authentication classes in `portofolio/settings.py`:

- **Token** (`TokenAuthentication`), for the mobile app: `POST /api/v1/auth/token/` with a username and password returns a token, and every later request sends it in the `Authorization: Token <token>` header. Token requests don't need a CSRF token, because a browser never attaches this header on its own.
- **Session** (`SessionAuthentication`), for the website: log in through the site or the browsable API's "Log in" link. Every request that changes data must send the `X-CSRFToken` header; the Education page reads the token from the `csrftoken` cookie.

Token authentication is listed first, so a request that isn't logged in at all, or that sends an invalid or revoked token, gets 401 with a `WWW-Authenticate: Token` header. A logged-in user whose role can't make a change still gets 403.

Outside production (`PRODUCTION` not set to `True`), `django-cors-headers` allows requests from any origin, so the Flutter app running in Chrome on its own `localhost` port can call the API, and `10.0.2.2` is added to `ALLOWED_HOSTS`, because that's the address the Android emulator uses to reach the computer running `runserver`. On PWS neither applies: no cross-origin requests are allowed, since the Android app doesn't need them.

| Method | Endpoint | Allowed for | Success | Notes |
| --- | --- | --- | --- | --- |
| `POST` | `/api/v1/auth/token/` | Everyone | 200 | Body `{"username": "...", "password": "..."}`; returns `{"token": "..."}`, or 400 for wrong credentials |
| `POST` | `/api/v1/auth/logout/` | Any logged-in user | 204 | Deletes the token sent in the `Authorization` header |
| `GET` | `/api/v1/education/` | Everyone | 200 | `?institution=` filters by institution (case-insensitive, partial match) |
| `POST` | `/api/v1/education/` | Owner | 201 | Returns the created entry |
| `GET` | `/api/v1/education/<id>/` | Everyone | 200 | 404 if the entry doesn't exist |
| `PUT` | `/api/v1/education/<id>/` | Owner, Editor | 200 | Full update: every required field must be sent |
| `PATCH` | `/api/v1/education/<id>/` | Owner, Editor | 200 | Partial update: only the fields sent are changed |
| `DELETE` | `/api/v1/education/<id>/` | Owner | 204 | Empty body |
| `POST` | `/api/v1/education/<id>/star/` | Any logged-in user | 200 | Toggles your star and returns the entry |

Invalid input returns 400 with errors per field, requests that aren't logged in return 401, actions a role can't perform return 403, and missing entries return 404. For writes the role check runs first, so a role that can't make a change gets 401 or 403 whether or not the entry exists.

Example entry:

```json
{
    "id": "3f2c9a1e-5b7d-4c8e-9a2f-1d6b8e4c7a90",
    "institution": "Universitas Indonesia",
    "degree": "S1 Ilmu Komputer KKI",
    "description": "Third-semester student in Ilmu Komputer KKI UI.",
    "started_at": "2025-08-01",
    "ended_at": null,
    "is_ongoing": true,
    "star_count": 1,
    "is_starred": false
}
```

Validation rules, shared by the API serializer and the HTML form through `main/validators.py`:

- `institution`, `degree` and `description` can't be blank or made only of HTML tags; tags are stripped with `strip_tags` before saving.
- `ended_at` can't be before `started_at`. A `PATCH` checks the new date against the stored one, and skips the check when it changes no dates.
- `id`, `is_ongoing`, `star_count` and `is_starred` are read-only, and the API never exposes who starred an entry.

Two older endpoints are kept so earlier assignments keep working, but the page no longer uses them: `GET /api/education/` (the Tutorial 3–5 JSON) and `POST /education/add-ajax/` (Tutorial 5).

## Running the Tests

`python manage.py test main` runs 90 tests. `main/tests_api.py` covers the API for every role (rejected writes also check the database stayed unchanged), validation, CSRF with a real logged-in session, read-only fields, 404s, a query-count check, and token authentication: logging in, creating with a token and no CSRF token, 401 for missing, invalid and revoked tokens, logging out, the CORS headers, and requests from the Android emulator's host. `main/tests.py` covers the HTML views, the page's role flags, the form, stars and the login redirect.

## Weekly Progress

| Week | Work |
| --- | --- |
| Tutorial 0 and 1 | Project setup, views, templates, HTML5/CSS3, PWS deployment |
| Assignment 1 | Static portfolio page with semantic HTML |
| Assignment 2 | Education model, list view, base template inheritance |
| Assignment 3 | ModelForm create/update/delete, JSON endpoints, institution search |
| Assignment 4 | Editor role via Django Group, server-side 403/redirect enforcement, POST-only star toggle with counts, JSON leak fix, login redirect back to the requested page, custom 403 page |
| Assignment 5 | Education page loads via `fetch()` against a hand-built `JsonResponse`, debounced AJAX search, Popover add-education modal with a permission-checked AJAX create endpoint, toast notifications, XSS escaping plus server-side `strip_tags` cleaning, shared `static/js/ajax-utils.js` |
| Assignment 6 | Django REST Framework API for Education under `/api/v1/` (built in Tutorial 7), page switched to the API, edit modal that saves only the changed fields with `PATCH` for the Editor and owner, inline and toast error messages, end-date and HTML-only validation shared by the form and serializer, page script moved to `static/js/education.js`, 80 tests |
| Tutorial 10 | Token authentication for the mobile app (`rest_framework.authtoken`): token login and logout endpoints, `TokenAuthentication` as the first default authentication class with `SessionAuthentication` kept for the website, CORS for the Flutter app in Chrome and the Android emulator's `10.0.2.2` host allowed outside production, 10 more tests |

### Assignment 1

1. Yes, I used semantic HTML elements such as <section> and <article> to organize the website into clear parts. These elements helped structure the static web and made the HTML easier to understand and maintain. They also made it clearer which content belonged to which part of the portfolio.
2. The biggest problem I ran into was that some elements I sized for the desktop page did not fit properly when the screen became smaller. For example, I had containers with fixed widths, and on mobile they would extend past the edge of the screen and create horizontal scrolling. I also had to deal with my picture becoming too large compared to the text around them.
3. One limitation I noticed was that I could only show the portofolio information in a fixed way. For example, if I had several projects, users would have to scroll through all of them instead of being able to sort or filter them. In the next iteration, perhaps I could add a simple project filter or search feature so users could choose what type of project then want to see without having to go through everything.

I used ChatGPT to help me learn HTML syntax and understand how different HTML elements and CSS properties work. During the development process, I learned the difference between using class and id attributes, how HTML elements can be nested to structure a page, and how CSS selectors are used to style specific elements. It was also useful when I was unsure why something was not displaying or behaving the way I expected, since I could describe the problem and use the explanation to understand what I had done wrong.

ChatGPT was also used to assist in overcoming the following technical difficulties:

1. Git Bash wouldn't properly reflect changes I was making in VS Code or the local server.
2. Folder duplication caused by previous versions of the project from Assignment 1 made it difficult to tell which files I was actually working on.
3. I had problems with incorrect file paths and folder locations when linking HTML and image files. Some files worked locally while others showed as missing because the paths were pointing to the wrong folder.

### Assignment 2

1. When a user opens `/education/`, the browser sends a GET request. `portofolio/urls.py` is the project's main URL file. It sends everything to `main.urls` using `include()`. `main/urls.py` matches `education/` and sends the request to the `show_education` view. The view calls `Education.objects.all().order_by("-started_at")` to get all the education rows from the database. It puts that data into a context dictionary along with a `name` string. Then `render()` loads `templates/education.html` and fills it in with that context. The `{% for %}` loop prints each education entry, or shows the `{% empty %}` message if there are none. Django sends the finished HTML back to the browser.
2. If education entries were hardcoded in the template, adding or changing one would mean editing HTML by hand every time. That's slow and easy to get wrong. With a model, the data lives in the database instead. New entries are just new rows, added without touching the template or view code at all. This also keeps the code cleaner. Template changes only affect layout, and data changes only affect the database.
3. `makemigrations` looks at the current models and writes a migration file describing what changed. It does not touch the database yet. `migrate` then applies that migration to the actual database, creating or changing tables to match. For example, adding the `Education` model needed `makemigrations` to create `0002_education.py`, then `migrate` to actually build that table so `Education.objects.create(...)` has somewhere to save data.

ChatGPT and Google's AI Overview was used for me to learn the following:
1. Learning how .order_by() controls the order in which records are returned was relevant to displaying the most recent education entry first instead of relying on the database's default ordering.
2. Learning hoow .filter(...).update(...) can modify an existing row without deleting and recreating it was useful for correcting the description of a UI card after placegolder text had been left in it.
3. Learning about template inheritance through {% extends %} and {% block %} was relevant to the  base-template refactor, particularly for moving the navbar and footer into a shared template.
4. Learning that a {% if %} block can be used without an {% else %} was relevant to making the Ongoing badge appear only when an entry is actually ongoing.

### Assignment 3

1. Django's ModelForm generates form fields straight from the model, matching each field's type and validation rules automatically. Writing an HTML form by hand means duplicating that logic yourself and keeping it in sync every time the model changes, which is extra work and an easy place to introduce bugs. ModelForm also handles validation and error messages consistently, instead of writing that by hand for every field. The csrf_token tag is required because Django rejects any POST request that does not include a valid CSRF token. Without it, a malicious site could trick a logged in user's browser into submitting a form on their behalf without their knowledge. The token proves the request actually came from a page Django itself served.
2. JSON is preferred over XML mainly because it is lighter and faster to parse. XML needs opening and closing tags for every value, which adds a lot of extra characters for the same amount of data. JSON also maps directly onto data structures already used in most programming languages, like objects and arrays, so it needs no extra translation step once parsed. Most modern APIs and JavaScript tooling are built around JSON by default, which makes it the more practical choice for web applications today.
3. When a view function returns portfolio data in JSON format, it starts with model instances from the database, which are Python objects. Those objects cannot be sent directly over HTTP as JSON, so they first go through serialization, converting the model instances into a plain data structure that maps cleanly to JSON syntax. Once serialized, that data is returned as an HttpResponse with content type application/json. Serialization is required because JSON only understands basic data types like strings, numbers, and lists, while a Django model instance carries extra structure, like its Python class and database relationships, that JSON has no way to represent directly.

ChatGPT and Google's AI Overview was used for me to learn the following:
1. Reusing one form and one template for both creating and updating a record, checking whether the form's instance already has a primary key to tell which mode it's in, instead of building two separate templates for the same fields.
2. Prefilling a form with an existing database row by passing instance to the form class, so editing something loads its current values instead of showing a blank form.
3. Creating a feature branch, doing the work only on that branch, then merging it back with an explicit merge commit instead of a fast forward, so the branch's shape stays visible in the history afterward.
4. Undoing commits with git reset while keeping the actual file changes intact, rather than losing the work outright.

### Assignment 4

**What was implemented**

1. Editor role: a Django `Group` named `Editor` holding only the `main.change_education` permission, assigned to users exclusively through Django Admin. The owner keeps every permission because superusers pass all permission checks; regular users hold none.
2. Server-side access control: `main/decorators.py` defines `permission_required_or_403`, which sends anonymous visitors to the login page and returns HTTP 403 to logged-in users who lack the permission. `create_education` requires `main.add_education`, `update_education` requires `main.change_education`, and `delete_education` requires `main.delete_education`, so the Editor group cannot create or delete without any role-specific code in the views.
3. Template gating: Add, Edit and Delete controls render only when `perms.main.add_education`, `perms.main.change_education` or `perms.main.delete_education` is true. The navbar shows an Owner or Editor badge.
4. Stars: `toggle_star` is `@require_POST` and login-protected, uses the `starred_by` ManyToManyField (one star per user by construction), and the Education page shows each entry's total star count plus whether the current user has starred it. Visitors see the count and a "Log in to star" link.
5. API integrity: the Education JSON endpoint now serializes an explicit field whitelist, so the `starred_by` user IDs no longer appear in the public response.
6. Extras: custom `403.html`, safe `next` redirect after login (external URLs are rejected), and `delete_education` now rejects GET requests with 405.
7. 30 automated tests cover all four roles, button visibility per role, the 403 template, star toggling and counts, the JSON field whitelist, and the login redirect.

ChatGPT was used for me to learn or discover the following:
1. Defining the Editor role as a Django Group holding the `main.change_education` permission, instead of hardcoding `is_superuser` in each view.
2. The difference between "not logged in" and "logged in but not allowed". `login_required` redirects to the login page, while `permission_required(..., raise_exception=True)` returns HTTP 403, so `login_required` has to wrap the permission check or visitors would get a 403 instead of a redirect.
3. Restricting state-changing views with `@require_POST` so a GET returns 405, and passing a `fields` whitelist to `serializers.serialize` so the public JSON no longer exposes the `starred_by` user IDs.
4. Validating the `next` parameter with `url_has_allowed_host_and_scheme`, so login can send someone back to the page they came from without allowing redirects to an external site.
5. Getting star counts with `annotate(Count(...))` in one query, instead of running a query for every card while the template loops.

### Assignment 5

1. Debouncing is a technique where a function only runs once a certain amount of time has passed without the triggering event happening again, and every new event resets that timer. Wiring the search box straight to the `input` event would fire the AJAX request once per keystroke, so typing a 6-letter term like "Depok" would send 5 separate requests, most of which get discarded before their response even returns. Debouncing waits until the user stops typing for a short window (300ms here) before actually calling `fetch()`, so a normal typing speed produces one request instead of one per letter. This matters for the server, which no longer runs a redundant query for every keystroke, and for the client, since fewer in-flight responses means less risk of an old, slow response overwriting a newer search's results. I paired this with an `AbortController` for the same reason, so a stale request that does get sent is explicitly cancelled once a newer one starts.
2. `fetch()` returns a Promise immediately, before the browser has actually received a response from the server. `await` pauses execution inside an `async` function until that Promise settles, so the code written after the `fetch()` call only runs once the response has truly arrived. Without `await`, the next line would run right away while the response variable was still an unresolved Promise rather than the real `Response` object, so calling `.json()` on it or checking `response.ok` would either throw an error or operate on data that doesn't exist yet. In `addEducation`, for example, dropping `await` would mean the code tries to close the modal and decide which toast to show before Django has even validated the form, so the toast would never actually reflect what the server decided.
3. Cross-Site Scripting is an attack where an attacker gets their own JavaScript to run inside another user's browser, usually by saving it as if it were ordinary data (a title, a description) so it executes every time that data is displayed. Data rendered through a Django template is escaped automatically: printing `{{ value }}` converts characters like `<` and `>` into `&lt;` and `&gt;` before the HTML reaches the browser, so even a stored `<img onerror=...>` payload only ever displays as plain text. AJAX-rendered content skips that protection entirely, because the data arrives as raw JSON and I'm the one deciding how to turn it into HTML, usually by building a template literal and assigning it to `innerHTML`. `innerHTML` has no idea the string is supposed to be plain data, so anything inserted into it, escaped or not, gets parsed as real markup, and an unescaped `<script>` or `onerror` payload runs immediately. That's exactly why `escapeHtml` exists: it replicates Django's own auto-escaping by hand, specifically because switching to AJAX quietly removes the protection the template engine used to provide for free.

**What was implemented**

1. AJAX page load: `show_education` now renders only the page skeleton (loading, error, empty and grid states); `get_educations_json` builds its response by hand with `JsonResponse` instead of `serializers.serialize`, and includes `star_count` and `is_starred` computed for the requesting session.
2. Debounced search: typing in the institution field waits 300ms after the last keystroke before calling `fetch()`. An `AbortController` also cancels any still-in-flight request once a newer one starts, so a slow late response can't overwrite a newer search's results.
3. Modal add form: Add Education opens a Popover-based modal instead of a separate page. Submitting it calls a new `create_education_ajax` view through `fetch()`, which checks `request.user.has_perm("main.add_education")` inside the view itself, not just hidden in the template, validates with `EducationForm`, and responds 201, 400 or 403 in JSON.
4. CSRF: the AJAX POST sends the token through the `X-CSRFToken` header, read from the `csrftoken` cookie by a shared `getCookie()` helper.
5. Toasts: success and failure, including the server's field-specific validation errors, each show a toast, and the list refreshes by calling `fetchEducations()` again after a successful add, with no page reload.
6. XSS: every value from the JSON is passed through `escapeHtml()` before being inserted with `innerHTML`, and `EducationForm.clean_institution`, `clean_degree` and `clean_description` call `strip_tags` server-side as a second layer, rejecting an institution that becomes empty once stripped.
7. Shared code: `getCookie` and `escapeHtml` were moved out of `education.html` into `static/js/ajax-utils.js`, loaded once from `base.html`, exactly as Tutorial 5's own hint suggested, so any other section I add AJAX to later can reuse them instead of redefining them.
8. 42 automated tests now cover the AJAX create endpoint specifically (403 for every non-owner role, 405 on GET, 400 with field errors, and that a `<script>` tag is stripped before saving), plus a test confirming the shared script is loaded and the old inline copies are gone.

ChatGPT was used for me to learn or discover the following:
1. Building a `JsonResponse` by hand instead of using `serializers.serialize`, and why `star_count`/`is_starred` need to be computed per request rather than stored as static fields on the model.
2. Why `fetch()` never rejects on an HTTP error status like 403 or 400 and only rejects on a network failure, which is why every fetch call has to check `response.ok` itself instead of relying on a `catch` block alone.
3. The limits of `strip_tags`: Django's own documentation states it isn't a sanitizer and doesn't guarantee safe HTML on its own, which is why it's a second layer behind `escapeHtml` rather than a replacement for it.
4. Guarding `if (educationForm) { ... }` before attaching an event listener, since a Popover modal that's conditionally rendered per role means `document.getElementById()` returns `null` on pages where that role doesn't have the modal.

Limitation I observed:
ChatGPT cannot access the live PWS deployment or its database, so the Editor group's existence there was never confirmed by ChatGPT directly; I verified that myself.

### Assignment 6

1. REST (Representational State Transfer) is a way of designing an API around resources instead of actions. Each thing the API manages has its own URL, and clients act on it with standard HTTP methods whose meaning is the same everywhere. In my API, `/api/v1/education/` is the collection and `/api/v1/education/<id>/` is one entry: `GET` reads, `POST` creates, `PUT` and `PATCH` update and `DELETE` removes. Every response's status code says what happened: 201 after creating, 204 after deleting, 400 for invalid input, 403 for an action the role can't do, 404 for a missing entry. Returning JSON alone isn't enough to make an API RESTful. My Tutorial 5 endpoints already returned JSON, but they used action-style URLs like `/education/add-ajax/` and `/education/<id>/delete/`, sent every change as `POST`, and answered with redirects instead of meaningful status codes, so a client had to learn each URL's quirks instead of relying on one uniform contract. Strictly, REST also asks every request to be self-contained; my API relies on the login session cookie, which is a common compromise when the API is used by the site's own pages. `PUT` is a full update: the request has to include every required field, and leaving one out returns 400. `PATCH` is a partial update: only the fields that are sent change. My edit modal uses `PATCH` and sends only what the user actually changed, so renaming a degree sends just `{"degree": "..."}` and clearing the end date sends just `{"ended_at": null}`. `PUT` fits a client that already holds the whole record and wants to overwrite it in one go, such as a script that re-imports every education entry from a spreadsheet.
2. A serializer is the contract between the model and the outside world. In one class, `EducationSerializer` decides which fields appear in the JSON (an explicit list, so nothing is exposed by accident) and converts values into JSON types: dates become strings like `2025-08-01`, and the `is_ongoing` property and the star information become read-only fields. It also works in the other direction for input. It parses the incoming JSON, checks types and required fields, runs my `validate_<field>` methods (which strip HTML tags) and `validate()` (which checks the end date isn't before the start date), and only then saves. In Tutorial 5 I built each dictionary by hand in a loop for `JsonResponse` and validated input separately through `EducationForm`. The serializer improves on that in several ways. The read and write shapes are defined once, so the list, detail and `PATCH` responses can't drift apart. Read-only fields are enforced automatically, so a client sending `"star_count": 99` or a forged `id` is ignored, which my tests check. Errors come back as a 400 with messages per field, which my page shows under the matching input. Partial updates only need `partial=True`. The browsable API can also build its forms from the serializer. In Tutorial 5 I had to compute values like `started_year` myself and remember to leave out sensitive fields every time I touched that dictionary.
3. Authentication answers who is making the request; authorization answers what that person is allowed to do. In DRF, authentication runs first: `SessionAuthentication` reads Django's session cookie and sets `request.user`, or leaves an anonymous user. Permission classes then decide whether that user may make this request. My `IsPortfolioOwnerOrEditorOrReadOnly` lets everyone use the safe methods (`GET`, `HEAD`, `OPTIONS`) and maps `POST`, `PUT`/`PATCH` and `DELETE` to `main.add_education`, `main.change_education` and `main.delete_education`. Superusers have all three automatically, and the Editor group only has the second. Because `SessionAuthentication` doesn't send a `WWW-Authenticate` header, DRF answers writes from visitors who aren't logged in with 403 rather than 401. Hiding the Edit or Delete button only changes what the page draws. The endpoint still exists, and anyone can call it directly with `fetch()` from the browser console, with curl, or through the browsable API's forms. If the check lived only in the template, any regular user could `PATCH` or `DELETE` every entry. That's why the permission class runs on the server for every request, and why my tests send writes straight to the API as each role and then check that the database didn't change, instead of only checking which buttons appear.
4. With `SessionAuthentication`, the browser proves who I am by attaching the session cookie to every request to my site automatically, including requests triggered by another website. Without a CSRF check, a malicious page I visit while logged in could make my browser send a `PATCH` or `DELETE` to `/api/v1/education/...`, and the API would accept it because the cookie is valid. The CSRF token closes that gap: my page reads it from the `csrftoken` cookie and sends it back in the `X-CSRFToken` header. Another site can't do the same, because the browser won't let it read my site's cookies, and it won't send a cross-site request with that custom header unless my server allows it. DRF exempts its views from Django's CSRF middleware and runs the check inside `SessionAuthentication` instead, for unsafe methods whenever the request is authenticated by the session. `force_authenticate` skips authentication entirely: it sets `request.user` directly, so `SessionAuthentication` never runs and neither does its CSRF check, and a test using it would pass even if CSRF protection were missing. On top of that, Django's test client doesn't enforce CSRF at all unless it's created with `enforce_csrf_checks=True`. That's why my CSRF tests use `APIClient(enforce_csrf_checks=True)` and log in with `.login()` to get a real session. They show that the same `POST` or `PATCH` fails with 403 without the token and succeeds with it.

**What was implemented**

Tutorial 7 was done directly on Education, the section I have used in every tutorial and assignment since Tutorial 3, so the DRF API in `main/api_views.py` is this assignment's API. This assignment completes it.

1. The API, built in Tutorial 7: `EducationSerializer` with an explicit field list, read-only `star_count`, `is_starred` and `is_ongoing`, and `validate_<field>` methods that clean text with `strip_tags`. `IsPortfolioOwnerOrEditorOrReadOnly` follows the four roles. Function-based views with `@api_view` and `SessionAuthentication` serve the list (`GET`, `POST`), detail (`GET`, `PUT`, `PATCH`, `DELETE`) and star (`POST`). Search is the `?institution=` query parameter, and the routes are in `main/api_urls.py`.
2. Editing through the API: Add and Edit share one Popover modal. Edit loads the entry fresh with `GET`, then saves with a `PATCH` that contains only the fields that changed. If nothing changed, no request is sent and a toast says so. The Editor and the owner can both use it.
3. Errors: a 400 shows each message under its input and in a toast, and focus moves to the first invalid field. A 403 shows the server's message in a toast. If an entry was deleted elsewhere, the resulting 404 removes its card with a toast.
4. Validation fixes, shared by the form and the serializer through `main/validators.py`. An end date before the start date is rejected; on a `PATCH` it's checked against the stored dates, and only when a date is being changed, so older rows can still be edited. A description made only of HTML tags is rejected instead of being saved empty.
5. Structure: the page script moved out of the template into `static/js/education.js`. The view builds the API URLs and role flags, and the template passes them to the script with `json_script`. `@ensure_csrf_cookie` sets the CSRF cookie for every role. `requestJson` in `static/js/ajax-utils.js` adds `X-CSRFToken` to every request that changes data and raises an `ApiError` that carries the status and the errors.
6. Interaction details: an edited card is replaced in place; the list only reloads when a change affects its order or the active search. Focus returns to the Edit button after saving or closing the modal, and the Star button keeps focus after starring.
7. Tests: 80 in total, 16 of them new. They cover:
   - an Editor `PATCH` through a real logged-in session, with and without the CSRF token
   - a regular user with a valid token who is still forbidden
   - the date rule on `PATCH`, `PUT` and `POST`, older rows, and clearing the end date
   - HTML-only descriptions
   - 404 versus 403 for missing entries
   - the page's role flags, and that the shared helpers load before the page script

Claude was used for me to learn or discover the following:
1. How one DRF serializer replaces both the hand-built `JsonResponse` dictionary and the separate form validation, and the difference between `validate_<field>` (one field) and `validate()` (rules that compare fields).
2. Mapping each HTTP method to a Django model permission inside one permission class, and why superusers pass `has_perm` without belonging to any group.
3. Why a check that compares fields has to fall back to the stored values on a `PATCH` (`getattr(self.instance, ...)`), because a partial update only contains the fields that were sent.
4. Why `force_authenticate` never runs `SessionAuthentication`'s CSRF check, and why Django's test client skips CSRF unless it's created with `enforce_csrf_checks=True`.
5. Passing server data to JavaScript with `json_script` instead of writing template tags inside a script, and setting the CSRF cookie with `@ensure_csrf_cookie` instead of relying on a form being on the page.
6. Using `prefetch_related` with a query-count test (`CaptureQueriesContext`) to prove the list doesn't run one extra query per card.

**AI disclosure**

Tool: Claude (claude.ai)

How I prompted it: I gave Claude the assignment PDF and read-only access to my public GitHub repository, so it built on exactly what I had pushed, and asked for a plan. I then applied every file myself, ran the tests on my laptop, and checked the page in my browser.

Parts Claude wrote: the API files (`serializers.py`, `permissions.py`, `api_views.py`, `api_urls.py`), `main/validators.py`, the edit flow in `static/js/education.js` and `static/js/ajax-utils.js`, the tests, and drafts of this README section. Before handing the code over, it tested it in a headless browser as every role and broke ten pieces of code on purpose to confirm the tests catch each one.

Limitations I observed:

- Claude can't reach my laptop or PWS. Its sandbox blocks `pws.cs.ui.ac.id`, so it tested a copy of my code against a throwaway SQLite database, and checking the live deployment was up to me.
- Its Tutorial 7 instructions for checking DevTools left out the extra `GET` (status 200) that reloads the list after adding an entry, so what I saw didn't match what it described until it replayed the flow and corrected itself.
- Its browser test script for this assignment had a timing bug: it waited for a "Success" toast that was still on screen from the previous action, so four checks failed for the wrong reason until it fixed the script.

**Prompting log (summary)**

1. Shared the Tutorial 7 PDF and gave Claude read-only access to my repository. It built the DRF API on Education, switched the page to it, and tested it for every role in a headless browser.
2. Followed its steps and sent back my terminal output and screenshots. When the status codes in DevTools didn't match its description, I asked it to replay the flow, and it corrected its instructions.
3. Shared the Assignment 6 PDF and asked for a plan. It built the `PATCH` edit modal, the validation fixes, and the new tests.
4. Applied the files, ran the tests, checked the page in my browser, and committed on a feature branch with conventional commits.
