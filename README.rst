armstrong.apps.embeds
=====================

.. image:: https://travis-ci.org/armstrong/armstrong.apps.embeds.svg?branch=master
  :target: https://travis-ci.org/armstrong/armstrong.apps.embeds
  :alt: TravisCI status
.. image:: https://img.shields.io/coveralls/armstrong/armstrong.apps.embeds.svg
  :target: https://coveralls.io/r/armstrong/armstrong.apps.embeds
  :alt: Coverage status
.. image:: https://pypip.in/version/armstrong.apps.embeds/badge.svg
  :target: https://pypi.python.org/pypi/armstrong.apps.embeds/
  :alt: PyPI Version
.. image:: https://pypip.in/license/armstrong.apps.embeds/badge.svg
  :target: https://pypi.python.org/pypi/armstrong.apps.embeds/
  :alt: License

Armstrong.Apps.Embeds provides a data model and modular backend system to
extract embeddable content and metadata from external URLs. Representing
embeddable content in a database brings the typical benefits of relational
data. Programmable backends allow more flexible use of the content beyond
the one-trick pony of the standard "<iframe>" copy-paste embed code.

Integrating AppsEmbeds into your site will require some work. Mostly because
this package doesn't make assumptions for *how* you'll be using these
external URLs. Maybe you just want to track references to embedded content,
maybe it's the caching that's interesting or programmatically accessing
content provider metadata is what you are after. There's nothing extra to get
in your way, but you'll have to customize code and/or templates.

This is a stand alone component; it *does not* require any other pieces of the
Armstrong family. However, it does play nicely with `ArmLayout`_. If you use
ArmLayout already, AppsEmbeds is ready to go. Much of the power of AppsEmbeds
comes from templating so if you use that feature and aren't already using
ArmLayout, it's worth considering.

The second optional package is `lxml`_, which is necessary if you use the
``resize_iframe`` template filter. Otherwise, this package has three fixed
requirements to provide model fields and support the backend APIs (currently
just Embedly). See ``package.json`` for these fixed requirements.


.. _ArmLayout: https://github.com/armstrong/armstrong.core.arm_layout/
.. _lxml: https://pypi.python.org/pypi/lxml/

Features
--------
- **Single embed, multiple relationships!** Always know where you are using
  external content and the number of references you have.
- **Metadata!** Access the metadata of the external content. Much more useful
  than the vanilla iframe embed code.
- **Modular backends!** Get metadata and embed codes with a standard
  interface to the various content provider APIs.
- **Customizable templates!** Presentation is separate from data. Make that
  external content look appropriate for your site.
- **Single embed, multiple uses!** Create templates for each use case. A video
  can be used as a title, thumbnail, captioned credit, in a gallery, etc.
- **Uniform visual appearance!** Each content type shares templates. Video
  content can be presented in a standard format regardless of the source.
- **Automatic backend assignment!** Program an Embed in one step.
  The URL is all we need.
- **Admin preview!** Examine the response data before saving. Look weird?
  Switch backends and preview again.
- **Response caching!** Worry less about third-party API failure. The
  response is cached indefinitely.
- **Check for new data!** See if new data is available without committing
  to it, right from the Admin.
- **Bird's eye overview!** Aggregate information on how and what types of
  external content you generally use.


Installation & Configuration
----------------------------
Supports Django 1.3, 1.4, 1.5, 1.6, 1.7 on Python 2.6 and 2.7.
(Though if you are using Django 1.3, make sure to use django-model-utils<1.4.)

#. ``pip install armstrong.apps.embeds``

#. [optional] ``pip install lxml`` if you plan on using the
   ``resize_iframe`` template filter

#. [optional] ``pip install armstrong.core.arm_layout`` if you want to use
   ArmLayout to render templates

#. Add ``armstrong.apps.embeds`` to your ``INSTALLED_APPS``

#. Install the database schema

   * Django 1.7+ use ``manage.py migrate``
   * previous Djangos use either ``manage.py syncdb`` or ``manage.py migrate``
     if you are using `South`_ (in which case use South 1.0+)

#. Load the provided Backends into your database. (This is not provided as
   initial fixture data so that you may edit them without worrying that
   syncdb will restore the initial versions.)

  ``manage.py loaddata embed_backends.json``

7. If you are using the Embedly backend, add your API key to ``settings.py``

  ``EMBEDLY_KEY = 'your key'``


**Logging:** This component emits logging statements using the
``armstrong.apps.embeds`` logger.

.. _South: http://south.aeracode.org/


Usage
-----
**A quick overview of the four models--**

