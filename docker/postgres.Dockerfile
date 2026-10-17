# Rebuild the unchanged upstream helper with a patched Go toolchain. The
# PostgreSQL entrypoint, major version and existing data directory stay intact.
FROM golang:1.27.2-alpine AS gosu
RUN apk add --no-cache git
WORKDIR /src
RUN git init . && git remote add origin https://github.com/tianon/gosu.git \
    && git fetch --depth 1 origin 6456aaa0f3c854d199d0f037f068eb97515b7513 \
    && git checkout --detach FETCH_HEAD
RUN CGO_ENABLED=0 go build -trimpath -o /out/gosu .

FROM postgres:16-alpine
RUN apk upgrade --no-cache
COPY --from=gosu /out/gosu /usr/local/bin/gosu
RUN gosu nobody true
