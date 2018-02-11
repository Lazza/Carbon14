# Carbon14

OSINT tool for estimating when a web page was written.

From [Wikipedia][1]:

> Radiocarbon dating (also referred to as carbon dating or carbon-14 dating) is
> a method for determining the age of an object containing organic material by
> using the properties of radiocarbon (<sup>14</sup>C), a radioactive isotope of
> carbon.

## Rationale

While performing digital forensics or OSINT, it might be crucial to determine
when a certain blog post has been written. Common CMS's easily permit to change
the displayed date of content, affecting both websites and RSS feeds. Moreover,
the dynamic nature of most web pages does not allow investigators to use the
`Last-Modified` HTTP header.

However, most users do not alter the timestamps of static resources that are
uploaded while writing articles. The `Last-Modified` header of linked images can
be leveraged to estimate the time period spent by the writer while preparing a
blog post. This period can be compared to what the CMS shows in order to detect
notable differences.

## Usage

Carbon14 accepts the target URL and an optional author name.

    usage: carbon14.py [-h] [-a name] url

    Date images on a web page.

    positional arguments:
      url                   URL of the page

    optional arguments:
      -h, --help            show this help message and exit
      -a name, --author name
                            author to be included in the report

The tool prints a simple report in [Pandoc's extended Markdown][2] format which
can then be redirected to a file (or with `tee`). For example:

    carbon14.py 'https://eforensicsmag.com/extracting-data-damaged-ntfs-drives-andrea-lazzarotto/' > report.md

Here's a snippet of the output:

    # Internal images

    --------------------------------------------------------------------------------
    Date (UTC)           Date (Europe/Rome)   URL
    -------------------- -------------------- --------------------------------------
    2017-02-06 19:53:16  2017-02-06 20:53:16  <https://eforensicsmag.com/wp-content/uploads/2016/09/Untitled-1.png>

    2017-02-06 19:53:25  2017-02-06 20:53:25  <https://eforensicsmag.com/wp-content/uploads/2016/02/logo-1.png>

    2017-02-06 19:53:36  2017-02-06 20:53:36  <https://eforensicsmag.com/wp-content/uploads/2015/09/Untitled-1.png>

We can infer that work on that article began on February 6, 2017.

## Markdown report

The Markdown syntax is text-based and lightweight. This means that the report
**can be used or printed as-is,** like a normal text file. Optionally, examiners
might want to convert it to a different format such as HTML, ODT or DOCX.

This *optional step* can be performed with [Pandoc][3]:

    pandoc -s report.md -o report-web.html
    pandoc report.md -o report-libreoffice.odt
    pandoc report.md -o report-msword.docx

Pandoc can also be used to generate HTML reports with custom CSS files, PDF
reports and several other outputs. Please refer to its [documentation][2] for
further details.


  [1]: https://en.wikipedia.org/wiki/Radiocarbon_dating
  [2]: https://pandoc.org/MANUAL.html
  [3]: https://pandoc.org/
