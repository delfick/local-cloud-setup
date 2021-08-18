#!/bin/bash

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if (($# < 1)); then
    echo "Please say what you want to run"
    exit 1
fi

if [[ ! -L $DIR/root_location ]]; then
    echo "Please create symlink at \`$DIR/root_location\` to where your company code resides"
    exit 1
fi

ROOT_PATH=$(readlink -f $DIR/root_location)

function kubectl_into() {
    # i.e. running `cloud.sh kubectl_into auth` would find the first pod with the app name of "auth" and kubectl exec into it
    kubectl exec -it $(kubectl get pod -l "app=$1" -o jsonpath='{.items[0].metadata.name}') /bin/bash
}

$1 "$@"
