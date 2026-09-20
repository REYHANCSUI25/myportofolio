Name : Reyhan

NPM : 2506637086

Class : PBP KKI

Portfolio repo for PBP KKI, Odd Semester 2026/2027

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
