#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import re
import subprocess
import shutil

def get_latest_version():
    url = 'https://help.nordlayer.com/docs/linux'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
                      'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/58.0.3029.110 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Ensure we notice bad responses
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the table of contents or the first header containing the version
    toc = soup.find('nav', {'aria-label': 'Table of contents'})
    if toc:
        # Extract the first link text from the table of contents
        first_link = toc.find('a')
        if first_link:
            text = first_link.get_text(strip=True)
            match = re.search(r'Linux\s+(\d+\.\d+\.\d+)', text)
            if match:
                return match.group(1)
    else:
        # Fallback to find headers in the content
        headers = soup.find_all(['h1', 'h2'])
        for header in headers:
            text = header.get_text(strip=True)
            match = re.search(r'Linux\s+(\d+\.\d+\.\d+)', text)
            if match:
                return match.group(1)
    return None

def update_pkgbuild(pkgbuild, version):
    # Update the PKGBUILD file content
    pkgbuild = re.sub(r'^pkgver=.*$', f'pkgver={version}', pkgbuild, flags=re.MULTILINE)
    pkgbuild = re.sub(r'^pkgrel=.*$', 'pkgrel=1', pkgbuild, flags=re.MULTILINE)
    pkgbuild = re.sub(
        r'^source=\(".*"\)$',
        f'source=("https://downloads.nordlayer.com/linux/latest/debian/pool/main/nordlayer_{version}_amd64.deb")',
        pkgbuild,
        flags=re.MULTILINE
    )
    return pkgbuild


if __name__ == '__main__':
    print("Getting latest version from website.")
    
    if (latest_version := get_latest_version()):

        print(f'Found latest version: {latest_version}')
        print("Updating version and source in PKGBUILD.")

        with open("PKGBUILD", "r+") as pkgbuild_file:
            if (pkgbuild_content := pkgbuild_file.read()):
                pkgbuild_file.seek(0)
                pkgbuild_file.truncate(0)
                pkgbuild_file.write(update_pkgbuild(pkgbuild_content, latest_version))
            else:
                print("PKGBUILD appears to be empty, or reading the file failed.")

        print("Updating checksums in PKGBUILD file, using updpkgsums from pacman-contrib package.")

        if (updpkgsums := shutil.which("updpkgsums")):
            subprocess.run([updpkgsums], check=True)

            print("Regenerating .SRCINFO file.")

            if (makepkg := shutil.which("makepkg")):
                with open(".SRCINFO", "w") as srcinfo_file:
                    subprocess.run(['makepkg', '--printsrcinfo'], stdout=srcinfo_file, check=True)

                print('All updates completed successfully; finished.')
            else:
                print("Cannot find makepkg. Maybe there is an issue with your PATH?")
        else:
            print("Cannot find updpkgsums. Install the pacman-contrib package and try again, or maybe there is an issue with your PATH?")
    else:
        print('Could not find the latest version. Please check the website or update the script.')
