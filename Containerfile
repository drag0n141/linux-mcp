FROM registry.access.redhat.com/ubi10-minimal:10.1-1770180557 as base

FROM base as build

RUN microdnf -y --nodocs --setopt=install_weak_deps=0 install \
        git \
        python3.12 \
        python3.12-pip \
        python-unversioned-command \
    && microdnf clean all

ARG PSEUDO_VERSION=0.1.0a

ENV VENVS=/opt/venvs
ENV UV_PROJECT=/usr/share/container-setup/linux-mcp-server/
ENV UV_PROJECT_ENVIRONMENT="${VENVS}"/mcp
ENV UV_PYTHON=/usr/bin/python
ENV PATH=$VENVS/mcp/bin:"$VENVS/uv/bin:$PATH"
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${PSEUDO_VERSION}

ADD uv.lock pyproject.toml README.md "$UV_PROJECT"
ADD src/ "$UV_PROJECT"/src/

RUN python -m venv /opt/venvs/uv \
    && /opt/venvs/uv/bin/python -m pip install -U pip \
    && /opt/venvs/uv/bin/python -m pip install uv \
    && uv venv --seed "${VENVS}"/mcp \
    && uv sync --no-cache --locked --no-dev --no-editable


FROM base as final

ARG UID=1001
ARG SOURCE_DATE_EPOCH
ARG PSEUDO_VERSION=0.1.0a
ARG VERSION=0.1.0a

ENV container=docker
ENV VENV=/opt/venvs/mcp
ENV PATH="${VENV}/bin:$PATH"
ENV HOME=/var/lib/mcp
ENV LINUX_MCP_SEARCH_FOR_SSH_KEY=True

LABEL description="MCP Server for inspecting Linux"
LABEL io.k8s.description="MCP Server for inspecting Linux"
LABEL io.k8s.display-name="Linux MCP Server"
LABEL name=linux-mcp
LABEL org.opencontainers.image.created=${SOURCE_DATE_EPOCH}
LABEL summary="Linux MCP Server"
LABEL url="https://github.com/drag0n141/linux-mcp"
LABEL version=${VERSION}

RUN microdnf -y --nodocs --setopt=install_weak_deps=0 install \
        git \
        openssh \
        python3.12 \
        python-unversioned-command \
    && microdnf clean all

COPY --from=build /opt/venvs/mcp /opt/venvs/mcp

RUN useradd --key HOME_MODE=0775 --uid "$UID" --gid 0 --create-home --home-dir "$HOME" mcp

USER mcp
WORKDIR $HOME

CMD ["linux-mcp-server"]
