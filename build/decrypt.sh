#!/bin/bash

gpg  --batch --passphrase-file mypass --output .ssh/id_rsa  --decrypt id_rsa.gpg

gpg  --batch --passphrase-file mypass --output .ssh/id_rsa.pub  --decrypt id_rsa.pub.gpg