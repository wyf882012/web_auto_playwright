#! /usr/bin/env python3
"""
Allure static files combiner.

Create single html files with all the allure report data, that can be opened from everywhere.

Example:
    python3 ./combine.py ../allure_gen [--dest xxx] [--remove-temp-file] [--auto-create-folders]

    or

    pip install allure-combine
    allure-combine allure_report_dir [--dest xxx] [--remove-temp-file] [--auto-create-folders]
    ac allure_report_dir [--dest xxx] [--remove-temp-file] [--auto-create-folders]

"""
# 基于开源代码二次开发： https://github.com/MihanEntalpo/allure-single-html-file
# pylint: disable=line-too-long

import os
import re
import base64
import argparse
from shutil import copyfile
from bs4 import BeautifulSoup

from loguru import logger
sep = os.sep
re_sep = os.sep if os.sep == "/" else r"\\"


def combine_allure(folder, dest_folder=None, remove_temp_files=False, auto_create_folders=False, ignore_utf8_errors=False):
    """
    Read all files,
    create server.js,
    then run server.js,
    """

    if not dest_folder:
        dest_folder = folder

    if dest_folder and not os.path.exists(dest_folder):
        if not auto_create_folders:
            raise FileNotFoundError(
                "Dest folder does not exists, please create it first, "
                "or you can use --auto-create-folders argument if in the command line.")
        else:
            logger.debug("Argument auto_create_folders is True, and Dest folder does not exists, so create it. --- start")
            os.makedirs(dest_folder)
            logger.debug("Done")

    cur_dir = os.path.dirname(os.path.realpath(__file__))

    logger.debug("> Folder to process is " + folder)
    logger.debug("> Checking for folder contents")

    files_should_be = ["index.html", "app.js", "styles.css"]

    for file in files_should_be:
        if not os.path.exists(folder + sep + file):
            raise Exception(f"ERROR: File {folder + sep + file} doesnt exists, but it should!")

    default_content_type = "text/plain;charset=UTF-8"

    content_types = {
        "svg": "image/svg",
        "txt": "text/plain;charset=UTF-8",
        "js": "application/javascript",
        "json": "application/json",
        "csv": "text/csv",
        "css": "text/css",
        "html": "text/html",
        "xml": "text/xml",
        "htm": "text/html",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpg",
        "gif": "image/gif",
        "mp4": "video/mp4",
        "avi": "video/avi",
        "webm": "video/webm"
    }

    base64_extensions = ["png", "jpeg", "jpg", "gif", "html", "htm", "mp4", "avi"]

    allowed_extensions = list(content_types.keys())

    data = []

    logger.debug("> Scanning folder for data files...")
    
    for path, dirs, files in os.walk(folder):
        if files:
            folder_url = re.sub(f"^{folder.rstrip(sep).replace(sep, re_sep)}{re_sep}", "", path)
            if folder_url and folder_url != folder:
                for file in files:
                    try:
                        file_url = folder_url + sep + file
                        ext = file.split(".")[-1]
                        if ext not in allowed_extensions:
                            logger.debug(f"WARNING: Unsupported extension: "
                                  f"{ext} (file: {path}{sep}{file}) skipping (supported are: {allowed_extensions}")
                            continue
                        mime = content_types.get(ext, default_content_type)
                        if ext in base64_extensions:
                            with open(path + sep + file, "rb") as f:
                                content = base64.b64encode(f.read())
                        else:
                            with open(path + sep + file, "r", encoding="utf8", errors='ignore' if ignore_utf8_errors else "strict") as f:
                                content = f.read()

                        data.append({"url": file_url, "mime": mime,
                                     "content": content, "base64": (ext in base64_extensions)})
                    except UnicodeDecodeError as e:
                        logger.debug(f"Error on reading file {folder_url + sep + file}: {e}. Use --ignore-utf8-errors argument to skip this type of errors")

    logger.debug(f"Found {len(data)} data files")

    logger.debug("> Building server.js file...")

    with open(f"{folder}{sep}server.js", "w", encoding="utf8") as f:
        f.write(r"""
        function _base64ToArrayBuffer(base64) {
            var binary_string = window.atob(base64);
            var len = binary_string.length;
            var bytes = new Uint8Array(len);
            for (var i = 0; i < len; i++) {
                bytes[i] = binary_string.charCodeAt(i);
            }
            return bytes.buffer;
        }

        function _arrayBufferToBase64( buffer ) {
          var binary = '';
          var bytes = new Uint8Array( buffer );
          var len = bytes.byteLength;
          for (var i = 0; i < len; i++) {
             binary += String.fromCharCode( bytes[ i ] );
          }
          return window.btoa( binary );
        }

        document.addEventListener("DOMContentLoaded", function() {
            var old_prefilter = jQuery.htmlPrefilter;

            jQuery.htmlPrefilter = function(v) {
            
                var regs = [
                    /<a[^>]*href="(?<url>[^"]*)"[^>]*>/gi,
                    /<img[^>]*src="(?<url>[^"]*)"\/?>/gi,
                    /<source[^>]*src="(?<url>[^"]*)"/gi
                ];
                
                var replaces = {};

                for (i in regs)
                {
                    reg = regs[i];

                    var m = true;
                    var n = 0;
                    while (m && n < 100)
                    {
                        n += 1;
                        
                        m = reg.exec(v);
                        if (m)
                        {
                            if (m['groups'] && m['groups']['url'])
                            {
                                var url = m['groups']['url'];
                                if (server_data.hasOwnProperty(url))
                                {
                                    console.log(`Added url:${url} to be replaced with data of ${server_data[url].length} bytes length`);
                                    replaces[url] = server_data[url];                                    
                                }
                            }
                        }
                    }
                }
                
                for (let src in replaces)
                {
                    let dest = replaces[src];
                    v = v.replace(src, dest);
                }

                return old_prefilter(v);
            };
        });

        """)

        f.write("var server_data={\n")
        for d in data:
            url = d['url'].replace(sep, "/")
            b64 = d['base64']
            if b64:
                content = "data:" + d['mime'] + ";base64, " + d['content'].decode("utf-8")
                f.write(f""" "{url}": "{content}", \n""")
            else:
                content = d['content'].replace("\\", "\\\\").replace('"', '\\"')\
                    .replace("\n", "\\n").replace("<", "&lt;").replace(">", "&gt;")

                f.write(f""" "{url}": "{content}", \n""")
        f.write("};\n")

        f.write("    var server = sinon.fakeServer.create();\n")

        for d in data:
            content_type = d['mime']
            url = d['url'].replace(sep, "/")
            f.write("""
                server.respondWith("GET", "{url}", [
                      200, { "Content-Type": "{content_type}" }, server_data["{url}"],
                ]);
            """.replace("{url}", url).replace("{content_type}", content_type))

        f.write("server.autoRespond = true;")

    size = os.path.getsize(f'{folder}{sep}server.js')
    logger.debug(f"server.js is build, it's size is: {size} bytes")

    logger.debug("> Copying file sinon-9.2.4.js into folder...")
    copyfile(cur_dir + f"{sep}sinon-9.2.4.js", folder + f"{sep}sinon-9.2.4.js")

    logger.debug("sinon-9.2.4.js is copied")

    logger.debug("> Reading index.html file")
    with open(folder + f"{sep}index.html", "r", encoding="utf8") as f:
        index_html = f.read()

    if "sinon-9.2.4.js" not in index_html:
        logger.debug("> Patching index.html file to make it use sinon-9.2.4.js and server.js")
        index_html = index_html.replace(
            """<script src="app.js"></script>""",
            """<script src="sinon-9.2.4.js"></script><script src="server.js"></script><script src="app.js"></script>""")

        with open(folder + f"{sep}index.html", "w", encoding="utf8") as f:
            logger.debug("> Saving patched index.html file, so It can be opened without --allow-file-access-from-files")
            f.write(index_html)
        logger.debug("Done")
    else:
        logger.debug("> Skipping patching of index.html as it's already patched")

    logger.debug("> Parsing index.html")
    soup = BeautifulSoup(''.join(index_html), features="html.parser")
    logger.debug("> Filling script tags with real files contents")
    for tag in soup.findAll('script'):
        if tag.has_attr('src'):
            file_path = folder + sep + tag['src']
            if os.path.exists(file_path):
                logger.debug("...", tag, file_path)                
                with open(file_path, "r", encoding="utf8") as ff:
                    file_content = ff.read()
                    full_script_tag = soup.new_tag("script")
                    full_script_tag.insert(0, file_content)
                    tag.replaceWith(full_script_tag)
            else:
                logger.debug("...", tag, "skipped due to file", file_path, "does not exists")
    logger.debug("Done")

    logger.debug("> Replacing link tags with style tags with real file contents")
    for tag in soup.findAll('link'):
        if tag.has_attr('rel'):
            if tag['rel'] == ["stylesheet"]:
                file_path = folder + sep + tag['href']
                if os.path.exists(file_path):
                    logger.debug("...", tag, file_path)
                    with open(file_path, "r", encoding="utf8") as ff:
                        file_content = ff.read()
                        full_script_tag = soup.new_tag("style")
                        full_script_tag.insert(0, file_content)
                        tag.replaceWith(full_script_tag)
                else:
                    logger.debug("...", tag, "skipped due to file", file_path, "does not exists")

    logger.debug("Done")
    import time
    # time_str = time.strftime("%Y_%m_%d_%H_%M_%S", time.localtime())
    with open(dest_folder + f"{sep}report.html", "w", encoding="utf8") as f:
        # 添加华测教育标记
        result = str(soup).replace("<title>Allure Report</title>", '<title>测试报告 - 华测教育</title>')
        result = result.replace('<a href="."', '<a href="http://vip.hctestedu.com" style="display:block; background: none; padding-left:0px;" class="side-nav__brand" > <span class ="side-nav__brand-text" style="font-size:20px;" > 华测教育科技 <a style="display:none;" ')
        f.write(result)

    logger.debug(f"> Saving result as {dest_folder}{sep}report.html")

    # size = os.path.getsize(dest_folder + f'{sep}report.html')
    # logger.debug(f"Done. Complete file size is:{size}")

    if remove_temp_files:
        logger.debug("Argument remove_temp_files is True, "
              "will remove temp files in allure report folder: server.js and sinon-9.2.4.js.")
        os.remove(f'{folder}{sep}server.js')
        os.remove(f'{folder}{sep}sinon-9.2.4.js')
        logger.debug("Done")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('folder', help='Folder path, where allure static files are located')
    parser.add_argument('--dest', default=None,
                        help='Folder path where the single html file will be stored. '
                             'Default is None, so dest folder == allure static files folder.')
    parser.add_argument('--remove-temp-files', action="store_true",
                        help='Whether remove temp files in source folder: server.js and sinon-9.2.4.js or not. '
                             'Default is false')
    parser.add_argument("--auto-create-folders", action="store_true",
                        help="Whether auto create dest folders or not when folder does not exist. Default is false.")
    parser.add_argument("--ignore-utf8-errors", action="store_true",
                        help="If test files does contain some broken unicode, decode errors would be ignored")
    args = parser.parse_args()

    combine_allure(args.folder.rstrip(sep), args.dest, args.remove_temp_files, args.auto_create_folders, args.ignore_utf8_errors)


if __name__ == '__main__':
    main()
