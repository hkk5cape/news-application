Python and HTTP reference
=========================

Models
------

.. automodule:: news.models
   :members: User, Publisher, Article, Newsletter, ApprovalEvent, ArticleEmail, ApprovedLog, NewsletterEmail
   :show-inheritance:

Access policies
---------------

.. automodule:: news.policies
   :members:

Forms
-----

.. automodule:: news.forms
   :members: RegistrationForm, ArticleForm, NewsletterForm, SubscriptionForm, PublisherForm, EmployeeForm

Services
--------

.. automodule:: news.services
   :members: approve_article, dispatch_approval, send_newsletter

Web workflows
-------------

.. automodule:: news.views
   :members: home, register, workspace, article_edit, article_approve, publisher_edit, publisher_detail, employee_remove

HTTP API
--------

POST /api/token/ with a username and password to obtain a private token.
Use the Authorization header with the value ``Token YOUR_TOKEN``.

.. list-table:: Main endpoints
   :header-rows: 1
   :widths: 38 62

   * - Method and path
     - Purpose
   * - GET/POST /api/articles/
     - List approved stories; journalists can create drafts.
   * - GET/PATCH/DELETE /api/articles/<id>/
     - Read or change a permitted story.
   * - POST /api/articles/<id>/approve/
     - Editor approval with author and company checks.
   * - POST /api/approved/
     - Record an event owned by the approving editor.
   * - GET /api/articles/subscribed/
     - Reader's subscribed feed.
   * - GET /api/publishers/
     - Publisher directory.
   * - GET/POST /api/newsletters/
     - List or create newsletters according to permissions.
   * - GET/PATCH/DELETE /api/newsletters/<id>/
     - Newsletter detail and authorised changes.
   * - GET /api/me/
     - Current user's role and applicable fields.
