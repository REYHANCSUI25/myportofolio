Name : Reyhan

NPM : 2506637086

Class : PBP KKI

Portfolio repo for PBP KKI, Odd Semester 2026/2027

## Overview

A personal portfolio website built with Django as the individual project of Platform-Based Programming (CSGE602022), Fasilkom UI. The portfolio section is **Education**: public list and JSON endpoints, with data changes and stars controlled by user roles.

Live site: https://muhammad-reyhan53-myportofolio.pws.cs.ui.ac.id

## Setup

1. `git clone https://github.com/REYHANCSUI25/myportofolio.git` then `cd myportofolio`
2. `python -m venv env`
3. Windows PowerShell: `env\Scripts\activate` (macOS/Linux: `source env/bin/activate`)
4. `pip install -r requirements.txt`
5. `python manage.py migrate`
6. `python manage.py createsuperuser` (this account becomes the portfolio owner)
7. `python manage.py runserver` and open http://127.0.0.1:8000/

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
| Read Education page and JSON | Yes | Yes | Yes | Yes |
| Give or remove a star | Log in first | Yes | Yes | Yes |
| Update an entry | Log in first | 403 | Yes | Yes |
| Create an entry | Log in first | 403 | 403 | Yes |
| Delete an entry | Log in first | 403 | 403 | Yes |

## Weekly Progress

| Week | Work |
| --- | --- |
| Tutorial 0 and 1 | Project setup, views, templates, HTML5/CSS3, PWS deployment |
| Assignment 1 | Static portfolio page with semantic HTML |
| Assignment 2 | Education model, list view, base template inheritance |
| Assignment 3 | ModelForm create/update/delete, JSON endpoints, institution search |
| Assignment 4 | Editor role via Django Group, server-side 403/redirect enforcement, POST-only star toggle with counts, JSON leak fix, login redirect back to the requested page, custom 403 page |
| Assignment 5 | Education page loads via `fetch()` against a hand-built `JsonResponse`, debounced AJAX search, Popover add-education modal with a permission-checked AJAX create endpoint, toast notifications, XSS escaping plus server-side `strip_tags` cleaning, shared `static/js/ajax-utils.js` |

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
ChatGPT cannot access the live PWS deployment or its database, so the Editor group's existence there was never confirmed by Claude directly; I verified that myself.
