User walkthrough
================

Create a publishing company
---------------------------

#. Open the home page and choose **Create an account**.
#. Register as **Editor** with your own email and strong password.
#. In **My publishers**, choose **Create publisher** and save the company profile.
   The creator becomes its first editor automatically.
#. Have a colleague register as **Journalist** using their own account.
#. Open the company and use **Add an employee** with that exact username.

Editors can edit their company's profile and remove employees. The last active
editor is protected from removal. Employees cannot manage unrelated companies.

Write and approve
-----------------

#. Sign in as the journalist, open **Newsroom**, then **Write article**.
#. Enter a title and content, select the employer, and save the draft.
#. Sign in as an assigned editor, open the story and select **Approve / retry
   delivery**. Authors cannot approve their own stories.
#. The approved article appears in **Latest news**. Readers cannot see drafts.
#. Editing an article creates a new revision and requires approval again.

Use separate browser profiles or log out between roles. These are real accounts
you register locally; the installation does not seed mock users.

Subscriptions and newsletters
-----------------------------

Readers register with the **Reader** role, then open **Subscriptions** to follow
publishers and journalists. **My subscriptions** filters their approved feed.
Editors and journalists can use **Newsletters**, curate approved articles and
send the newsletter to subscribers. Console email is visible in terminal logs.

Approval delivery
-----------------

Approval creates a durable revision snapshot and email recipient records before
network calls. Delivery then emails readers and uses Requests to POST the event
to /api/approved/. Retrying skips deliveries already marked successful. Network
ambiguity can still cause duplicate remote acceptance; exactly-once delivery is
not guaranteed. Use **Approve / retry delivery** after resolving a connection
problem. Check pending emails and API status displayed by the application.
