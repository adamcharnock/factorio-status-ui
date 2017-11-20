Factorio Status UI
==================

Provides a public-facing interface for your factorio server. Information displayed:

* How to connect
* Mods (with 'download all' option)
* Players (online & offline)
* Server configuration
* Mod settings

.. image:: https://github.com/adamcharnock/factorio-status-ui/raw/master/docs/screenshot.png

Getting started
---------------

Factorio Status UI can be run in several ways, so choose the way which best suits you.

Python package
~~~~~~~~~~~~~~

If you have Python 3.6 available to you can use::

    pip install factorio-status-ui
    factorio_status_ui \
        --mods-directory="/path/to/factorio/mods" \
        --saves-directory="/path/to/factorio/saves" \
        --rcon-host=127.0.0.1 \
        --rcon-port=27015 \
        --rcon-password=c14ed7d6e6920dad

Docker image
~~~~~~~~~~~~

Factorio Status UI is available as a docker image::

    docker run \
        -v /path/to/factorio/mods:/mods \
        -v /path/to/factorio/saves:/saves \
        -p 8080:8080 \
        adamcharnock/factorio-status-ui \
        --rcon-host=FACTORIO_SERVER_IP \
        --rcon-port=27015 \
        --mods-directory=/mods \
        --saves-directory=/saves \
        --rcon-password=7b548251be2314ff

Kubernetes Helm Chart (UI only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can install Factorio Status UI to your kubernetes cluster via Helm.
Note that this will require your factorio server to use a form of persistent storage
which can be mounted multiple times (e.g. ``hostDir``, ``nfs`` etc)::

    git clone https://github.com/adamcharnock/factorio-status-ui.git
    cd factorio-status-ui/deploy/charts/factorio-status-ui

    helm install . \
        --set factorio.port=31564 \
        --set factorio.rconHost=FACTORIO_RCON_SERVICE_DNS_NAME \
        --set factorio.rconPassword=RCON_PASSWORD \
        --set persistance.modsPersistantVolumeClaimName=MODS_PVC_NAME \
        --set persistance.savesPersistantVolumeClaimName=SAVES_PVC_NAME \
        --set factorio.serverName="Adam's Factorio Server" \
        --set ingress.enabled=true \
        --set ingress.hosts={a.factorio.theihop.com}

If you want HTTP support (and have kube-lego_ running), then you can add the following::

        --set ingress.tls[0].hosts={a.factorio.theihop.com} \
        --set ingress.tls[0].secretName=factorio-tls \

Kubernetes Helm Chart (Factorio + UI only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

TBA - a chart which will install factorio and the status UI in a single kubernetes POD.
This will provide a simpler deployment option.

Credits
-------

*Any credits here*

factorio-status-ui is packaged using seed_.

.. _seed: https://github.com/adamcharnock/seed/
.. _kube-lego: https://github.com/jetstack/kube-lego
