#!/bin/bash

cd $(git rev-parse --show-toplevel)

# Make it so you can just paste the password for each cert
cat ~/.ssh/step-ca-password | pbcopy

for app in $(cat apps); do
    name=$app.local.mycompany.co
    mkdir -p grpc/$name
    if [[ ! -e grpc/$name/$name.crt && ! -e grpc/$name/$name.key ]]; then
        step certificate create grpc/$name grpc/$name/$name.crt grpc/$name/$name.key \
            --ca $HOME/.step/certs/intermediate_ca.crt \
            --ca-key $HOME/.step/secrets/intermediate_ca_key \
            --no-password \
            --insecure \
            --not-after 43800h \
            --san $name \
            --bundle
    fi
done
