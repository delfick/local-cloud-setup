Local Cloud Setup
=================

Setting up a local cloud involves the following:

* starting the apps with the correct arguments
* reverse proxy hosts/path to particular apps running locally
* tls certs for talking https and talking grpc

This repository makes it easy to do that without requiring docker or k8s locally.

DNS
---

It's useful so that all ``*.local.mycompany.co`` DNS names resolve to 127.0.0.1.

On a MAC, it's good to use dnsmasq for this::

    > brew install dnsmasq

    # Edit /usr/local/etc/dnsmasq.conf
    | port=53
    | address=/local.mycompany.co/127.0.0.1

    # Edit /etc/resolver/local.mycompany.co
    | nameserver 127.0.0.1

    > sudo brew services start dnsmasq

TLS certs
---------

This repo creates tls certs using step-ca

Go here https://smallstep.com/docs/step-ca/getting-started and set it up.

It uses the ACME protocol, which was created by letsencrypt which is what
certmanager uses in a k8s cluster.

Configure it so that it's called ``step-ca.local.mycompany.co`` and is on the
address ``:666``.

Take the password it makes and put it in ``~/.ssh/step-ca-password``

And make ``$HOME/Library/LaunchAgents/step.plist`` with your username replacing ``MY_USERNAME``::

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
      <dict>
        <key>KeepAlive</key>
        <true/>
        <key>Label</key>
        <string>step</string>
        <key>ProgramArguments</key>
        <array>
          <string>/usr/local/bin/step-ca</string>
          <string>/Users/MY_USERNAME/.step/config/ca.json</string>
          <string>--password-file</string>
          <string>/Users/MY_USERNAME/.ssh/step-ca-password</string>
        </array>
        <key>RunAtLoad</key>
        <true/>
        <key>StandardOutPath</key>
        <string>/usr/local/var/log/step.log</string>
        <key>StandardErrorPath</key>
        <string>/usr/local/var/log/step.log</string>
      </dict>
    </plist>

And make it start when you start your computer::

    > launchctl load ~/Library/LaunchAgents/step.plis
    > launchctl start ~/Library/LaunchAgents/step.plis

And also run::

    > step ca provisioner add acme --type ACME

Caddy
-----

To do reverse proxying such that the hostnames go to the correct places. For
example ``https://auth.local.mycompany.co`` should actually talk to
``http://127.0.0.1:3000`` but ``https://auth.local.mycompany.co/some/url/*``
should go to some other service at ``http://127.0.0.1:3003``.

On a MAC you would run::

    > brew install caddy

    # Edit /usr/local/Cellar/caddy/2.2.1/homebrew.mxcl.caddy.plist
    | <key>ProgramArguments</key>
    | <array>
    |   <string>/usr/local/opt/caddy/bin/caddy</string>
    |   <string>run</string>
    |   <string>--resume</string>
    | </array>

    > brew services start caddy

And then to tell caddy our configuration, you run::

    > ./configure_caddy.py

You can edit ``configure_caddy.py`` in the future and run ``./configure_caddy.py``
again and Caddy will instantly get the changes.

GRPC
----

We connect directly to our GRPC endpoints in our configuration and so we need
static certs for those connections. To make that we have a list of apps that
need this certs in the ``apps`` file and running::

    > ./make_grpc_certs.sh

As long as you made ``~/.ssh/step-ca-password`` then you can just paste for
each cert that is made cause the password will be in your clipboard.

Starting everything
-------------------

You must make a symlink in this repo to where your mycompany code is::

    > ln -s ~/Projects/mycompany root_location

and then for example, to start the auth service add a function to cloud.sh:

.. code-block:: bash

    function auth() {
        cd $ROOT_PATH/auth
        go build -race
        ./auth
    }

and run from cloud.sh::

    > ~/cloud.sh auth