``EmbedType`` and ``Provider`` do essentially nothing besides normalize the
database and provide a quick way to perform aggregation queries. EmbedType is
based on the four `oEmbed`_ types, though in practice you'll likely have a
fifth ``error`` type (and that's okay).

``Backend`` is the front-end model for the actual code that connects to
third-party APIs to retrieve response data for the external content URLs.
It's easiest to initially load them from the fixture data file but feel free
to customize them as you will. Just don't change the ``slug``, which is how
the model maps to its code back-end. ``regex`` and ``priority`` are designed
to change. That's how you'll customize the auto-assignment behavior. The
Embedly backend will handle YouTube sure, but say you've written a more
targeted YouTube-specific backend--add it to the database with a selective
regex and a higher priority.

``Embed`` is the cornerstone. Creating a new embed object only requires a
``url``. The backend will auto-assign by regular expression matching the URL
and selecting from the matching backends by highest priority. Auto-assignment
is just a nice feature for faster Embed creation. You can also manually assign
a backend on object creation or later. Every other field on the model is
backend-provided metadata. Consider them read-only. So how do you get a
response? How do you get actual information?

**The Response object--**

``embed_obj.update_response()`` will retrieve a response from the backend and
assign it if the response is *valid* and *different*, then return ``True``. If
the response is invalid or the same, no assignment is made and ``False`` is
returned. If you want the response object itself, use
``embed_obj.get_response()``.

``embed_obj.response`` is the way to access the response data. This will be a
subclass of the ``BaseResponse`` object with a standard set of attributes.
``is_valid()`` will be False in cases where the API had a problem, didn't
return data, 404'd, etc. ``is_fresh()`` will be True when the response is
fresh off the wire. It's used to differentiate from database cached response
data and you can probably ignore it. ``type`` and ``provider`` are
``EmbedType`` and ``Provider`` model objects. ``_data`` holds the actual raw
response in JSON. The goal is to never directly access this. Instead, the
BaseResponse class is subclassed by each backend/API and tailored to parse the
raw data into standardized attributes. This way who cares if it's YouTube or
Vimeo, access the object the same and share the templates. These attributes
return an empty string when nothing is available and are therefore
*template safe*. The current data attributes are:

- ``title``
- ``author_name``
- ``author_url``
- ``image_url``
- ``image_height``
- ``image_width``
- ``render``

``render`` is perhaps the most important; it is the full expression of the
embedded content that the content provider offers. For Twitter, this is the
blockquote with JavaScript widget that dynamically loads the tweet into an
iframe. For YouTube and Vimeo, this is the video player. Whatever way the
service designs its content to be embedded, this is it.

``image_xxx`` means different things depending on the content. For a video,
this will be the still image that shows before the video is played. For
SlideShare, it's the first slide in the presentation. For Flickr, it's the
thumbnail. It's worth noting that we have no idea what the image size will
be and so if you use this in a template, consider fixing the image tag's
dimensions with attributes or CSS.


**Backends--**

`Embedly`_ is a sort of meta-embed service. They know how to handle over 250
content providers to deliver a standardized set of metadata. Specifically this
backend uses their "Embed" service via their `embedly-python`_ library. It
offers a huge benefit but does require an account. Fortunately there is a quite
reasonable free tier. Configuration required to use this is mentioned under the
Installation section.

**Twitter** is a simple wrapper for a tag that loads the tweet via Twitter's
JavaScript widget. It does not perform any API or network calls and therefore
does not provide any metadata about the URL. The only thing it can do is embed
the Tweet as if you'd copy-pasted the embed code.

**Default** just regurgitates the provided URL. It's the catch-all that does
nothing useful.


.. _Embedly: http://embed.ly/
.. _embedly-python: https://github.com/embedly/embedly-python/

**Templates--**

Assuming you want to display the embed content on your site, this is where
you'll spend the most developer time. It's not just about what a photo looks
like versus a video. Now that you have access to more than just the "embed
code"--now that you have metadata--you can use the same embed multiple ways.
For example, a photo can be used as a preview thumbnail with a small image,
a larger image with a title for lead art, a thumbnail in a story that expands
into a modal full-size version with attribution. Whatever you want. Since
Response objects have a standard interface, it doesn't even matter where that
photo came from. Instagram and TwitPic behave the same.

Note: This concept of provider apathy hinges on the ``EmbedType``. We can only
treat like types the same or fall back to something generic for all embeds.
If the provider or the backend reports a Flickr URL as a "link" type, even
though we know in our hearts it's a "photo", it won't use the photo-specific
templates.

Now for some examples. Since `ArmLayout`_ was designed for this purpose, we'll
use it. It provides a ``render_model`` template tag that takes an object and a
template name then looks in a hierarchy from most-specific to least for that
template. ArmLayout uses ``get_layout_template_name()`` for the lookup and
AppsEmbeds has extended it to also look for type-specific templates.

``render_model embed_obj 'full'`` for a ``photo`` type will look in this order:

- ``layout/embeds/embedtype/photo/full.html``
- ``layout/embeds/embed/full.html``

So to display an Embed object as "preview", just make the following files.
Each content type can customize what "preview" means. (Maybe a small
thumbnail or truncated intro text.)

- ``layout/embeds/embedtype/photo/preview.html``
- ``layout/embeds/embedtype/video/preview.html``
- ``layout/embeds/embedtype/link/preview.html``
- ``layout/embeds/embedtype/rich/preview.html``
- ``layout/embeds/embed/preview.html``

"Lead art" could be another way of displaying an embed. (Perhaps a larger
image along with title and author attribution.)

- ``layout/embeds/embedtype/photo/lead_art.html``
- ``layout/embeds/embedtype/video/lead_art.html``
- ``layout/embeds/embedtype/link/lead_art.html``
- ``layout/embeds/embedtype/rich/lead_art.html``
- ``layout/embeds/embed/lead_art.html``

Leave out a type-specific template file and ArmLayout will use the more
general file next in the hierarchy.

There's also a ``default.html`` template used as a fallback when the response
is invalid or missing. (This template name can be customized via
``embed_obj.fallback_template_name``.) Without a response, there won't be any
data to show in the normal/intended template. A fallback can provide more
helpful output and a visual reference that something isn't right.


**Template tags/filters (requires lxml)--**

``resize_iframe`` is a template filter that caps the width of iframes since
embedding an unexpectedly huge iframe into your layout might break the
appearance. It only shrinks large iframes; it doesn't alter iframes that are
already the specified size (or smaller).

Common usage:
  ``{{ object.response.render|resize_iframe:645|safe }}``

In this example, if the ``render`` attribute contains code with iframes and
the width of any or all of those iframes is larger than 645px, the iframes'
width will be changed to 645 and the height will scale smaller accordingly.


.. _oEmbed: http://oembed.com/


Limitations
-----------
**Content provider terms of service--**

The service you are embedding content from may have usage guidelines and
restrictions. Pay attention and follow these. It may be against their terms
of service to rework or restyle the presentation or to use only pieces of the
metadata. Changing or reusing things may also be disrespectful and disingenuous
to the content creator. Respect the creator and respect the service.

**Publishing content--**

Embedded content is already published; it's available from some other site.
It's how we use and integrate that external content into our own works that
matters here. Armstrong is a platform for newsrooms and content publishers.
The typical situation is one where reporters and editors write, draft, proof
and publish. Content has eyes on it and doesn't get published until it's
finished. AppsEmbeds is just the same. A general assumption is that some
human is looking at the embed--maybe not the raw response data--but certainly
the end result of how it looks (i.e. how a template renders it). If it looks
wrong, it doesn't get published.

It's likely that someday you'll come across a content provider whose responses
don't fit the expected form. It's hard to account for these things but
hopefully someone is looking at the content and will notice.

**Custom API queries--**

Many APIs provide customization for the responses they provide. They may allow
you to specify maxwidth and maxheight, alignments for text or localization,
callbacks, transparency modes or word length truncation. AppsEmbeds doesn't
do any of that primarily because it can't make those assumptions. AppsEmbeds
gets you the raw data in its default form whatever that may be and follows
the "customize after" approach.

``resize_iframe`` is an example of this. You may want a 200px iframe for a
preview and an 800px iframe within an article body for the *same* embedded
content. It wouldn't do to set a maxwidth=200 on the API call, cache that
and then be stuck for the larger size use case.

Ultimately, API use can be a finicky thing. The best course of action within
the AppsEmbeds paradigm is to customize or create a backend and/or response
class fitting the API you use and the parameters you may want to query with.
Have a better idea or an awesome backend? Please make a Pull Request!

**Different URLs to the same content--**

There is currently no way to know if multiple URLs refer to the same content.
These two YouTube links will make two separate Embed objects::

  https://www.youtube.com/watch?v=12345
  https://www.youtube.com/watch?v=12345&feature=player_embedded

Contributing
------------
Development occurs on Github. Participation is welcome!

* Found a bug? File it on `Github Issues`_. Include as much detail as you
  can and make sure to list the specific component since we use a centralized,
  project-wide issue tracker.
* Testing? ``pip install tox`` and run ``tox``
* Have code to submit? Fork the repo, consolidate your changes on a topic
  branch and create a `pull request`_. The `armstrong.dev`_ package provides
  tools for testing, coverage and South migration as well as making it very
  easy to run a full Django environment with this component's settings.
* Questions, need help, discussion? Use our `Google Group`_ mailing list.

.. _Github Issues: https://github.com/armstrong/armstrong/issues
.. _pull request: http://help.github.com/pull-requests/
.. _armstrong.dev: https://github.com/armstrong/armstrong.dev
.. _Google Group: http://groups.google.com/group/armstrongcms


State of Project
----------------
`Armstrong`_ is an open-source news platform that is freely available to any
organization. It is the result of a collaboration between the `Texas Tribune`_
and `The Center for Investigative Reporting`_ and a grant from the
`John S. and James L. Knight Foundation`_. Armstrong is available as a
complete bundle and as individual, stand-alone components.

.. _Armstrong: http://www.armstrongcms.org/
.. _Texas Tribune: http://www.texastribune.org/
.. _The Center for Investigative Reporting: http://cironline.org/
.. _John S. and James L. Knight Foundation: http://www.knightfoundation.org/
