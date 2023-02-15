# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.192.0/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT="3.9"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Choice] Node.js version: none, lts/*, 16, 14, 12, 10
ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# [Option] Install zsh
ARG INSTALL_ZSH="true"
# [Option] Upgrade OS packages to their latest versions
ARG UPGRADE_PACKAGES="false"
# [Option] Enable non-root Docker access in container
ARG ENABLE_NONROOT_DOCKER="true"
# [Option] Use the OSS Moby Engine instead of the licensed Docker Engine
ARG USE_MOBY="true"

# Install needed packages and setup non-root user. Use a separate RUN statement to add your
# own dependencies. A user of "automatic" attempts to reuse an user ID if one already exists.
ARG USERNAME=automatic
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
    && rm -rf /tmp/pip-tmp

# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends <your-package-list-here>


# [Optional] Uncomment this line to install global node packages.
# RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g <your-package-here>" 2>&1

RUN curl https://raw.githubusercontent.com/nektos/act/master/install.sh > /tmp/install-act.sh \
    && chmod a+x /tmp/install-act.sh \
    && /tmp/install-act.sh v0.2.20

COPY library-scripts/*.sh /tmp/library-scripts/


RUN apt-get update \
    && /bin/bash /tmp/library-scripts/common-debian.sh "${INSTALL_ZSH}" "${USERNAME}" "${USER_UID}" "${USER_GID}" "${UPGRADE_PACKAGES}" "true" "true" \
	&& /bin/bash /tmp/library-scripts/desktop-lite-debian.sh \
    # Use Docker script from script library to set things up
    && /bin/bash /tmp/library-scripts/docker-in-docker-debian.sh "${ENABLE_NONROOT_DOCKER}" "${USERNAME}" "${USE_MOBY}" \
    && apt-get -y install --no-install-recommends mariadb-client \
    && wget https://github.com/planetscale/cli/releases/download/v0.77.0/pscale_0.77.0_linux_amd64.deb \
    && dpkg -i pscale_0.77.0_linux_amd64.deb \
    && apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o /tmp/chrome.deb \
    && apt-get -y install /tmp/chrome.deb \
    && ALIASES="alias google-chrome='google-chrome --disable-dev-shm-usage'\nalias google-chrome-stable='google-chrome-stable --disable-dev-shm-usage'\n\alias x-www-browser='x-www-browser --disable-dev-shm-usage'\nalias gnome-www-browser='gnome-www-browser --disable-dev-shm-usage'" \
    && echo "${ALIASES}" >> tee -a /etc/bash.bashrc \
    && if type zsh > /dev/null 2>&1; then echo "${ALIASES}" >> /etc/zsh/zshrc; fi \
    # Clean up
    && rm pscale_0.77.0_linux_amd64.deb \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/* /tmp/library-scripts/